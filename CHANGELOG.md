# Changelog

All notable changes to this recipe. Dates are `YYYY-MM-DD`.

The version here is the **recipe's**, not the game's and not the package's.

## 1.0.1 — 2026-10-16

### Fixed

- **`LICENSE`: the explanatory block named the wrong project.** Everything after the MIT text had
  been copied from the `dkr-xbox` repository and never adapted: it said this was a derivative of
  Golden Balloon, denied granting rights in Diddy Kong Racing, quoted "the 57 lines of the upstream
  project", and listed folders this repository does not have. The MIT grant itself was correct all
  along, and `NOTICE.md` always had the right figures. The block now names HarbourMasters/Lighthouse (CC0-1.0) and libultraship (MIT) and
  Banjo-Kazooie, and points at `NOTICE.md` for the measurements instead of repeating a number.

## 1.0.0 — 2026-10-14

First release.

### Included

- `patches/01-game.patch` (183 added lines over 7 files) and `patches/02-libultraship.patch`
  (121 over 6), all behind `#ifdef _UWP`, so a patched checkout still builds for the desktop.
- `src/`: the WinRT wrapper — `main.cpp` and its `CMakeLists.txt`.
- `tools/apply_uwp.py`: applies, reverts, lists and checks both patches; idempotent, and it
  refuses to leave a checkout half-patched.
- `tools/package_uwp.ps1`: configures the wrapper and lets MSBuild package and sign, after
  checking the certificate, the manifest and the game DLL. Visual Studio is located with
  `vswhere`, not by a hard-coded year.
- `package/Package.appxmanifest` with `CHANGE-ME` identity, and documentation in English and
  Spanish.

### Verified before release

On a fresh clone of Lighthouse 1.1.0 (`9c39b49`): both patches apply clean, the recipe reproduces
the tree the shipped package was built from — **13 of 13 files identical byte for byte** once line
endings are normalised — and it is idempotent. `package_uwp.ps1` parses and validates under the
PowerShell 5.1 that Windows ships. Detail in [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md).
