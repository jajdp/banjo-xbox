# Cómo funciona

*(English: [HOW-IT-WORKS.md](HOW-IT-WORKS.md))*

## La forma del port

Un juego de libultraship en una Xbox no puede ser un ejecutable normal: un proceso UWP arranca en
`CoreApplication`, no en `main()`. La arquitectura —tomada de la rama UWP de Starship— le da la
vuelta:

1. el **juego** se compila como una DLL (`-DBUILD_UWP=ON`) que exporta `SDL_main`;
2. un **envoltorio WinRT** de unas doscientas líneas carga esa DLL y le cede el hilo con
   `SDL_WinRTRunApp`;
3. las bibliotecas de UWP (SDL2, libuwp, Mesa, glfw3) vienen de un paquete de dependencias que
   descarga CMake.

Todo lo que esta receta cambia en el juego y en libultraship va bajo `#ifdef _UWP`, así que la
misma copia sigue compilando para escritorio. Los parches de Starship usan `#if 0`; mantener vivos
los dos objetivos es lo que permite volver a aplicar esta receta cuando Lighthouse avance.

## El fallo que más enseña

Durante horas el proceso vivía **entre tres y seis segundos** y desaparecía, en el punto del
arranque que le tocara, **sin excepción en ningún hilo y sin dejar volcado**. Esa última parte es
la pista: si no hay volcado, no hubo crash. Lo mató el sistema, que es lo que WinRT hace con una
aplicación que no presenta su ventana al arrancar.

En una consola no hay stderr, así que el diagnóstico salió de instrumentar el arranque con migas de
pan y marcas de tiempo en un archivo de la carpeta de datos de la app. Eso lo acotó a una línea:

```
[   266 ms] RunExtract: version o2r 1.1.0  shouldRegen=0
[   266 ms] bucle vuelta 0  paso=0
[   266 ms] bucle vuelta 1  paso=1      <-- de aquí no pasaba
```

El paso 1 es `ES_WINDOWS`, y hace dos preguntas de escritorio: ¿me estoy ejecutando desde `%TEMP%`?
y ¿puedo escribir junto al ejecutable? Las dos pasan por `getenv`, y **en UWP `getenv` devuelve
NULL siempre**: el proceso arranca sin bloque de entorno. Con `TEMP` a nulo la ruta no
canonicaliza, y el manejador construye un `std::string` desde el NULL de `USERPROFILE`.

Ninguna de las dos preguntas significa nada dentro de un paquete: las respuestas se saben de
antemano, y de escribir se encarga `NON_PORTABLE`, que lo lleva todo a la carpeta de datos de la
app. Así que el paso se salta entero, y con eso la aplicación pasó de morir a los tres segundos a
vivir indefinidamente a 60 cuadros por segundo.

**La lección que conviene guardar:** cuando una app UWP desaparece sin volcado, no busques un
crash. Busca qué espera el sistema y no está recibiendo.

## Tres más, que parecían otra cosa

- **`unresolved external symbol SDL_main`.** Lighthouse llama así a su entrada pero no la exporta.
  El macro propio de SDL, `SDLMAIN_DECLSPEC`, definido como `__declspec(dllexport)` antes de los
  includes, es todo el arreglo.
- **Se instalaba y se cerraba al instante.** Tres objetos de ruta **globales** corrían sus
  inicializadores dentro de `DllMain`, y `SDL_GetPrefPath` le pregunta a WinRT por
  `ApplicationData::Current`. Llamar a WinRT desde `DllMain` no está permitido; en escritorio la
  misma función resuelve con Win32 y nadie se da cuenta. El arreglo cambia *cuándo*, no *qué*:
  estáticas de función, calculadas en el primer uso. Es mejor código en las dos plataformas,
  porque además quita una dependencia del orden de inicialización estática.
- **Una cadena de intercambio sin tamaño.** `CreateSwapChainForHwnd` deduce el tamaño de la
  ventana, así que el código pasa `Width = 0`. `CreateSwapChainForCoreWindow` no admite 0: no hay
  ventana de la que deducirlo. Una diferencia de contrato entre dos funciones que parecen
  intercambiables.

## El mando: tres capas, cada una tapando a la siguiente

1. el backend de ventana tiene que ser **SDL+OpenGL**, no DXGI: en esta consola es el único por el
   que llega el mando;
2. la navegación por mando hay que **forzarla** en UWP;
3. `SDL_INIT_GAMECONTROLLER` tiene que inicializarse **después** de crear la ventana, no antes.

Arreglas una y el mando sigue muerto, que es lo que hace caro este tipo de fallo.

## Cómo se verificó esto

Sobre un **clon nuevo de Lighthouse 1.1.0 (`9c39b49`)** con su submódulo `libultraship`, el
2026-10-14: los dos parches aplican limpios, la receta reproduce el árbol del que salió el paquete
instalado —**13 de 13 archivos idénticos byte a byte** una vez normalizados los finales de línea— y
una segunda corrida no escribe nada.

⚠ El árbol de trabajo se clonó con `core.autocrlf=true` y el clon de verificación sin él, así que
uno tiene CRLF en disco y el otro LF: comparados en crudo, los 13 archivos «difieren» y nada de eso
es contenido. Normaliza antes de concluir nada cuando compares dos copias.

Lo que **no** se vuelve a medir aquí es la salida de MSBuild: eso necesita el paquete de
dependencias y una compilación completa del juego. El paquete que corre en las consolas se
construyó con este mismo árbol.

## Sobre el idioma

`tools/package_uwp.ps1` está en inglés. Los parches llevan algunos comentarios en español, que es
donde se escribieron, y se publican tal como se compilaron y se verificaron en vez de volver a
teclearlos.
