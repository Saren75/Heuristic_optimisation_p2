#!/usr/bin/env python3
"""Parte 1: ruta de minima distancia Haversine entre dos aeropuertos.

Uso: ./sol-1.py <fichero-entrada> <fichero-salida>

Entrada (dos lineas):  codigo IATA de origen / codigo IATA de destino
Salida  (dos lineas):  distancia total en km / recorrido "AAA - BBB - CCC"

La misma informacion se muestra en pantalla y se escribe en el fichero de
salida. Se resuelve con A* (optimo); la fuerza bruta puede lanzarse y
compararse con analisis.py.
"""

import os
import sys

DIRECTORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIRECTORIO_SCRIPT)

from busqueda import a_estrella          # noqa: E402
from grafo import Grafo, localizar_csv   # noqa: E402

MENSAJE_SIN_SOLUCION = "No existe solucion"


def resolver_ruta(nombre):
    """Un nombre sin directorio se interpreta relativo a la carpeta del script."""
    return nombre if os.path.dirname(nombre) else os.path.join(DIRECTORIO_SCRIPT, nombre)


def leer_entrada(ruta):
    """Devuelve (origen, destino) ignorando lineas en blanco."""
    with open(ruta, encoding="utf-8") as fichero:
        lineas = [linea.strip() for linea in fichero if linea.strip()]
    if len(lineas) < 2:
        raise ValueError("el fichero de entrada debe tener dos lineas: origen y destino")
    return lineas[0].upper(), lineas[1].upper()


def formatear_solucion(resultado):
    if not resultado.hay_solucion:
        return MENSAJE_SIN_SOLUCION
    kilometros = resultado.distancia_m / 1000
    return f"{kilometros:.2f}\n{' - '.join(resultado.camino)}"


def main():
    if len(sys.argv) != 3:
        print("Uso: ./sol-1.py <fichero-entrada> <fichero-salida>", file=sys.stderr)
        return 1
    ruta_entrada = resolver_ruta(sys.argv[1])
    ruta_salida = resolver_ruta(sys.argv[2])

    try:
        origen, destino = leer_entrada(ruta_entrada)
        grafo = Grafo(localizar_csv("vertices.csv", DIRECTORIO_SCRIPT),
                      localizar_csv("edges.csv", DIRECTORIO_SCRIPT))
        for aeropuerto in (origen, destino):
            if aeropuerto not in grafo.coordenadas:
                raise ValueError(f"aeropuerto desconocido: {aeropuerto}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    texto = formatear_solucion(a_estrella(grafo, origen, destino))

    print(texto)
    try:
        with open(ruta_salida, "w", encoding="utf-8") as fichero:
            fichero.write(texto + "\n")
    except OSError as error:
        print(f"Error: no se pudo escribir {ruta_salida}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
