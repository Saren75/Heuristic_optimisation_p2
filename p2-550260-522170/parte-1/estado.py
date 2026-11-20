"""Estado y nodo de busqueda de la parte 1 (distancia minima).

Estado: el aeropuerto en el que se encuentra el viajero. No hace falta nada
mas, porque en esta parte se ignoran los horarios: lo que se puede hacer desde
un aeropuerto, y lo que cuesta, no depende de como ni cuando se llego a el.

Nodo: un estado junto con la informacion del camino por el que se alcanzo
(coste acumulado g, estimacion h y nodo padre). Varios nodos pueden referirse
al mismo estado; la busqueda se queda con el de menor g.
"""


class Estado:
    """Aeropuerto actual, identificado por su codigo IATA."""

    __slots__ = ("aeropuerto",)

    def __init__(self, aeropuerto):
        self.aeropuerto = aeropuerto

    def clave(self):
        """Identificador unico del estado para las listas abierta y cerrada."""
        return self.aeropuerto

    def es_meta(self, destino):
        return self.aeropuerto == destino

    def __repr__(self):
        return f"Estado({self.aeropuerto})"


class Nodo:
    """Nodo del arbol de busqueda.

    g     -- coste del camino desde el origen, en METROS enteros (asi las
             sumas son exactas y no se acumula error de coma flotante).
    h     -- estimacion del coste que falta hasta la meta, en metros.
    padre -- nodo desde el que se genero (None en el nodo inicial).
    """

    __slots__ = ("estado", "g", "h", "padre")

    def __init__(self, estado, g, h, padre=None):
        self.estado = estado
        self.g = g
        self.h = h
        self.padre = padre

    @property
    def f(self):
        return self.g + self.h

    def prioridad(self):
        """Orden en la lista abierta: menor f; a igualdad de f, menor h.

        El desempate por h prefiere los nodos mas cercanos a la meta, lo que
        reduce expansiones cuando hay muchos nodos con la misma f.
        """
        return (self.g + self.h, self.h)

    def camino(self):
        """Secuencia de aeropuertos desde el origen hasta este nodo."""
        aeropuertos = []
        nodo = self
        while nodo is not None:
            aeropuertos.append(nodo.estado.aeropuerto)
            nodo = nodo.padre
        aeropuertos.reverse()
        return aeropuertos
