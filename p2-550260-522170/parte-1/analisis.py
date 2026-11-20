#!/usr/bin/env python3
"""Comparacion entre fuerza bruta y A* para la parte 1 (datos de la memoria).

Uso:
  ./analisis.py ORIGEN DESTINO     compara ambos algoritmos en un caso
  ./analisis.py                    bateria de casos aleatorios (semilla fija)
  ./analisis.py N                  igual, con N casos

No forma parte de la solucion pedida: solo mide.
"""

import os
import random
import sys

DIRECTORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIRECTORIO_SCRIPT)

from busqueda import a_estrella, fuerza_bruta   # noqa: E402
from grafo import Grafo, localizar_csv          # noqa: E402

SEMILLA = 2026
CASOS_POR_DEFECTO = 500


def ramificacion_efectiva(nodos, profundidad):
    """Factor b* tal que 1 + b + b^2 + ... + b^d = nodos + 1 (por biseccion)."""
    if profundidad == 0 or nodos <= profundidad:
        return 1.0
    bajo, alto = 1.0, float(nodos)
    for _ in range(60):
        medio = (bajo + alto) / 2
        total = sum(medio ** i for i in range(profundidad + 1))
        if total < nodos + 1:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2


def comprobar_consistencia(grafo, destinos):
    """Mayor violacion de h(a) <= c(a,b) + h(b); debe ser <= 0."""
    peor = float("-inf")
    for destino in destinos:
        h = grafo.heuristica_hacia(destino)
        for origen, arcos in grafo.sucesores.items():
            h_origen = h(origen)
            for vecino, coste in arcos:
                peor = max(peor, h_origen - coste - h(vecino))
    return peor


def contar_optimos(grafo, origen):
    """Para cada aeropuerto alcanzable, numero de caminos optimos distintos.

    Programacion dinamica sobre las distancias minimas: un arco (a,b) esta en
    algun camino optimo si dist[a] + c(a,b) == dist[b].
    """
    distancia = {}
    for destino in grafo.sucesores:
        resultado = fuerza_bruta(grafo, origen, destino)
        if resultado.hay_solucion:
            distancia[destino] = resultado.distancia_m
    caminos = {origen: 1}
    for aeropuerto in sorted(distancia, key=distancia.get):
        for vecino, coste in grafo.sucesores[aeropuerto]:
            if vecino in distancia and distancia[aeropuerto] + coste == distancia[vecino]:
                caminos[vecino] = caminos.get(vecino, 0) + caminos.get(aeropuerto, 0)
    return caminos


def comparar_caso(grafo, origen, destino):
    bruta = fuerza_bruta(grafo, origen, destino)
    heuristica = a_estrella(grafo, origen, destino)
    print(f"Caso {origen} -> {destino}")
    if not bruta.hay_solucion:
        print("  No existe solucion")
    else:
        print(f"  Distancia: {bruta.distancia_m / 1000:.3f} km (FB)  "
              f"{heuristica.distancia_m / 1000:.3f} km (A*)")
        print(f"  Ruta A*: {' - '.join(heuristica.camino)}")
    print(f"  {'':14}{'expandidos':>11}{'generados':>11}{'ramif.':>8}{'max abierta':>13}{'ms':>9}")
    for nombre, r in (("Fuerza bruta", bruta), ("A*", heuristica)):
        print(f"  {nombre:14}{r.expandidos:>11}{r.generados:>11}{r.ramificacion_media:>8.2f}"
              f"{r.maximo_abierta:>13}{r.segundos * 1000:>9.2f}")


def bateria(grafo, casos):
    aleatorio = random.Random(SEMILLA)
    aeropuertos = sorted(grafo.sucesores)
    arcos = sum(len(a) for a in grafo.sucesores.values())
    print(f"Grafo: {len(aeropuertos)} aeropuertos, {arcos} arcos, "
          f"ramificacion media del grafo {arcos / len(aeropuertos):.2f}, "
          f"maxima {max(len(a) for a in grafo.sucesores.values())}")
    print(f"Factor de seguridad rho = {grafo.factor_seguridad:.9f}")
    print(f"Mayor violacion de consistencia (20 metas): "
          f"{comprobar_consistencia(grafo, aleatorio.sample(aeropuertos, 20)):.6f} m (debe ser <= 0)")

    infactibles = discrepancias = 0
    por_saltos = {}   # numero de vuelos de la solucion -> lista de (FB, A*)
    for _ in range(casos):
        origen, destino = aleatorio.sample(aeropuertos, 2)
        bruta = fuerza_bruta(grafo, origen, destino)
        heuristica = a_estrella(grafo, origen, destino)
        if bruta.hay_solucion != heuristica.hay_solucion or (
                bruta.hay_solucion and bruta.distancia_m != heuristica.distancia_m):
            discrepancias += 1
            print(f"  DISCREPANCIA en {origen} -> {destino}")
        if not bruta.hay_solucion:
            infactibles += 1
            continue
        saltos = len(bruta.camino) - 1
        por_saltos.setdefault(saltos, []).append((bruta, heuristica))

    print(f"\n{casos} casos aleatorios: {infactibles} infactibles, "
          f"{discrepancias} discrepancias FB/A*")
    print(f"\n{'vuelos':>6}{'casos':>7} | {'exp FB':>8}{'exp A*':>8}{'ahorro':>8} | "
          f"{'ram FB':>7}{'ram A*':>7} | {'b* FB':>6}{'b* A*':>6} | {'ms FB':>7}{'ms A*':>7}")
    totales = []
    for saltos in sorted(por_saltos):
        pares = por_saltos[saltos]
        totales.extend(pares)
        imprimir_fila(str(saltos), pares, saltos)
    imprimir_fila("todos", totales, None)


def imprimir_fila(etiqueta, pares, saltos):
    n = len(pares)
    def media(funcion):
        return sum(funcion(par) for par in pares) / n
    exp_fb = media(lambda p: p[0].expandidos)
    exp_a = media(lambda p: p[1].expandidos)
    b_fb = media(lambda p: ramificacion_efectiva(p[0].expandidos, len(p[0].camino) - 1))
    b_a = media(lambda p: ramificacion_efectiva(p[1].expandidos, len(p[1].camino) - 1))
    print(f"{etiqueta:>6}{n:>7} | {exp_fb:>8.1f}{exp_a:>8.1f}{100 * (1 - exp_a / exp_fb):>7.1f}% | "
          f"{media(lambda p: p[0].ramificacion_media):>7.2f}"
          f"{media(lambda p: p[1].ramificacion_media):>7.2f} | {b_fb:>6.2f}{b_a:>6.2f} | "
          f"{media(lambda p: p[0].segundos) * 1000:>7.2f}{media(lambda p: p[1].segundos) * 1000:>7.2f}")


def main():
    grafo = Grafo(localizar_csv("vertices.csv", DIRECTORIO_SCRIPT),
                  localizar_csv("edges.csv", DIRECTORIO_SCRIPT))
    argumentos = sys.argv[1:]
    if len(argumentos) == 2:
        comparar_caso(grafo, argumentos[0].upper(), argumentos[1].upper())
    elif len(argumentos) == 1 and argumentos[0] == "optimos":
        aleatorio = random.Random(SEMILLA)
        total = multiples = 0
        for origen in aleatorio.sample(sorted(grafo.sucesores), 5):
            for destino, cantidad in contar_optimos(grafo, origen).items():
                if destino != origen:
                    total += 1
                    multiples += cantidad > 1
        print(f"Pares alcanzables analizados: {total}; con mas de un camino optimo: {multiples}")
    else:
        bateria(grafo, int(argumentos[0]) if argumentos else CASOS_POR_DEFECTO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
