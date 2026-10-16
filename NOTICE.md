# Notice

*(Español: [NOTICE.es.md](NOTICE.es.md))*

## Not affiliated

This is an unofficial, noncommercial fan project. It is **not affiliated with, endorsed by or
connected to** the rights holders of *Banjo-Kazooie*, with Microsoft, or with the authors of
[HarbourMasters/Lighthouse](https://github.com/HarbourMasters/Lighthouse) or of any of the projects it builds on. *Banjo-Kazooie*, *Xbox* and all
related names and marks are the property of their respective owners.

Nothing here is for sale, and nothing here is monetized.

## What this repository does not distribute

No ROM. No game code belonging to the rights holders. No extracted assets. No built executable or
library. No package. No save data. No package tiles, which were made from the game's own artwork.
No signing certificate, and no thumbprint of one.

The `.gitignore` blocks all of it by extension. That is a safeguard, not a substitute for reading
this file.

## What it does contain of other people's work

Measured, so that "we distribute nothing of theirs" is something you can check rather than
something you have to believe:

| | Lines | What it is | License |
|---|---|---|---|
| Our own patch lines | 304 | What the two patches add, all behind `#ifdef _UWP` | ours, MIT |
| Quoted from Lighthouse | 131 | The **context lines** a unified diff carries, plus 11 lines removed | CC0-1.0 |
| Quoted from libultraship | 146 | Same: context, plus 3 lines removed | MIT |
| `src/main.cpp`, `src/CMakeLists.txt` | 196 | The WinRT wrapper that loads the game DLL and hands it the thread | ours, MIT |
| `tools/` | 338 | `apply_uwp.py` and `package_uwp.ps1` | ours, MIT |

The ROM is yours to supply and never travels through here, and neither does the `.o2r`
archive the project builds from it. The UWP dependency bundle is fetched by CMake on your
machine: it has no license, so nothing of it is redistributed here.

## Takedown

If you hold rights to any of the above and want something removed, write to
**jajdpmail@gmail.com** and it will be taken down. No argument, no delay.
