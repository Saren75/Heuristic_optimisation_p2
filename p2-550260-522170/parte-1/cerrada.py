"""Lista cerrada: estados ya expandidos.

Cuando un nodo sale de la lista abierta se ha encontrado el camino optimo
hasta su estado (ver busqueda.py), de modo que ese estado no debe volver a
expandirse. La lista cerrada es una tabla hash (diccionario) estado -> nodo:

  * comprobar si un estado esta cerrado es O(1) de media, que es la operacion
    que se repite una vez por cada sucesor generado;
  * guardar el nodo (y no solo la clave) permite reconstruir el camino
    siguiendo los punteros al padre.
"""


class ListaCerrada:
    """Conjunto de estados expandidos, con acceso al nodo de cada uno."""

    def __init__(self):
        self._nodos = {}   # clave del estado -> nodo con el que se expandio

    def __len__(self):
        return len(self._nodos)

    def contiene(self, clave):
        return clave in self._nodos

    def insertar(self, nodo):
        self._nodos[nodo.estado.clave()] = nodo

    def obtener(self, clave):
        """Nodo con el que se cerro el estado, o None si no esta cerrado."""
        return self._nodos.get(clave)
