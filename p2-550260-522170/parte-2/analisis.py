#!/usr/bin/env python3
"""Medidas de la busqueda de la parte 2 (datos de la memoria).

Uso:
  ./analisis.py ORIGEN DESTINO HH:MM HOLGURA   detalle de un caso
  ./analisis.py                                bateria de experimentos (semilla fija)

No forma parte de la solucion pedida: solo mide.
"""

import os
import random
import sys

DIRECTORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIRECTORIO_SCRIPT)

from busqueda import fuerza_bruta                                               # noqa: E402
from horarios import Horarios, hora_a_segundos, localizar_csv, segundos_a_hora  # noqa: E402

SEMILLA = 2026
CASOS_POR_CONFIGURACION = 300
HOLGURAS_MINUTOS = (0, 30, 60, 120, 240, 480, 1440)
HORAS_INICIO = ("00:00", "06:00", "12:00", "18:00", "23:00")


def duracion_legible(segundos):
    return f"{segundos // 3600}h{segundos % 3600 // 60:02d}"


def detalle(horarios, origen, destino, hora, holgura_minutos):
    inicio = hora_a_segundos(hora)
    r = fuerza_bruta(horarios, origen, destino, inicio, holgura_minutos * 60)
    print(f"Caso {origen} -> {destino}, inicio {hora}, holgura {holgura_minutos} min")
    if not r.hay_solucion:
        print("  No existe solucion")
    else:
        for vuelo, salida, llegada in r.itinerario:
            print(f"  {vuelo.origen} - {vuelo.destino} {vuelo.callsign} "
                  f"{segundos_a_hora(salida)} - {segundos_a_hora(llegada)} "
                  f"(dia {salida // 86400} -> dia {llegada // 86400})")
        print(f"  Tiempo total: {duracion_legible(r.duracion_total)}")
    print(f"  expandidos {r.expandidos}, generados {r.generados}, "
          f"ramificacion {r.ramificacion_media:.2f}, max abierta {r.maximo_abierta}, "
          f"{r.segundos * 1000:.2f} ms")


def medir(horarios, pares, hora, holgura_minutos):
    """Medias sobre los pares con solucion para una configuracion."""
    inicio = hora_a_segundos(hora)
    resueltos = []
    for origen, destino in pares:
        r = fuerza_bruta(horarios, origen, destino, inicio, holgura_minutos * 60)
        if r.hay_solucion:
            resueltos.append(r)
    n = len(resueltos)
    def media(funcion):
        return sum(funcion(r) for r in resueltos) / n
    return (n, media(lambda r: r.duracion_total) / 3600, media(lambda r: len(r.itinerario)),
            media(lambda r: r.expandidos), media(lambda r: r.generados),
            media(lambda r: r.ramificacion_media), media(lambda r: r.segundos) * 1000)


def bateria(horarios):
    aleatorio = random.Random(SEMILLA)
    aeropuertos = sorted(horarios.salidas)
    vuelos = sum(len(v) for v in horarios.salidas.values())
    print(f"Datos: {len(aeropuertos)} aeropuertos, {vuelos} vuelos diarios, "
          f"ramificacion media {vuelos / len(aeropuertos):.2f}, "
          f"maxima {max(len(v) for v in horarios.salidas.values())}")
    pares = [tuple(aleatorio.sample(aeropuertos, 2)) for _ in range(CASOS_POR_CONFIGURACION)]
    cabecera = (f"{'factibles':>10}{'horas':>8}{'vuelos':>8}{'expand.':>9}"
                f"{'generados':>11}{'ramif.':>8}{'ms':>8}")

    print(f"\nEfecto de la holgura (inicio 00:00, {len(pares)} pares aleatorios)")
    print(f"{'holgura':>8}" + cabecera)
    for holgura in HOLGURAS_MINUTOS:
        fila = medir(horarios, pares, "00:00", holgura)
        print(f"{holgura:>8}{fila[0]:>10}{fila[1]:>8.2f}{fila[2]:>8.2f}{fila[3]:>9.1f}"
              f"{fila[4]:>11.1f}{fila[5]:>8.2f}{fila[6]:>8.2f}")

    print(f"\nEfecto de la hora de inicio (holgura 60 min, mismos pares)")
    print(f"{'inicio':>8}" + cabecera)
    for hora in HORAS_INICIO:
        fila = medir(horarios, pares, hora, 60)
        print(f"{hora:>8}{fila[0]:>10}{fila[1]:>8.2f}{fila[2]:>8.2f}{fila[3]:>9.1f}"
              f"{fila[4]:>11.1f}{fila[5]:>8.2f}{fila[6]:>8.2f}")

    # Peor caso: destino inalcanzable obliga a agotar todo lo alcanzable.
    r = fuerza_bruta(horarios, "MAD", "___", 0, 3600)
    print(f"\nBusqueda exhaustiva desde MAD (destino inexistente): {r.expandidos} expandidos, "
          f"{r.generados} generados, {r.segundos * 1000:.1f} ms")


def main():
    horarios = Horarios(localizar_csv("vertices.csv", DIRECTORIO_SCRIPT),
                        localizar_csv("edges.csv", DIRECTORIO_SCRIPT))
    argumentos = sys.argv[1:]
    if len(argumentos) == 4:
        detalle(horarios, argumentos[0].upper(), argumentos[1].upper(),
                argumentos[2], int(argumentos[3]))
    else:
        bateria(horarios)
    return 0


if __name__ == "__main__":
    sys.exit(main())
