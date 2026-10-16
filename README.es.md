# Banjo-Kazooie en la Xbox — el port UWP

Cómo coger la decompilación [Lighthouse](https://github.com/HarbourMasters/Lighthouse) de
*Banjo-Kazooie* (Nintendo 64, 1998) y hacerla correr **en una Xbox Series en modo
desarrollador**, como un paquete UWP que compilas y firmas tú.

No es una teoría: el juego se juega en dos consolas, y nadie más lo había portado — un censo
de los **19 forks** de Lighthouse el 2026-09-16 encontró ports de iOS, macOS, Wii U y uno de
XR móvil, y ninguna rama de UWP.

*(English: [README.md](README.md))*

## Qué es este repositorio

**Una receta y las herramientas que la aplican.** La arquitectura es la que usa
[JRickey/Starship](https://github.com/JRickey/Starship) en su rama `uwp-2026-rebase`, que es
el único port UWP publicado de un juego de libultraship: el juego se compila como **DLL**
exportando `SDL_main`, un **envoltorio WinRT mínimo** la carga y le cede el hilo con
`SDL_WinRTRunApp`, y las bibliotecas de UWP vienen de un paquete de dependencias que CMake
descarga él solo.

⚠ **Los parches de Starship no aplican a este juego**, y ese es el trabajo que es este
repositorio: están escritos contra el libultraship de octubre de 2025, mientras Lighthouse
1.1.0 fija el de agosto de 2026, que además reorganizó el árbol
(`src/graphic/Fast3D/` → `src/fast/`, `src/Context.cpp` → `src/ship/Context.cpp`). Cada
cambio se reimplementó en su sitio nuevo y se puso bajo `#ifdef _UWP` en vez del `#if 0` de
Starship, para que un mismo árbol siga compilando también para escritorio.

## Qué **no** es

Aquí **no hay ROM, ni código del juego, ni ejecutable, ni paquete, ni arte**. Esto no puede dar un
juego jugable por sí solo, y nada de lo que te puedas descargar aquí es un juego. Necesitas tu
propio volcado legal del juego. Ver [`NOTICE.es.md`](NOTICE.es.md).

Los mosaicos del paquete tampoco están: los de la consola de verdad se hicieron con el arte
del propio juego. En [`docs/ASSETS.es.md`](docs/ASSETS.es.md) está lo que hace falta.

Tampoco el **paquete de dependencias de UWP**
([worleydl/uwp-dep](https://github.com/worleydl/uwp-dep)): son binarios de otra gente y no
tiene licencia, así que CMake lo descarga en tu máquina y aquí no pasa nada suyo.

## Qué hace falta antes

| | |
|---|---|
| El proyecto del juego | [HarbourMasters/Lighthouse](https://github.com/HarbourMasters/Lighthouse) **1.1.0** (commit `9c39b49`) con su submódulo `libultraship` (`62e973a`), **compilando y corriendo antes en tu PC** |
| Tu propia ROM | Banjo-Kazooie (USA). El proyecto extrae sus datos a un archivo `.o2r` en tu máquina; aquí no se distribuye ni la ROM ni ese archivo |
| Visual Studio | 2022 con la **carga de trabajo de C++ para UWP**: aquí MSBuild empaqueta y firma |
| CMake | 3.20 o posterior (el que viene con Visual Studio sirve) |
| Python 3 | Para `tools/apply_uwp.py`. Solo biblioteca estándar |
| Una Xbox en modo desarrollador | Y un certificado para firmar ([`docs/INSTALL.es.md`](docs/INSTALL.es.md) apartado 4) |

## Cómo va

```powershell
# 1. parchear tu copia: el juego y su submódulo libultraship
python tools\apply_uwp.py <ruta-a-tu-copia-de-lighthouse>

# 2. compilar el juego como DLL (docs/INSTALL.es.md apartado 3)
#    cmake -S . -B build-windows -DBUILD_UWP=ON  &&  cmake --build build-windows --config Release

# 3. copiar el envoltorio a la copia y empaquetar
#    (src\main.cpp + src\CMakeLists.txt -> <copia>\uwp\, y package\Package.appxmanifest)
powershell -ExecutionPolicy Bypass -File tools\package_uwp.ps1 `
    -Tree <ruta-a-tu-copia> -Thumbprint <tu certificado> -Version 0.1.0.0
```

`python tools\apply_uwp.py --list` imprime los dos parches y qué resuelve cada cambio.

Paso a paso, incluido el lado de la consola: **[`docs/INSTALL.es.md`](docs/INSTALL.es.md)**.

## Qué hubo que resolver

Cada una de estas cosas fue un fallo real en la consola. El detalle está en
**[`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md)**.

| | Síntoma | Arreglo |
|---|---|---|
| 1 | `unresolved external symbol SDL_main` | Lighthouse llama así a su entrada pero no la exporta. Se marca con el macro propio de SDL, `SDLMAIN_DECLSPEC`, definido como `__declspec(dllexport)` antes de los includes |
| 2 | El paquete se instalaba y se cerraba al instante, sin volcado | Tres objetos de ruta **globales** corrían sus inicializadores dentro de `DllMain`, y `SDL_GetPrefPath` le pregunta a WinRT por `ApplicationData::Current`. **Llamar a WinRT desde DllMain no está permitido.** El arreglo cambia *cuándo*, no *qué*: estáticas de función, calculadas en el primer uso |
| 3 | Pantalla negra con el proceso vivo | `CreateSwapChainForCoreWindow` no admite un tamaño de 0, mientras `CreateSwapChainForHwnd` lo deduce de la ventana. Ancho y alto explícitos |
| 4 | **El proceso moría a los 3-6 segundos, sin excepción y sin volcado** | Que no haya volcado significa que no hubo crash: lo mató el sistema, que es lo que WinRT hace con una app que no presenta su ventana al arrancar. La causa era un paso del arranque — el siguiente |
| 5 | Ese paso: `ES_WINDOWS` | Hace dos preguntas de escritorio (¿me ejecuto desde `%TEMP%`?, ¿puedo escribir junto al ejecutable?) con `getenv`, y **en UWP `getenv` devuelve NULL siempre**: un `std::string` construido desde el NULL de `USERPROFILE`. Ninguna de las dos preguntas significa nada en un paquete, así que el paso se salta entero. Con eso, la app pasó de morir a los 3 segundos a vivir indefinidamente a 60 fps |
| 6 | Después: pantalla negra otra vez, dibujando pero invisible | `ImGui_ImplWin32_NewFrame` saca el tamaño de pantalla de `GetClientRect(hWnd)`, y en este port el `hWnd` es una CoreWindow disfrazada: la llamada falla, el rectángulo queda a cero y todo se dibuja sobre un lienzo de 0×0. El tamaño sale de `uwp_GetScreenSize` |
| 7 | Sin mando | Tres capas, cada una tapando a la siguiente: el backend de ventana tiene que ser SDL+OpenGL (no DXGI), porque es el único por el que llega el mando; la navegación por mando hay que forzarla; y `SDL_INIT_GAMECONTROLLER` tiene que ir **después** de crear la ventana |

## Cómo se verificó

No leyéndolo: reconstruyendo el árbol. Sobre un **clon nuevo de Lighthouse 1.1.0 (`9c39b49`)**
con su submódulo `libultraship`, el 2026-10-14:

| Qué se midió | Resultado |
|---|---|
| Los dos parches aplican a una copia limpia | Sí, limpios, con `git apply --check` primero y sin escribir nada si algo falla |
| El árbol que produce la receta, contra el árbol del que salió el paquete instalado | **13 de 13 archivos idénticos**, byte a byte, una vez normalizados los finales de línea |
| Idempotencia | Una segunda corrida dice `already applied` y no escribe nada |
| `tools/package_uwp.ps1` | Parsea y valida con la **PowerShell 5.1 que trae Windows**, con la política de ejecución de fábrica, y rechaza un árbol que no existe, una DLL que falta, un manifiesto con `CHANGE-ME`, un certificado sin clave privada y un `Publisher` que no coincide con el certificado |

⚠ **Sobre esos finales de línea:** el árbol de trabajo se clonó con `core.autocrlf=true` (el valor
por defecto de Git para Windows) y el clon de verificación sin él, así que uno tiene CRLF en disco y
el otro LF. Normalizando, los 13 archivos son idénticos; comparados en crudo, los 13 «difieren» y
nada de eso es contenido. Conviene saberlo antes de comparar dos copias y pensar que la receta está
mal.

Lo que **no** se vuelve a medir aquí es la salida de MSBuild: rehacer el paquete necesita el paquete
de dependencias de UWP y una compilación completa del juego, y el paquete que corre en las consolas
se construyó con este mismo árbol. Lo verificado es la receta.

## Créditos y licencia

Port y herramientas de **Recompilaciones**, bajo la [MIT License](LICENSE).
El proyecto del juego es CC0-1.0 y el motor que este port parchea, libultraship, es MIT; la
MIT es la que cubre los dos y pide atribución, que es la lectura honesta.

La arquitectura viene de [JRickey/Starship](https://github.com/JRickey/Starship) (CC0-1.0),
cuya rama `uwp-2026-rebase` es el único port UWP publicado de un juego de libultraship. Sus
parches no se reutilizan aquí —no aplican a esta versión del motor—, pero la forma de la
solución es suya y merece decirse.

*Banjo-Kazooie* es © de sus titulares. Este proyecto no está afiliado con ellos, ni con Microsoft, ni
con los autores de los proyectos sobre los que se construye, y no distribuye nada que les
pertenezca. El detalle está en [`NOTICE.es.md`](NOTICE.es.md). Los titulares de derechos pueden
escribir a **jajdpmail@gmail.com**.
