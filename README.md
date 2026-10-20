# Banjo-Kazooie on Xbox — the UWP port

How to take the [Lighthouse](https://github.com/HarbourMasters/Lighthouse) decompilation of
*Banjo-Kazooie* (Nintendo 64, 1998) and run it **on an Xbox Series X in Developer Mode**, as a
UWP package you build and sign yourself.

It is not a theory: the game plays on two consoles, and nobody else had ported it — a census
of the **19 forks** of Lighthouse on 2026-09-16 found iOS, macOS, Wii U and a mobile-XR port,
and no UWP branch at all.

*(Español: [README.es.md](README.es.md))*

## Which console this was tested on

**An Xbox Series X**, in Developer Mode. Both of the consoles this was built and tested on are Series X,
so that is the only hardware anything claimed here covers.

**A Series S has never been tried — not once.** It is a different machine: less memory available to a
game and a weaker GPU. This may work on one, it may run slower, or it may not start at all; nothing here
has been measured on it. If you run it on a Series S, what you get is not what this README reports, and
none of the numbers here are a promise about that console.

## What this repository is

**A recipe and the tools that apply it.** The architecture is the one
[JRickey/Starship](https://github.com/JRickey/Starship) uses on its `uwp-2026-rebase`
branch, which is the only published UWP port of a libultraship game: the game is built as a
**DLL** exporting `SDL_main`, a **minimal WinRT wrapper** loads it and hands it the thread
with `SDL_WinRTRunApp`, and the UWP libraries come from a dependency bundle CMake fetches by
itself.

⚠ **Starship's own patches do not apply to this game**, and that is the work this
repository is: they are written against the libultraship of October 2025, while Lighthouse
1.1.0 pins the one of August 2026, which also moved the tree around
(`src/graphic/Fast3D/` → `src/fast/`, `src/Context.cpp` → `src/ship/Context.cpp`). Every
change was reimplemented in the new places and put behind `#ifdef _UWP` rather than
Starship's `#if 0`, so one tree keeps building for the desktop too.

## What this repository is **not**

It contains **no ROM, no game code, no built executable, no package and no artwork**. It cannot
produce a playable game on its own, and nothing you can download here is a game. You need your own
legally dumped copy of the game. See [`NOTICE.md`](NOTICE.md).

The package tiles are not here either: the ones on the real console were made from the
game's own art. [`docs/ASSETS.md`](docs/ASSETS.md) lists what is needed.

Neither is the **UWP dependency bundle** ([worleydl/uwp-dep](https://github.com/worleydl/uwp-dep)):
those are other people's binaries and it has no license, so CMake fetches it on your machine
and nothing of it travels through here.

## What you need first

| | |
|---|---|
| The game project | [HarbourMasters/Lighthouse](https://github.com/HarbourMasters/Lighthouse) **1.1.0** (commit `9c39b49`) with its `libultraship` submodule (`62e973a`), **building and running on your PC first** |
| Your own ROM | Banjo-Kazooie (USA). The project extracts its assets into an `.o2r` archive on your machine; neither the ROM nor the archive is distributed here |
| Visual Studio | 2022 with the **C++ UWP workload**: here MSBuild packages and signs |
| CMake | 3.20 or newer (the one that ships with Visual Studio is fine) |
| Python 3 | For `tools/apply_uwp.py`. Standard library only |
| An Xbox in Developer Mode | And a certificate to sign with ([`docs/INSTALL.md`](docs/INSTALL.md) section 4) |

## How it goes

```powershell
# 1. patch your checkout: the game, and its libultraship submodule
python tools\apply_uwp.py <path-to-your-lighthouse-checkout>

# 2. build the game as a DLL (docs/INSTALL.md section 3)
#    cmake -S . -B build-windows -DBUILD_UWP=ON  &&  cmake --build build-windows --config Release

# 3. copy the wrapper into the checkout and package it
#    (src\main.cpp + src\CMakeLists.txt -> <checkout>\uwp\, package\Package.appxmanifest too)
powershell -ExecutionPolicy Bypass -File tools\package_uwp.ps1 `
    -Tree <path-to-your-checkout> -Thumbprint <your certificate> -Version 0.1.0.0
```

`python tools\apply_uwp.py --list` prints both patches and what each change solves.

Step by step, including the console side: **[`docs/INSTALL.md`](docs/INSTALL.md)**
([en español](docs/INSTALL.es.md)).

## What it had to solve

Every one of these was a real failure on the console. The detail is in
**[`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md)**.

| | Symptom | Fix |
|---|---|---|
| 1 | `unresolved external symbol SDL_main` | Lighthouse names its entry point that way but does not export it. It is marked with SDL's own `SDLMAIN_DECLSPEC`, defined as `__declspec(dllexport)` before the includes |
| 2 | The package installed and closed instantly, no crash dump | Three **global** path objects ran their initialisers inside `DllMain`, and `SDL_GetPrefPath` asks WinRT for `ApplicationData::Current`. **Calling WinRT from DllMain is not allowed.** The fix changes *when*, not *what*: function statics, computed on first use |
| 3 | A black screen with a living process | `CreateSwapChainForCoreWindow` does not accept a size of 0, while `CreateSwapChainForHwnd` infers it from the window. Explicit width and height |
| 4 | **The process died after 3-6 seconds, with no exception and no dump** | No dump means no crash: the system killed it, which is what WinRT does to an app that does not present its window at startup. The cause was one startup step — see below |
| 5 | That step: `ES_WINDOWS` | It asks two desktop questions (am I running from `%TEMP%`, can I write next to the executable) through `getenv`, and **in UWP `getenv` always returns NULL** — a `std::string` built from a NULL `USERPROFILE`. Neither question means anything in a package, so the step is skipped entirely. With that, the app went from dying at 3 seconds to running indefinitely at 60 fps |
| 6 | Then: a black screen again, drawing but invisible | `ImGui_ImplWin32_NewFrame` takes the screen size from `GetClientRect(hWnd)`, and in this port the `hWnd` is a disguised CoreWindow: the call fails, the rectangle is zero, and everything draws on a 0×0 canvas. The size comes from `uwp_GetScreenSize` instead |
| 7 | No controller | Three layers, each hiding the next: the window backend has to be SDL+OpenGL (not DXGI) because it is the only one the pad comes through; gamepad navigation has to be forced on; and `SDL_INIT_GAMECONTROLLER` has to happen **after** the window is created |

## How it was verified

Not by reading it: by rebuilding the tree. On a **fresh clone of Lighthouse 1.1.0 (`9c39b49`)**
with its `libultraship` submodule, on 2026-10-14:

| What was measured | Result |
|---|---|
| Both patches apply to a clean checkout | Yes, clean, with `git apply --check` first and nothing written on failure |
| The tree the recipe produces, against the tree the shipped package was built from | **13 of 13 files identical**, byte for byte, once line endings are normalised |
| Idempotence | A second run reports `already applied` and writes nothing |
| `tools/package_uwp.ps1` | Parses and validates under the **PowerShell 5.1 that Windows ships**, with a stock execution policy, and refuses a missing tree, a missing DLL, a `CHANGE-ME` manifest, a certificate without a private key, and a Publisher that does not match the certificate |

⚠ **About those line endings:** the working tree was cloned with `core.autocrlf=true` (Git for
Windows' default) and the verification clone without it, so one has CRLF on disk and the other LF.
Normalising, the 13 files are identical; compared raw, all 13 "differ" and none of it is content.
Worth knowing before you compare two checkouts and think the recipe is wrong.

What is **not** re-measured here is MSBuild's own output: rebuilding the package needs the UWP
dependency bundle and a full build of the game, and the package that runs on the consoles was built
from this exact tree. The verified claim is the recipe.

## Credits and license

Port and tooling by **Recompilaciones**, under the [MIT License](LICENSE). The game project is CC0-1.0 and the engine this port patches, libultraship, is MIT; MIT is
the one that covers both and asks for attribution, which is the honest reading.

The architecture comes from [JRickey/Starship](https://github.com/JRickey/Starship) (CC0-1.0),
whose `uwp-2026-rebase` branch is the only published UWP port of a libultraship game. Its
patches are not reused here — they do not apply to this engine version — but the shape of the
solution is theirs and deserves saying so.

*Banjo-Kazooie* is © its rights holders. This project is not affiliated with them, with Microsoft, or
with the authors of the projects it builds on, and it distributes nothing that belongs to them. The
details are in [`NOTICE.md`](NOTICE.md). Rights holders can write to **jajdpmail@gmail.com**.
