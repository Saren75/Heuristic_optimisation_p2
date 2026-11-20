"""Algoritmos de busqueda de la parte 1.

Los dos algoritmos pedidos comparten el mismo bucle (mejor primero con
f = g + h) y solo se diferencian en la funcion h:

  * fuerza bruta  -> h = 0. Es la busqueda de coste uniforme (Dijkstra):
    expande por orden de distancia al origen, sin saber donde esta la meta.
  * heuristico    -> A* con h = distancia en linea recta (corregida) a la meta.

Ambos son optimos. Como h es consistente (ver grafo.py), cuando un nodo sale
de la lista abierta su g ya es la distancia minima a ese estado, y por eso un
estado cerrado nunca necesita reabrirse.
"""

import time

from abierta import ListaAbierta
from cerrada import ListaCerrada
from estado import Estado, Nodo


class Resultado:
    """Solucion encontrada y medidas de esfuerzo de la busqueda."""

    def __init__(self):
        self.nodo_meta = None        # None si no existe solucion
        self.expandidos = 0          # nodos sacados de abierta y expandidos
        self.generados = 0           # sucesores generados (aplicaciones de operador)
        self.maximo_abierta = 0      # tamano maximo alcanzado por la lista abierta
        self.segundos = 0.0

    @property
    def hay_solucion(self):
        return self.nodo_meta is not None

    @property
    def distancia_m(self):
        return self.nodo_meta.g

    @property
    def camino(self):
        return self.nodo_meta.camino()

    @property
    def ramificacion_media(self):
        """Sucesores generados por nodo expandido."""
        return self.generados / self.expandidos if self.expandidos else 0.0


def heuristica_nula(_aeropuerto):
    return 0


def buscar(grafo, origen, destino, heuristica):
    """Mejor primero con f = g + h entre dos aeropuertos.

    `heuristica` es una funcion aeropuerto -> estimacion en metros. Debe ser
    consistente para que el resultado sea optimo sin reabrir nodos.
    """
    resultado = Resultado()
    inicio = time.perf_counter()

    abierta = ListaAbierta()
    cerrada = ListaCerrada()
    abierta.insertar(Nodo(Estado(origen), 0, heuristica(origen)))

    while not abierta.esta_vacia():
        resultado.maximo_abierta = max(resultado.maximo_abierta, len(abierta))
        nodo = abierta.extraer_minimo()
        aeropuerto = nodo.estado.aeropuerto

        # La prueba de meta se hace al EXTRAER, no al generar: solo entonces
        # esta garantizado que no queda en abierta un camino mas corto.
        if nodo.estado.es_meta(destino):
            resultado.nodo_meta = nodo
            break

        cerrada.insertar(nodo)
        resultado.expandidos += 1

        # Operador volar(aeropuerto, vecino) para cada conexion existente.
        for vecino, coste in grafo.sucesores[aeropuerto]:
            resultado.generados += 1
            if cerrada.contiene(vecino):
                continue   # ya se conoce su camino optimo
            # insertar() descarta el nodo si abierta ya tiene uno igual o mejor.
            abierta.insertar(Nodo(Estado(vecino), nodo.g + coste, heuristica(vecino), nodo))

    resultado.segundos = time.perf_counter() - inicio
    return resultado


def fuerza_bruta(grafo, origen, destino):
    """Busqueda no informada de coste uniforme (Dijkstra)."""
    return buscar(grafo, origen, destino, heuristica_nula)


def a_estrella(grafo, origen, destino):
    """Busqueda heuristica A* con la distancia en linea recta corregida."""
    return buscar(grafo, origen, destino, grafo.heuristica_hacia(destino))
