# Instalación — de una copia limpia al juego corriendo en la consola

*(English: [INSTALL.md](INSTALL.md))*

## 0. Dónde se escriben estas órdenes

- **PowerShell** —pulsa **Windows**, escribe `powershell`, **Entrar**— para el script de Python, el
  certificado, el script de empaquetado y el Device Portal.
- **Una ventana de `cmd` o PowerShell** para CMake, que compila el juego como DLL.

**No hace falta «ejecutar como administrador»**, y usarlo rompería el apartado 4: el certificado se
crea en el almacén de quien ejecuta la orden. El `-ExecutionPolicy Bypass` de los ejemplos es
porque un Windows de fábrica no ejecuta un `.ps1`; vale solo para ese proceso.

## 1. Clonar el proyecto del juego

```powershell
git clone --branch 1.1.0 https://github.com/HarbourMasters/Lighthouse.git C:\bk
cd C:\bk
git submodule update --init --depth 1 libultraship
```

Haz que el juego corra **primero en escritorio**, con tu propia ROM: Lighthouse extrae los datos a
un archivo `.o2r` y ese paso no tiene nada que ver con esta receta. Si la versión de escritorio no
funciona, la de UWP tampoco.

## 2. Aplicar la receta

```powershell
python <este repo>\tools\apply_uwp.py C:\bk
```

Dos parches: uno al juego y otro **dentro** del submódulo `libultraship`. El script comprueba los
dos antes de escribir nada y se niega a aplicar uno sin el otro. `--check` informa sin escribir,
`--revert` lo deshace y `--list` explica cada cambio y por qué.

Después se copia el envoltorio a la copia:

```powershell
mkdir C:\bk\uwp
copy <este repo>\src\main.cpp         C:\bk\uwp\
copy <este repo>\src\CMakeLists.txt   C:\bk\uwp\
copy <este repo>\package\Package.appxmanifest C:\bk\uwp\
mkdir C:\bk\uwp\Assets
rem ... y tus trece mosaicos en C:\bk\uwp\Assets (docs/ASSETS.es.md)
```

## 3. Compilar el juego como DLL

```powershell
cmake -S C:\bk -B C:\bk\build-windows -DBUILD_UWP=ON
cmake --build C:\bk\build-windows --config Release
```

`BUILD_UWP=ON` es lo que añade el parche: fuerza `NON_PORTABLE` (así el juego escribe en la carpeta
de datos de la app y no junto al ejecutable), descarga el paquete de dependencias de UWP, saca sdl2
y glfw3 de vcpkg y compila **una DLL** en vez de un ejecutable. El resultado es
`build-windows\Release\Lighthouse.dll`.

## 4. Un certificado para firmar

```powershell
New-SelfSignedCertificate -Type Custom -Subject "CN=<tu nombre>" -KeyUsage DigitalSignature `
  -FriendlyName "<tu nombre> UWP dev" -CertStoreLocation "Cert:\CurrentUser\My" `
  -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
```

Apunta el `Thumbprint` y pon tu `Name` y tu `Publisher` en `C:\bk\uwp\Package.appxmanifest` (la
copia que acabas de hacer). El `Publisher` tiene que ser **exactamente** el `-Subject` de arriba:
`package_uwp.ps1` los compara antes de hacer nada, porque la consola los compara literalmente y
rechaza el paquete si no coinciden.

## 5. Empaquetar, firmar e instalar

```powershell
powershell -ExecutionPolicy Bypass -File <este repo>\tools\package_uwp.ps1 `
    -Tree C:\bk -Thumbprint <tu huella> -Version 0.1.0.0
```

Configura el envoltorio con CMake y deja que MSBuild empaquete y firme. Visual Studio se localiza
con `vswhere`, así que no hay ninguna ruta ni ningún año escritos a mano.

⚠ **La versión tiene que subir en cada ciclo.** La consola no reemplaza un paquete instalado por
otro con la misma versión, y el fallo parece que tu compilación nueva está rota.

Instala el `.msixbundle` desde el **Device Portal** de la consola (`https://<ip de la
consola>:11443`, con el usuario y la contraseña de Dev Home), con el appx de
`Microsoft.VCLibs.140.00` para x64 como dependencia. La consola necesita **un usuario
conectado**.

Después sube al `LocalState` de la app el archivo `.o2r` que produjo la versión de escritorio.

⚠ Dos cosas que cuestan una tarde cada una: la carpeta de datos de la app **no existe hasta que la
app ha corrido una vez**, y los archivos subidos **dentro de un `.zip`** quedan con permisos que el
AppContainer no puede leer. Láncala una vez, ciérrala y sube los archivos de uno en uno.

## 6. Cuando algo sale mal

| Lo que ves | Qué es |
|---|---|
| `unresolved external symbol SDL_main` | El parche del juego no se aplicó (apartado 2) |
| El paquete se instala y se cierra al instante | Un inicializador global llamando a WinRT desde `DllMain`: o sea, falta el parche del juego |
| Pantalla negra con el proceso vivo | ImGui dibujando en un lienzo de 0×0: falta el parche de libultraship |
| Muere a los 3-6 segundos y sin volcado | El paso `ES_WINDOWS`: `getenv` devuelve NULL en UWP (lo explica `--list`) |
| Sin mando | El backend de ventana tiene que ser SDL+OpenGL, no DXGI, y `SDL_INIT_GAMECONTROLLER` tiene que ir después de la ventana |
| La consola rechaza el paquete | El `Publisher` y el sujeto del certificado no son la misma cadena (apartado 4) |
| Instalar «funciona» pero el juego es el viejo | No subió la versión del paquete (apartado 5) |
| El juego no encuentra sus datos | El `.o2r` no está en `LocalState`, o se subió dentro de un zip (apartado 5) |
