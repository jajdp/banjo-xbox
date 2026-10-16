# Install — from a clean checkout to the game running on the console

*(Español: [INSTALL.es.md](INSTALL.es.md))*

## 0. Where you type these commands

- **PowerShell** — press **Windows**, type `powershell`, **Enter** — for the Python script, the
  certificate, the packaging script and the Device Portal.
- **A `cmd` or PowerShell window** for CMake, which builds the game as a DLL.

**You do not need "run as administrator"**, and using it would break section 4: the certificate is
created in the store of whoever runs the command. The `-ExecutionPolicy Bypass` in the examples is
because a stock Windows will not run a `.ps1` at all; it applies to that one process.

## 1. Clone the game project

```powershell
git clone --branch 1.1.0 https://github.com/HarbourMasters/Lighthouse.git C:\bk
cd C:\bk
git submodule update --init --depth 1 libultraship
```

Get the game running **for the desktop first**, with your own ROM: Lighthouse extracts the assets
into an `.o2r` archive and that step has nothing to do with this recipe. If the desktop build does
not work, the UWP one will not either.

## 2. Apply the recipe

```powershell
python <this repo>\tools\apply_uwp.py C:\bk
```

Two patches: one to the game, one **inside** the `libultraship` submodule. The script checks both
before writing anything and refuses to apply one without the other. `--check` reports without
writing, `--revert` undoes it, `--list` explains every change and why.

Then copy the wrapper into the checkout:

```powershell
mkdir C:\bk\uwp
copy <this repo>\src\main.cpp         C:\bk\uwp\
copy <this repo>\src\CMakeLists.txt   C:\bk\uwp\
copy <this repo>\package\Package.appxmanifest C:\bk\uwp\
mkdir C:\bk\uwp\Assets
rem ... and your own thirteen tiles into C:\bk\uwp\Assets (docs/ASSETS.md)
```

## 3. Build the game as a DLL

```powershell
cmake -S C:\bk -B C:\bk\build-windows -DBUILD_UWP=ON
cmake --build C:\bk\build-windows --config Release
```

`BUILD_UWP=ON` is what the patch adds: it forces `NON_PORTABLE` (so the game writes to the app
data folder instead of next to the executable), fetches the UWP dependency bundle, takes sdl2 and
glfw3 out of vcpkg, and builds **a DLL** instead of an executable. The result is
`build-windows\Release\Lighthouse.dll`.

## 4. A certificate to sign with

```powershell
New-SelfSignedCertificate -Type Custom -Subject "CN=<your name>" -KeyUsage DigitalSignature `
  -FriendlyName "<your name> UWP dev" -CertStoreLocation "Cert:\CurrentUser\My" `
  -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
```

Write down the `Thumbprint`, and put your own `Name` and `Publisher` in
`C:\bk\uwp\Package.appxmanifest` (the copy you just made). `Publisher` must be **exactly** the
`-Subject` above: `package_uwp.ps1` compares them before doing any work, because the console
compares them literally and rejects the package if they differ.

## 5. Package, sign and install

```powershell
powershell -ExecutionPolicy Bypass -File <this repo>\tools\package_uwp.ps1 `
    -Tree C:\bk -Thumbprint <your thumbprint> -Version 0.1.0.0
```

It configures the wrapper with CMake and lets MSBuild package and sign. Visual Studio is located
with `vswhere`, so no path or year is hard-coded.

⚠ **The version has to go up on every cycle.** The console will not replace an installed package
with another one carrying the same version, and the failure looks like your new build is broken.

Install the `.msixbundle` from the console's **Device Portal** (`https://<console ip>:11443`, user
`xbox`), with the `Microsoft.VCLibs.140.00` x64 appx as a dependency. The console needs **a user
signed in**.

Then upload the `.o2r` archive the desktop build produced to the app's `LocalState`.

⚠ Two things that cost an afternoon each: the app's data folder **does not exist until the app has
run once**, and files uploaded **inside a `.zip`** come out with permissions the AppContainer
cannot read. Launch it once, close it, then upload one file at a time.

## 6. When something goes wrong

| What you see | What it is |
|---|---|
| `unresolved external symbol SDL_main` | The game patch did not apply (section 2) |
| The package installs and closes instantly | A global initialiser calling WinRT from `DllMain` — i.e. the game patch is not in |
| A black screen, process alive | ImGui drawing on a 0×0 canvas: the libultraship patch is not in |
| It dies after 3-6 seconds with no dump | The `ES_WINDOWS` step: `getenv` returns NULL in UWP (section 2 of the patch list) |
| No controller | The window backend must be SDL+OpenGL, not DXGI, and `SDL_INIT_GAMECONTROLLER` must come after the window |
| The console rejects the package | `Publisher` and the certificate subject are not the same string (section 4) |
| Installing "works" but the game is the old one | The package version did not go up (section 5) |
| The game cannot find its assets | The `.o2r` is not in `LocalState`, or it was uploaded inside a zip (section 5) |
