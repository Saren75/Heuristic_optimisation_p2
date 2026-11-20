#!/usr/bin/env python3
"""Parte 2: itinerario de minimo tiempo de viaje entre dos aeropuertos.

Uso: ./sol-2.py <fichero-entrada> <fichero-salida>

Entrada (cuatro lineas): IATA origen / IATA destino / HH:MM de inicio (UTC) /
                         holgura minima en cada conexion, en minutos
Salida (una linea por vuelo): "ORI - DES CALLSIGN HH:MM - HH:MM"

La misma informacion se muestra en pantalla y se escribe en el fichero de
salida.
"""

import os
import sys

DIRECTORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIRECTORIO_SCRIPT)

from busqueda import fuerza_bruta                                               # noqa: E402
from horarios import Horarios, hora_a_segundos, localizar_csv, segundos_a_hora  # noqa: E402

MENSAJE_SIN_SOLUCION = "No existe solucion"


def resolver_ruta(nombre):
    """Un nombre sin directorio se interpreta relativo a la carpeta del script."""
    return nombre if os.path.dirname(nombre) else os.path.join(DIRECTORIO_SCRIPT, nombre)


def leer_entrada(ruta):
    """Devuelve (origen, destino, instante_inicio_s, holgura_s)."""
    with open(ruta, encoding="utf-8") as fichero:
        lineas = [linea.strip() for linea in fichero if linea.strip()]
    if len(lineas) < 4:
        raise ValueError("el fichero de entrada debe tener cuatro lineas: "
                         "origen, destino, HH:MM y holgura en minutos")
    holgura_minutos = int(lineas[3])
    if holgura_minutos < 0:
        raise ValueError("la holgura no puede ser negativa")
    return lineas[0].upper(), lineas[1].upper(), hora_a_segundos(lineas[2]), holgura_minutos * 60


def formatear_solucion(resultado):
    if not resultado.hay_solucion:
        return MENSAJE_SIN_SOLUCION
    return "\n".join(
        f"{vuelo.origen} - {vuelo.destino} {vuelo.callsign} "
        f"{segundos_a_hora(salida)} - {segundos_a_hora(llegada)}"
        for vuelo, salida, llegada in resultado.itinerario)


def main():
    if len(sys.argv) != 3:
        print("Uso: ./sol-2.py <fichero-entrada> <fichero-salida>", file=sys.stderr)
        return 1
    ruta_entrada = resolver_ruta(sys.argv[1])
    ruta_salida = resolver_ruta(sys.argv[2])

    try:
        origen, destino, instante_inicio, holgura = leer_entrada(ruta_entrada)
        horarios = Horarios(localizar_csv("vertices.csv", DIRECTORIO_SCRIPT),
                            localizar_csv("edges.csv", DIRECTORIO_SCRIPT))
        for aeropuerto in (origen, destino):
            if not horarios.existe(aeropuerto):
                raise ValueError(f"aeropuerto desconocido: {aeropuerto}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    texto = formatear_solucion(fuerza_bruta(horarios, origen, destino, instante_inicio, holgura))

    # Si origen y destino coinciden no hay ningun vuelo que mostrar.
    if texto:
        print(texto)
    try:
        with open(ruta_salida, "w", encoding="utf-8") as fichero:
            fichero.write(texto + "\n" if texto else "")
    except OSError as error:
        print(f"Error: no se pudo escribir {ruta_salida}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
