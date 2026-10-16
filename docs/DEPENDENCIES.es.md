# Dependencias

*(English: [DEPENDENCIES.md](DEPENDENCIES.md))*

## El proyecto del juego

| | |
|---|---|
| Repositorio | [HarbourMasters/Lighthouse](https://github.com/HarbourMasters/Lighthouse) |
| Versión | **1.1.0**, commit `9c39b49` — contra el que se generaron los parches |
| Submódulo `libultraship` | `62e973a`, el que fija la 1.1.0. El segundo parche se aplica **dentro** de él |
| Licencias | Lighthouse CC0-1.0, libultraship MIT |

⚠ **Por qué aquí la versión importa más de lo normal.** Lighthouse 1.1.0 fija el libultraship de
agosto de 2026, que reorganizó el árbol: `src/graphic/Fast3D/` pasó a `src/fast/` y
`src/Context.cpp` a `src/ship/Context.cpp`. Los parches escritos contra un libultraship anterior
—los de Starship, por ejemplo— no aplican en absoluto. Si pasas a un Lighthouse posterior, cuenta
con rehacer la mitad de libultraship de esta receta; `apply_uwp.py` te lo dirá antes de escribir
nada.

## Tu propia ROM

Banjo-Kazooie (USA). El proyecto extrae los datos él mismo a un archivo `.o2r`, en tu máquina, y
ese archivo es lo que el juego lee en ejecución. Aquí no se distribuye ni la ROM ni el archivo, y
el `.gitignore` bloquea los dos por extensión.

## Herramientas de compilación

| | Qué hace falta | Por qué |
|---|---|---|
| Visual Studio 2022 | Con la **carga de trabajo de C++ para UWP** | MSBuild empaqueta y firma el objetivo UWP. `package_uwp.ps1` localiza Visual Studio con `vswhere`, así que la edición y el año no están escritos a mano |
| CMake | 3.20 o posterior | Para las dos mitades: la DLL del juego y el envoltorio. Si está, se usa el que trae Visual Studio |
| Python 3 | Cualquiera 3.8+ | `tools/apply_uwp.py`, solo biblioteca estándar |
| PowerShell | La **5.1** que trae Windows | `package_uwp.ps1` está probado en ella con la política de ejecución de fábrica. PowerShell 7 no hace falta |
| Paquete de dependencias de UWP | [worleydl/uwp-dep](https://github.com/worleydl/uwp-dep) | SDL2, libuwp, Mesa y glfw3 compilados para UWP. **Lo descarga CMake**; no tiene licencia, así que aquí no se redistribuye nada suyo |

## La consola

Xbox Series X o S en **modo desarrollador**, con un usuario conectado, y el appx de
`Microsoft.VCLibs.140.00` para x64 instalado junto al paquete como dependencia.
