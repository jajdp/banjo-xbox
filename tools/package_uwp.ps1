<#
.SYNOPSIS
  Builds and signs the UWP package of Banjo-Kazooie (Lighthouse) for an Xbox Series.

.DESCRIPTION
  This is the second half of the recipe. The first half is building the game itself as a DLL
  with -DBUILD_UWP=ON (docs/INSTALL.md section 3); this script takes that DLL, configures the
  WinRT wrapper from uwp/, and lets MSBuild package and sign it.

  Everything is a parameter: there is no path here pointing at anyone's machine, and Visual
  Studio is located with vswhere rather than by a hard-coded year and edition.

.PARAMETER Tree
  Your Lighthouse checkout -- the one you patched with tools/apply_uwp.py. Required.

.PARAMETER Thumbprint
  SHA-1 thumbprint of your signing certificate (docs/INSTALL.md section 4). Required.

.PARAMETER Version
  Package version, four numbers. It has to go up on every cycle: the console will not replace
  an installed package with another one carrying the SAME version, and it fails in a way that
  looks like the new build did not work.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\package_uwp.ps1 `
      -Tree C:\lighthouse -Thumbprint 1A2B3C... -Version 0.1.0.0
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Tree,
  [Parameter(Mandatory = $true)][string]$Thumbprint,
  [string]$Version = "0.1.0.0"
)

$ErrorActionPreference = 'Stop'

if ($Version -notmatch '^\d+\.\d+\.\d+\.\d+$') { throw "-Version takes four numbers, like 0.1.0.0" }
if (-not (Test-Path -LiteralPath $Tree)) { throw "that tree does not exist: $Tree" }

# --- Visual Studio, by asking instead of guessing -------------------------------------------
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere)) {
  throw "vswhere.exe not found. Visual Studio 2022 (any edition) has to be installed."
}
$vs = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -property installationPath
if (-not $vs) { throw "no Visual Studio installation with MSBuild was found" }
$msbuild = Join-Path $vs 'MSBuild\Current\Bin\MSBuild.exe'
$cmake = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
if (-not (Test-Path -LiteralPath $cmake)) { $cmake = 'cmake' }   # the one on PATH, if any
Write-Host "  Visual Studio: $vs"

# --- the certificate, before doing any work -------------------------------------------------
# Through .NET and not the Cert: drive: that drive comes from a PowerShell module, and on a
# machine whose PSModulePath has been rewritten (a PowerShell 7 install will do it) Windows
# PowerShell 5.1 says the drive does not exist while the certificate is sitting in the store.
$store = New-Object System.Security.Cryptography.X509Certificates.X509Store 'My', 'CurrentUser'
$store.Open('ReadOnly')
$cert = $store.Certificates | Where-Object { $_.Thumbprint -eq $Thumbprint } | Select-Object -First 1
if (-not $cert) { throw "no certificate with thumbprint $Thumbprint in the current user's My store" }
if (-not $cert.HasPrivateKey) { throw "that certificate has no private key, so it cannot sign" }
Write-Host "  certificate: $($cert.Subject)"

$dll = Join-Path $Tree 'build-windows\Release\Lighthouse.dll'
if (-not (Test-Path -LiteralPath $dll)) {
  throw "the game DLL is missing: $dll`nBuild the game first with -DBUILD_UWP=ON (docs/INSTALL.md section 3)."
}
Write-Host ("  game DLL: {0:N1} MB" -f ((Get-Item -LiteralPath $dll).Length / 1MB))

# The version goes into the manifest before configuring, because that is where MSBuild reads it.
$manifest = Join-Path $Tree 'uwp\Package.appxmanifest'
if (-not (Test-Path -LiteralPath $manifest)) {
  throw "the wrapper manifest is missing: $manifest`nDid tools/apply_uwp.py run, and did you copy package/Package.appxmanifest into <tree>\uwp\?"
}
$text = Get-Content -LiteralPath $manifest -Raw
if ($text -match 'CHANGE-ME') {
  throw "the manifest still says CHANGE-ME. Put your own Name and Publisher in it first; the comment above <Identity> explains what each one does."
}
$publisher = [regex]::Match($text, '<Identity\b[^>]*?Publisher="([^"]*)"', 'Singleline').Groups[1].Value
if ($publisher.Trim() -ne $cert.Subject.Trim()) {
  throw "the manifest Publisher and the certificate subject are not the same string:`n  manifest:    $publisher`n  certificate: $($cert.Subject)`nThe console compares them literally and rejects the package if they differ."
}
$text = [regex]::Replace($text, 'Version="\d+\.\d+\.\d+\.\d+"', "Version=`"$Version`"")
Set-Content -LiteralPath $manifest -Value $text -Encoding UTF8
Write-Host "  manifest at $Version"

Write-Host "=== 1. configure the WinRT wrapper ==="
& $cmake -S (Join-Path $Tree 'uwp') -B (Join-Path $Tree 'build-uwp') `
  -G "Visual Studio 17 2022" -A x64 `
  -DLIGHTHOUSE_DIR="$Tree/build-windows"
if ($LASTEXITCODE -ne 0) { throw "the wrapper configure step failed" }

Write-Host "=== 2. package and sign ==="
$out = Join-Path $Tree "paquete-$Version"
& $msbuild (Join-Path $Tree 'build-uwp\lighthouse-uwp.vcxproj') `
  /p:Configuration=Release /p:Platform=x64 `
  /p:AppxPackageSigningEnabled=true `
  /p:PackageCertificateThumbprint=$Thumbprint `
  /p:UapAppxPackageBuildMode=SideloadOnly `
  /p:AppxBundle=Always /p:AppxBundlePlatforms=x64 `
  /p:AppxPackageDir="$out\\" `
  /verbosity:minimal
if ($LASTEXITCODE -ne 0) { throw "packaging failed" }

Write-Host "=== 3. what came out ==="
Get-ChildItem -LiteralPath $out -Recurse -Include *.msixbundle, *.appxbundle, *.msix, *.appx, *.cer |
  ForEach-Object { "  {0,8:N1} MB  {1}" -f ($_.Length / 1MB), $_.FullName }
Write-Host "Install it through the Device Portal: docs/INSTALL.md section 5."
