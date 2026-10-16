#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply this repository's UWP patches to your own checkout of Lighthouse (Banjo-Kazooie).

There are two patches and they go to two different roots, which is the one thing people get
wrong: `01-game.patch` applies to the game checkout, `02-libultraship.patch` applies to its
`libultraship/` submodule. This script knows which goes where, checks before it writes, and
refuses to do half the job.

    python tools/apply_uwp.py <path-to-game-checkout>
    python tools/apply_uwp.py <path-to-game-checkout> --check     # dry run, writes nothing
    python tools/apply_uwp.py <path-to-game-checkout> --revert    # undo
    python tools/apply_uwp.py --list                              # what each patch changes

Everything the patches add is guarded by `#ifdef _UWP`, so a patched checkout still builds and
runs for the desktop exactly as it did before. That is deliberate, and it is not how the port this
recipe is based on did it (Starship's patches use `#if 0`): keeping both targets alive in one tree
is what lets the recipe be re-applied to a later Lighthouse.

It is idempotent: run it twice and the second run reports "already applied" and changes nothing.
That is tested by asking git itself (`git apply --reverse --check`), not by looking for a marker
of ours, so it stays true even if upstream edits those files around our hunks.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
PATCHES = HERE.parent / 'patches'

# (patch file, subdirectory of the checkout it applies to, what it is for)
STEPS = (
    ('01-game.patch', '.',
     'The game: CMakeLists.txt and six files under src/port/.\n'
     '      - CMakeLists.txt gets a BUILD_UWP option that forces NON_PORTABLE, pulls in the UWP\n'
     '        dependency bundle, takes sdl2/glfw3 out of vcpkg and builds the game as a DLL.\n'
     '      - Game.cpp exports SDL_main from that DLL (SDLMAIN_DECLSPEC = dllexport), which is\n'
     '        how the WinRT wrapper finds it.\n'
     '      - Engine.cpp, ExtractFlow.cpp, Rando.cpp, RefreshOptions.cpp and SaveManager.cpp:\n'
     '        three global paths become lazily initialised -- as globals they ran before the\n'
     '        AppContainer was ready and killed the DLL before it loaded -- the ES_WINDOWS step\n'
     '        is skipped because it reads getenv(), which returns NULL in UWP, and the save and\n'
     '        extraction paths move to the folder a packaged app may write to.'),
    ('02-libultraship.patch', 'libultraship',
     'The engine: six files.\n'
     '      - gfx_dxgi.cpp: a CoreWindow instead of CreateWindowW, and\n'
     '        CreateSwapChainForCoreWindow with an explicit size. Without the size the swap\n'
     '        chain comes out 0x0 and nothing is ever presented.\n'
     '      - Fast3dWindow.cpp, gfx_sdl2.cpp: the window backend, the event pump and the\n'
     '        refresh rate read through libuwp. In UWP the SDL+OpenGL backend is the one that\n'
     '        works, because it is the only one the controller comes through.\n'
     '      - Context.cpp, Gui.cpp: the log path, and the screen size for ImGui taken from\n'
     '        uwp_GetScreenSize instead of from the window -- otherwise ImGui draws on a 0x0\n'
     '        canvas and the menu is invisible.\n'
     '      - cmake/dependencies/windows.cmake: the UWP dependency bundle.'),
)


def run(cmd, cwd):
    return subprocess.run([str(c) for c in cmd], cwd=str(cwd), capture_output=True,
                          text=True, errors='replace')


def git_ok(root):
    p = run(['git', 'rev-parse', '--is-inside-work-tree'], root)
    return p.returncode == 0 and p.stdout.strip() == 'true'


def state(root, patch):
    """'applied', 'pending', or a string explaining why neither is possible."""
    forward = run(['git', 'apply', '--check', str(patch)], root)
    if forward.returncode == 0:
        return 'pending'
    reverse = run(['git', 'apply', '--reverse', '--check', str(patch)], root)
    if reverse.returncode == 0:
        return 'applied'
    return 'stuck: ' + (forward.stderr.strip().splitlines() or ['git apply refused it'])[-1]


def sane(patch):
    """A patch file that is not a patch any more.

    Worth checking, because when it happens `git apply` fails and the natural reading of the
    failure is that your checkout is wrong. It is not. A `.patch` written through a shell
    pipeline can arrive with its newlines stripped (every hunk on one line) or with CRLF where
    the tree has LF, and neither is something you could see by eyeing the file.
    """
    raw = patch.read_bytes()
    if not raw:
        return 'it is empty'
    if b'@@ -' not in raw:
        return 'it has no hunk header (@@), so it is not a unified diff'
    if b'\n' not in raw:
        return ('it has no line breaks at all -- %d bytes on a single line. Something rewrote it '
                'after git produced it' % len(raw))
    if not raw.endswith(b'\n'):
        return 'it does not end in a newline, and git apply needs that'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('checkout', nargs='?', type=Path,
                    help='root of your Lighthouse checkout')
    ap.add_argument('--check', action='store_true', help='report only, write nothing')
    ap.add_argument('--revert', action='store_true', help='remove the patches')
    ap.add_argument('--list', action='store_true', help='print what each patch changes')
    a = ap.parse_args()

    if a.list:
        for name, where, what in STEPS:
            print('%s  ->  %s' % (name, '<checkout>' if where == '.' else '<checkout>/' + where))
            print('      ' + what + '\n')
        return 0

    if a.checkout is None:
        ap.error('pass the path to your Lighthouse checkout '
                 '(there is no default: this script never guesses a path)')

    root = a.checkout.expanduser().resolve()
    if not root.is_dir():
        sys.exit('not a directory: %s' % root)
    if not (root / 'src').is_dir() or not (root / 'libultraship').is_dir():
        sys.exit('that does not look like a Lighthouse checkout: expected src/ and\n'
                 'libultraship/ inside %s\n'
                 'Clone it and initialise the libultraship submodule; see docs/INSTALL.md section 1.' % root)

    targets = []
    for name, where, _what in STEPS:
        patch = PATCHES / name
        if not patch.is_file():
            sys.exit('missing patch: %s' % patch)
        mal = sane(patch)
        if mal:
            sys.exit('%s is damaged: %s.\nRe-download the repository; this is not a problem '
                     'with your checkout.' % (patch.name, mal))
        target = root if where == '.' else root / where
        if not git_ok(target):
            sys.exit('%s is not a git work tree, so the patches cannot be checked before\n'
                     'they are written. The submodule has to be initialised: see\n'
                     'docs/INSTALL.md section 1.' % target)
        targets.append((name, patch, target))

    # Look at everything first. Half-patched is the one outcome worth protecting against.
    states = [(name, patch, target, state(target, patch)) for name, patch, target in targets]
    for name, _patch, target, st in states:
        print('%-30s %-14s %s' % (name, st.split(':')[0], target))
    if any(st.startswith('stuck') for *_x, st in states):
        for name, _p, _t, st in states:
            if st.startswith('stuck'):
                print('\n%s: %s' % (name, st), file=sys.stderr)
        sys.exit('\nNothing was written. Either the checkout is not the version this recipe was\n'
                 'written against (see docs/DEPENDENCIES.md) or it has local changes in the\n'
                 'files these patches touch.')

    want = 'applied' if a.revert else 'pending'
    todo = [(name, patch, target) for name, patch, target, st in states if st == want]
    if not todo:
        print('\nNothing to do: everything is already %s.'
              % ('removed' if a.revert else 'applied'))
        return 0
    if a.check:
        print('\n--check: %d patch(es) would be %s. Nothing was written.'
              % (len(todo), 'reverted' if a.revert else 'applied'))
        return 0

    for name, patch, target in todo:
        cmd = ['git', 'apply']
        if a.revert:
            cmd.append('--reverse')
        cmd.append(str(patch))
        p = run(cmd, target)
        if p.returncode:
            print(p.stdout, p.stderr, file=sys.stderr)
            sys.exit('%s failed on %s. The patches that ran before this one are still '
                     'applied; re-run with --revert to undo them.' % (name, target))
        print('%s %s' % ('reverted' if a.revert else 'applied ', name))

    if not a.revert:
        print('\nDone. Next: build it (docs/INSTALL.md section 3). The desktop build of your\n'
              'checkout is unchanged: everything added is behind #ifdef _UWP.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
