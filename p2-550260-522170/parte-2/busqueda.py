"""Algoritmo de fuerza bruta de la parte 2: coste uniforme sobre (aeropuerto, instante).

Se expande siempre el nodo con menor tiempo transcurrido desde el inicio. Como
todos los costes son positivos (un vuelo dura al menos 15 minutos), el primer
nodo del aeropuerto destino que sale de la lista abierta es el de llegada mas
temprana posible.
"""

import time

from abierta import ListaAbierta
from cerrada import ListaCerrada
from estado import Estado, Nodo

# El enunciado exige holgura "en cada conexion". El primer vuelo no es una
# conexion (no se llega de otro vuelo), asi que puede tomarse desde la misma
# hora de inicio. Poner True si se quisiera exigir holgura tambien al principio.
HOLGURA_EN_PRIMER_VUELO = False


class Resultado:
    """Solucion encontrada y medidas de esfuerzo de la busqueda."""

    def __init__(self):
        self.nodo_meta = None        # None si no existe solucion
        self.expandidos = 0
        self.generados = 0
        self.maximo_abierta = 0
        self.segundos = 0.0

    @property
    def hay_solucion(self):
        return self.nodo_meta is not None

    @property
    def duracion_total(self):
        """Segundos entre la hora de inicio y la llegada al destino."""
        return self.nodo_meta.g

    @property
    def itinerario(self):
        return self.nodo_meta.itinerario()

    @property
    def ramificacion_media(self):
        return self.generados / self.expandidos if self.expandidos else 0.0


def fuerza_bruta(horarios, origen, destino, instante_inicio, holgura):
    """Llegada mas temprana a `destino` saliendo de `origen` en `instante_inicio`.

    Los instantes y la holgura se expresan en segundos.
    """
    resultado = Resultado()
    inicio = time.perf_counter()

    abierta = ListaAbierta()
    cerrada = ListaCerrada()
    abierta.insertar(Nodo(Estado(origen, instante_inicio), 0))

    while not abierta.esta_vacia():
        resultado.maximo_abierta = max(resultado.maximo_abierta, len(abierta))
        nodo = abierta.extraer_minimo()
        aeropuerto = nodo.estado.aeropuerto

        # Prueba de meta al extraer: garantiza que no hay llegada anterior.
        if nodo.estado.es_meta(destino):
            resultado.nodo_meta = nodo
            break

        cerrada.insertar(nodo)
        resultado.expandidos += 1

        # Instante a partir del cual se puede embarcar en otro vuelo.
        if nodo.es_inicial() and not HOLGURA_EN_PRIMER_VUELO:
            disponible_desde = nodo.estado.instante
        else:
            disponible_desde = nodo.estado.instante + holgura

        # Operador tomar(vuelo) para cada vuelo que despega de este aeropuerto.
        for vuelo in horarios.salidas[aeropuerto]:
            resultado.generados += 1
            if cerrada.contiene(vuelo.destino):
                continue   # ya se conoce la llegada mas temprana a ese aeropuerto
            salida = vuelo.proxima_salida(disponible_desde)
            llegada = salida + vuelo.duracion
            # insertar() conserva solo la llegada mas temprana a cada aeropuerto.
            abierta.insertar(Nodo(Estado(vuelo.destino, llegada),
                                  llegada - instante_inicio, nodo, vuelo, salida))

    resultado.segundos = time.perf_counter() - inicio
    return resultado
