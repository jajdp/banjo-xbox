# Dependencies

*(Español: [DEPENDENCIES.es.md](DEPENDENCIES.es.md))*

## The game project

| | |
|---|---|
| Repository | [HarbourMasters/Lighthouse](https://github.com/HarbourMasters/Lighthouse) |
| Version | **1.1.0**, commit `9c39b49` — what the patches are generated against |
| Submodule `libultraship` | `62e973a`, the one 1.1.0 pins. The second patch applies **inside** it |
| Licenses | Lighthouse CC0-1.0, libultraship MIT |

⚠ **Why the version matters here more than usual.** Lighthouse 1.1.0 pins the libultraship of
August 2026, which reorganised the tree: `src/graphic/Fast3D/` became `src/fast/`, and
`src/Context.cpp` became `src/ship/Context.cpp`. Patches written against an earlier libultraship —
Starship's, for instance — do not apply at all. If you move to a later Lighthouse, expect to
redo the libultraship half of this recipe; `apply_uwp.py` will tell you before it writes anything.

## Your own ROM

Banjo-Kazooie (USA). The project extracts the assets itself into an `.o2r` archive, on your
machine, and that archive is what the game reads at run time. Neither the ROM nor the archive is
distributed here, and the `.gitignore` blocks both by extension.

## Build tools

| | What is needed | Why |
|---|---|---|
| Visual Studio 2022 | With the **C++ UWP workload** | MSBuild packages and signs the UWP target. `package_uwp.ps1` finds Visual Studio with `vswhere`, so the edition and the year are not hard-coded |
| CMake | 3.20 or newer | Both halves: the game DLL and the wrapper. The one bundled with Visual Studio is used if it is there |
| Python 3 | Any 3.8+ | `tools/apply_uwp.py`, standard library only |
| PowerShell | The **5.1** that Windows ships | `package_uwp.ps1` is tested on it with a stock execution policy. PowerShell 7 is not needed |
| UWP dependency bundle | [worleydl/uwp-dep](https://github.com/worleydl/uwp-dep) | SDL2, libuwp, Mesa and glfw3 built for UWP. **CMake fetches it**; it has no license, so nothing of it is redistributed here |

## The console

Xbox Series X or S in **Developer Mode**, with a user signed in, and the
`Microsoft.VCLibs.140.00` x64 appx installed alongside the package as a dependency.
