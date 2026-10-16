cmake_minimum_required(VERSION 3.14)

# Envoltorio WinRT de Lighthouse para Xbox Series X.
#
# Derivado del de Starship (JRickey/Starship, rama uwp-2026-rebase), que es el unico port de
# libultraship con soporte UWP publicado. El reparto de trabajo es el mismo:
#   - el juego se compila como DLL (Lighthouse.dll) con -DBUILD_UWP=ON
#   - este proyecto es un ejecutable WinRT minimo que la carga y le cede el hilo
#
# Se construye APARTE del juego, con CMAKE_SYSTEM_NAME=WindowsStore, porque son dos mundos
# distintos: la DLL se compila como binario de escritorio y solo el envoltorio es de la tienda.

set(CMAKE_SYSTEM_NAME WindowsStore)
set(CMAKE_SYSTEM_VERSION 10.0.19041.0)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type (Debug, Release, RelWithDebInfo, MinSizeRel)" FORCE)
endif()

project(lighthouse-uwp LANGUAGES CXX)
set_directory_properties(PROPERTIES VS_STARTUP_PROJECT ${PROJECT_NAME})

set(LIGHTHOUSE_DIR "" CACHE PATH "")
if(NOT LIGHTHOUSE_DIR)
  message(FATAL_ERROR "LIGHTHOUSE_DIR debe apuntar a la carpeta de build de la DLL")
endif()

add_executable(${PROJECT_NAME} WIN32
	main.cpp
)

# Lo que viaja dentro del paquete. Ojo: bk.o2r (los assets del juego, 24 MB) NO va aqui: se sube
# a LocalState, igual que se hizo con Star Fox 64, porque sale del volcado del usuario.
set(BinDeps
	${LIGHTHOUSE_DIR}/Lighthouse.dll

	${LIGHTHOUSE_DIR}/../lighthouse.o2r

	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/dxil.dll
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/glfw3.dll
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/libgallium_wgl.dll
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/libuwp.dll
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/opengl32.dll
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/SDL2.dll
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/bin/z-1.dll

	Package.appxmanifest
)
source_group("BinDeps" FILES ${BinDeps})
set_source_files_properties(${BinDeps} PROPERTIES
	VS_COPY_TO_OUT_DIR Always
	VS_DEPLOYMENT_CONTENT TRUE
	VS_DEPLOYMENT_LOCATION "."
)

set(PkgAssets
	Assets/Square44x44Logo.png
	Assets/Square44x44Logo.scale-200.png
	Assets/Square44x44Logo.targetsize-24_altform-unplated.png
	Assets/Square150x150Logo.png
	Assets/Square150x150Logo.scale-200.png
	Assets/SplashScreen.png
	Assets/SplashScreen.scale-200.png
	Assets/StoreLogo.png
)
source_group("PkgAssets" FILES ${PkgAssets})
set_source_files_properties(${PkgAssets} PROPERTIES
	VS_DEPLOYMENT_CONTENT TRUE
	VS_DEPLOYMENT_LOCATION "Assets"
)

# Los assets del port (yaml de Torch y demas) conservando su estructura de carpetas.
file(GLOB_RECURSE DATA_FILES
	RELATIVE ${CMAKE_SOURCE_DIR}/..
	${CMAKE_SOURCE_DIR}/../assets/*
)

foreach(ASSET ${DATA_FILES})
	set(FULL_PATH "${CMAKE_SOURCE_DIR}/../${ASSET}")
	get_filename_component(DEST_DIR ${ASSET} DIRECTORY)
	set_source_files_properties("${FULL_PATH}" PROPERTIES
		VS_COPY_TO_OUT_DIR Always
		VS_DEPLOYMENT_CONTENT TRUE
		VS_DEPLOYMENT_LOCATION "${DEST_DIR}"
	)
	target_sources(${PROJECT_NAME} PRIVATE "${FULL_PATH}")
	source_group("BinData" FILES "${FULL_PATH}")
endforeach()

target_sources(${PROJECT_NAME} PRIVATE
	${BinDeps}
	${PkgAssets}
)

# La bitacora de arranque usa fopen y aqui C4996 es error.
target_compile_definitions(${PROJECT_NAME} PRIVATE _CRT_SECURE_NO_WARNINGS)

target_include_directories(${PROJECT_NAME} PRIVATE
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/include
)

set(BinLibs
	${LIGHTHOUSE_DIR}/${CMAKE_BUILD_TYPE}/Lighthouse.lib

	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/lib/libuwp.lib
	${LIGHTHOUSE_DIR}/_deps/uwplibs-src/x64/lib/SDL2.lib

	OneCore.lib
	WindowsApp.lib
)
target_link_libraries(${PROJECT_NAME} PRIVATE ${BinLibs})
set_target_properties(${PROJECT_NAME} PROPERTIES VS_WINDOWS_TARGET_PLATFORM_MIN_VERSION 10.0.19041.0)
