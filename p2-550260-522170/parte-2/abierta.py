"""Lista abierta: cola de prioridad implementada como monticulo binario indexado.

La lista abierta guarda los nodos generados que aun no se han expandido y debe
devolver siempre el de menor prioridad. Se implementa a mano (sin heapq) con:

  * un vector `_monticulo` que representa un arbol binario casi completo en el
    que cada nodo tiene una prioridad menor o igual que la de sus hijos, y
  * un diccionario `_posicion` que dice en que casilla del vector esta el nodo
    de cada estado.

El diccionario es lo que hace al monticulo "indexado": permite localizar en
O(1) el nodo de un estado y, si se encuentra un camino mejor hasta el, mejorar
su prioridad en O(log n) (decrease-key) en lugar de insertar un duplicado.
Asi la lista abierta contiene como mucho un nodo por estado.

Costes: insertar O(log n), extraer el minimo O(log n), mejorar O(log n),
consultar pertenencia O(1).
"""


class ListaAbierta:
    """Cola de prioridad minima con un unico nodo por estado."""

    def __init__(self):
        self._monticulo = []   # nodos ordenados parcialmente por prioridad
        self._posicion = {}    # clave del estado -> indice en _monticulo

    def __len__(self):
        return len(self._monticulo)

    def esta_vacia(self):
        return not self._monticulo

    def contiene(self, clave):
        return clave in self._posicion

    def insertar(self, nodo):
        """Mete el nodo en abierta, o mejora el que ya habia para ese estado.

        Devuelve True si la lista ha cambiado (nodo nuevo o nodo mejorado) y
        False si ya habia un nodo igual o mejor para el mismo estado.
        """
        clave = nodo.estado.clave()
        indice = self._posicion.get(clave)
        if indice is None:
            self._monticulo.append(nodo)
            self._posicion[clave] = len(self._monticulo) - 1
            self._flotar(len(self._monticulo) - 1)
            return True
        if nodo.g < self._monticulo[indice].g:
            # Camino mas barato al mismo estado: se sustituye el nodo. Su
            # prioridad solo puede haber bajado, asi que basta con flotarlo.
            self._monticulo[indice] = nodo
            self._flotar(indice)
            return True
        return False

    def extraer_minimo(self):
        """Saca y devuelve el nodo de menor prioridad."""
        if not self._monticulo:
            raise IndexError("la lista abierta esta vacia")
        minimo = self._monticulo[0]
        ultimo = self._monticulo.pop()
        del self._posicion[minimo.estado.clave()]
        if self._monticulo:
            # El ultimo elemento pasa a la raiz y se hunde hasta su sitio.
            self._monticulo[0] = ultimo
            self._posicion[ultimo.estado.clave()] = 0
            self._hundir(0)
        return minimo

    # ------------------------------------------------------------------
    # Operaciones internas del monticulo
    # ------------------------------------------------------------------
    def _flotar(self, indice):
        """Sube el nodo mientras sea mejor que su padre."""
        monticulo, posicion = self._monticulo, self._posicion
        nodo = monticulo[indice]
        prioridad = nodo.prioridad()
        while indice > 0:
            indice_padre = (indice - 1) // 2
            padre = monticulo[indice_padre]
            if padre.prioridad() <= prioridad:
                break
            monticulo[indice] = padre
            posicion[padre.estado.clave()] = indice
            indice = indice_padre
        monticulo[indice] = nodo
        posicion[nodo.estado.clave()] = indice

    def _hundir(self, indice):
        """Baja el nodo mientras alguno de sus hijos sea mejor que el."""
        monticulo, posicion = self._monticulo, self._posicion
        total = len(monticulo)
        nodo = monticulo[indice]
        prioridad = nodo.prioridad()
        while True:
            indice_hijo = 2 * indice + 1
            if indice_hijo >= total:
                break
            # Se elige el menor de los dos hijos.
            derecho = indice_hijo + 1
            if derecho < total and monticulo[derecho].prioridad() < monticulo[indice_hijo].prioridad():
                indice_hijo = derecho
            hijo = monticulo[indice_hijo]
            if prioridad <= hijo.prioridad():
                break
            monticulo[indice] = hijo
            posicion[hijo.estado.clave()] = indice
            indice = indice_hijo
        monticulo[indice] = nodo
        posicion[nodo.estado.clave()] = indice
