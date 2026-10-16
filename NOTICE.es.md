# Aviso

*(English: [NOTICE.md](NOTICE.md))*

## Sin afiliación

Este es un proyecto de aficionado, no oficial y sin ánimo de lucro. **No está afiliado,
patrocinado ni relacionado** con los titulares de *Banjo-Kazooie*, ni con Microsoft, ni con los
autores de [HarbourMasters/Lighthouse](https://github.com/HarbourMasters/Lighthouse) ni de ninguno de los proyectos sobre los que se construye.
*Banjo-Kazooie*, *Xbox* y todos los nombres y marcas relacionados son de sus respectivos
propietarios.

Aquí no se vende nada y nada está monetizado.

## Qué NO se distribuye en este repositorio

Ninguna ROM. Ningún código del juego de sus titulares. Ningún dato extraído. Ningún ejecutable ni
biblioteca compilados. Ningún paquete. Ninguna partida. Ningún mosaico, que se hicieron con el arte
del propio juego. Ningún certificado de firma, ni la huella de uno.

El `.gitignore` bloquea todo eso por extensión. Es una red de seguridad, no un sustituto de leer
este archivo.

## Qué contiene de trabajo ajeno

Medido, para que «no distribuimos nada suyo» sea algo que puedas comprobar y no algo que tengas
que creerte:

| | Líneas | Qué es | Licencia |
|---|---|---|---|
| Líneas propias de los parches | 304 | Lo que añaden los dos parches, todo bajo `#ifdef _UWP` | nuestras, MIT |
| Citado de Lighthouse | 131 | Las **líneas de contexto** que lleva un diff unificado, más 11 líneas que se quitan | CC0-1.0 |
| Citado de libultraship | 146 | Lo mismo: contexto, más 3 líneas que se quitan | MIT |
| `src/main.cpp`, `src/CMakeLists.txt` | 196 | El envoltorio WinRT que carga la DLL del juego y le cede el hilo | nuestros, MIT |
| `tools/` | 338 | `apply_uwp.py` y `package_uwp.ps1` | nuestros, MIT |

La ROM la pones tú y nunca pasa por aquí, ni tampoco el archivo `.o2r` que el proyecto
construye a partir de ella. El paquete de dependencias de UWP lo descarga CMake en tu
máquina: no tiene licencia, así que aquí no se redistribuye nada suyo.

## Retirada

Si tienes derechos sobre algo de lo anterior y quieres que se retire, escribe a
**jajdpmail@gmail.com** y se retira. Sin discusión y sin demora.
