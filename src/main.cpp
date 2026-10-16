// Punto de entrada WinRT de Lighthouse para Xbox Series X.
//
// Todo el juego vive en Lighthouse.dll; esto solo registra la vista de WinRT y le cede el hilo.
// La primera llamada a uwp_GetWindowReference() es obligatoria y no es redundante: deja cacheada
// la referencia a la CoreWindow para que los OTROS hilos (el de render, que corre aparte) puedan
// pedirla despues sin tocar el hilo de la interfaz.
//
// Igual que en el port de Diddy Kong Racing, la plantilla C++/CX de SDL no se usa: lo que hace
// cabe en C++ normal.
//
// ACTIVAR LA VENTANA ES OBLIGATORIO, y fue lo que costo el arranque. Sintoma: el proceso moria
// entre t+3 y t+4 SIEMPRE, en el punto del arranque que le tocara, sin excepcion en ningun hilo
// **y sin dejar volcado**. Esa ultima parte es la que lo delata: si no hay volcado no hubo
// crash, o sea que a la aplicacion la estaba matando el sistema. En WinRT una aplicacion que no
// llama a CoreWindow::Activate() al arrancar se da por colgada y el shell la cierra.
//
// Normalmente lo hace SDL al crear su ventana, pero este port no crea ninguna: el backend DXGI de
// libultraship se hace la suya, y en UWP se sustituyo por la CoreWindow del sistema. Con eso, la
// activacion se quedaba sin hacer y nadie lo notaba hasta que la consola cerraba el juego.
//
// LA BITACORA DE ARRANQUE TAMPOCO ES OPCIONAL. En una consola no hay stderr, y si algo lanza
// dentro de SDL_main la excepcion sube hasta el bucle de WinRT, que la traduce a un fail-fast
// (0xC0000409): el volcado solo ensena el fail-fast, no lo que fallo.
#include <Windows.h>
#include <exception>
#include <cstdio>
#include <cstring>

#include <winrt/Windows.UI.Core.h>

#include "SDL2/SDL.h"

extern "C" __declspec(dllimport) void* uwp_GetWindowReference();

static void Apunta(const char* texto) {
    char* base = SDL_GetPrefPath("", "");
    if (base == NULL) {
        return;
    }
    char ruta[512];
    snprintf(ruta, sizeof(ruta), "%sarranque.txt", base);
    FILE* f = fopen(ruta, "a");
    if (f != NULL) {
        fputs(texto, f);
        fputc('\n', f);
        fclose(f);
    }
    SDL_free(base);
}

int bootstrap(int argc, char** argv) {
    uwp_GetWindowReference();

    try {
        winrt::Windows::UI::Core::CoreWindow::GetForCurrentThread().Activate();
        Apunta("[uwp] CoreWindow activada");
    } catch (...) {
        Apunta("[uwp] NO se pudo activar la CoreWindow");
    }

    Apunta("[uwp] entrando a SDL_main");
    try {
        int r = SDL_main(argc, argv);
        Apunta("[uwp] SDL_main devolvio normalmente");
        return r;
    } catch (const std::exception& e) {
        char linea[1024];
        snprintf(linea, sizeof(linea), "[uwp] EXCEPCION: %s", e.what());
        Apunta(linea);
        return 1;
    } catch (...) {
        Apunta("[uwp] EXCEPCION desconocida (no deriva de std::exception)");
        return 1;
    }
}

int CALLBACK WinMain(HINSTANCE, HINSTANCE, LPSTR argv, int argc) {
    return SDL_WinRTRunApp(bootstrap, NULL);
}
