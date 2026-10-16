# How it works

*(Español: [HOW-IT-WORKS.es.md](HOW-IT-WORKS.es.md))*

## The shape of the port

A libultraship game on an Xbox cannot be an ordinary executable: a UWP process starts at
`CoreApplication`, not at `main()`. The architecture — taken from Starship's UWP branch — turns
that around:

1. the **game** is built as a DLL (`-DBUILD_UWP=ON`) that exports `SDL_main`;
2. a **WinRT wrapper** of about two hundred lines loads that DLL and hands it the thread with
   `SDL_WinRTRunApp`;
3. the UWP libraries (SDL2, libuwp, Mesa, glfw3) come from a dependency bundle CMake fetches.

Everything this recipe changes in the game and in libultraship sits behind `#ifdef _UWP`, so the
same checkout still builds for the desktop. Starship's patches use `#if 0` instead; keeping both
targets alive is what makes this recipe re-appliable when Lighthouse moves on.

## The failure that teaches the most

For hours the process lived **three to six seconds** and vanished — at whatever point of startup it
had reached, **with no exception in any thread and no crash dump**. That last part is the clue: no
dump means there was no crash. The system killed it, which is what WinRT does to an app that does
not present its window at startup.

There is no stderr on a console, so the diagnosis came from instrumenting startup with breadcrumbs
and timestamps into a file in the app's data folder. That narrowed it to one line:

```
[   266 ms] RunExtract: version o2r 1.1.0  shouldRegen=0
[   266 ms] bucle vuelta 0  paso=0
[   266 ms] bucle vuelta 1  paso=1      <-- it never got past this
```

Step 1 is `ES_WINDOWS`, and it asks two desktop questions: am I running from `%TEMP%`, and can I
write next to the executable. Both go through `getenv`, and **in UWP `getenv` always returns
NULL** — the process starts with no environment block. With `TEMP` null the path does not
canonicalise, and the handler builds a `std::string` from a null `USERPROFILE`.

Neither question means anything inside a package: the answers are known in advance, and writing is
`NON_PORTABLE`'s job, which puts everything in the app data folder. So the step is skipped
entirely, and with that the app went from dying at three seconds to running indefinitely at 60
frames per second.

**The lesson worth keeping:** when a UWP app disappears without a dump, do not look for a crash.
Look for what the system expects and is not getting.

## Three more that each looked like something else

- **`unresolved external symbol SDL_main`.** Lighthouse names its entry point that way but does not
  export it. SDL's own `SDLMAIN_DECLSPEC` macro, defined as `__declspec(dllexport)` before the
  includes, is the whole fix.
- **Installed and closed instantly.** Three **global** path objects ran their initialisers inside
  `DllMain`, and `SDL_GetPrefPath` asks WinRT for `ApplicationData::Current`. Calling WinRT from
  `DllMain` is not allowed; on the desktop the same function resolves through Win32 and nobody
  notices. The fix changes *when*, not *what*: function statics, computed on first use. It is
  better code on both platforms, since it also drops a static initialisation order dependency.
- **A swap chain with no size.** `CreateSwapChainForHwnd` infers the size from the window, so the
  code passes `Width = 0`. `CreateSwapChainForCoreWindow` does not accept 0 — there is no window to
  infer it from. A contract difference between two functions that look interchangeable.

## The controller: three layers, each hiding the next

1. the window backend has to be **SDL+OpenGL**, not DXGI: on this console it is the only one the
   pad comes through at all;
2. gamepad navigation has to be **forced on** in UWP;
3. `SDL_INIT_GAMECONTROLLER` has to be initialised **after** the window is created, not before.

Fix one and the pad is still dead, which is what makes this kind of bug expensive.

## How this was verified

On a **fresh clone of Lighthouse 1.1.0 (`9c39b49`)** with its `libultraship` submodule, on
2026-10-14: both patches apply clean, the recipe reproduces the tree the shipped package was built
from — **13 of 13 files identical byte for byte** once line endings are normalised — and a second
run writes nothing.

⚠ The working tree was cloned with `core.autocrlf=true` and the verification clone without it, so
one has CRLF on disk and the other LF: compared raw, all 13 files "differ" and none of it is
content. Normalise before concluding anything when you compare two checkouts.

What is **not** re-measured here is MSBuild's output: that needs the dependency bundle and a full
build of the game. The package that runs on the consoles was built from this exact tree.

## A note on language

`tools/package_uwp.ps1` is in English. The patches carry a few comments in Spanish, which is where
they were written, and they are published as they were compiled and verified rather than retyped.
