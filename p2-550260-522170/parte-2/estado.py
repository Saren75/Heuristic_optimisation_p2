"""Estado y nodo de busqueda de la parte 2 (tiempo minimo de viaje).

Estado: (aeropuerto, instante). A diferencia de la parte 1, aqui el aeropuerto
no basta: los vuelos que se pueden tomar, y cuanto hay que esperarlos, dependen
de la hora a la que se esta en el aeropuerto.

Todos los instantes son segundos enteros contados desde las 00:00 UTC del dia
en que empieza el viaje (dia 0). Un instante mayor que 86400 cae en dias
posteriores.

Dominancia: dos estados del mismo aeropuerto son comparables. Quien llega
antes puede esperar y hacer exactamente lo mismo que quien llega despues, asi
que el estado con menor instante nunca es peor. Por eso clave() devuelve solo
el aeropuerto: las listas abierta y cerrada conservan, para cada aeropuerto,
unicamente el nodo que llega antes.
"""


class Estado:
    """Aeropuerto en el que se esta y momento en que se llego a el."""

    __slots__ = ("aeropuerto", "instante")

    def __init__(self, aeropuerto, instante):
        self.aeropuerto = aeropuerto
        self.instante = instante

    def clave(self):
        """Identificador para abierta y cerrada (ver 'Dominancia' arriba)."""
        return self.aeropuerto

    def es_meta(self, destino):
        return self.aeropuerto == destino

    def __repr__(self):
        return f"Estado({self.aeropuerto}, t={self.instante})"


class Nodo:
    """Nodo del arbol de busqueda.

    g      -- segundos transcurridos desde la hora de inicio del viaje
              (esperas incluidas). Es la metrica que se minimiza.
    padre  -- nodo desde el que se genero (None en el nodo inicial).
    vuelo  -- vuelo tomado para llegar aqui (None en el nodo inicial).
    salida -- instante absoluto en que despego ese vuelo.
    """

    __slots__ = ("estado", "g", "padre", "vuelo", "salida")

    def __init__(self, estado, g, padre=None, vuelo=None, salida=None):
        self.estado = estado
        self.g = g
        self.padre = padre
        self.vuelo = vuelo
        self.salida = salida

    def prioridad(self):
        """Orden en la lista abierta: menor tiempo transcurrido primero."""
        return self.g

    def es_inicial(self):
        return self.padre is None

    def itinerario(self):
        """Lista de (vuelo, salida, llegada) desde el origen hasta este nodo."""
        tramos = []
        nodo = self
        while not nodo.es_inicial():
            tramos.append((nodo.vuelo, nodo.salida, nodo.estado.instante))
            nodo = nodo.padre
        tramos.reverse()
        return tramos
