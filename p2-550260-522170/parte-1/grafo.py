"""Carga de los datos y construccion del grafo de conexiones de la parte 1.

En esta parte se ignoran los horarios: de edges.csv solo interesa que pares
(origen, destino) estan conectados y a que distancia Haversine. Los 26.495
vuelos se reducen asi a un grafo dirigido simple (un arco por par).
"""

import csv
import math
import os

RADIO_TIERRA_KM = 6371.0088   # radio medio usado en README.md para haversine_km
METROS_POR_KM = 1000


def localizar_csv(nombre, directorio_script):
    """Busca un CSV en el directorio de trabajo y, si no esta, junto al script."""
    for directorio in (os.getcwd(), directorio_script):
        ruta = os.path.join(directorio, nombre)
        if os.path.isfile(ruta):
            return ruta
    raise FileNotFoundError(f"no se encuentra {nombre}")


class Grafo:
    """Grafo dirigido de aeropuertos con costes en metros enteros.

    coordenadas[a] -- (latitud, longitud) en radianes del aeropuerto a
    sucesores[a]   -- lista de (b, coste_en_metros) con arco a -> b
    factor_seguridad -- ver _calcular_factor_seguridad
    """

    def __init__(self, ruta_vertices, ruta_arcos):
        self.coordenadas = {}
        self.sucesores = {}
        self._cargar_vertices(ruta_vertices)
        self._cargar_arcos(ruta_arcos)
        self.factor_seguridad = self._calcular_factor_seguridad()

    def _cargar_vertices(self, ruta):
        with open(ruta, newline="", encoding="utf-8") as fichero:
            for fila in csv.DictReader(fichero):
                aeropuerto = fila["acronym"]
                self.coordenadas[aeropuerto] = (
                    math.radians(float(fila["latitude_deg"])),
                    math.radians(float(fila["longitude_deg"])),
                )
                self.sucesores[aeropuerto] = []

    def _cargar_arcos(self, ruta):
        costes = {}   # (origen, destino) -> metros
        with open(ruta, newline="", encoding="utf-8") as fichero:
            for fila in csv.DictReader(fichero):
                origen, destino = fila["origin"], fila["destination"]
                # Un vuelo que vuelve al mismo aeropuerto no cambia el estado
                # y nunca puede formar parte de un camino minimo.
                if origen == destino:
                    continue
                metros = round(float(fila["haversine_km"]) * METROS_POR_KM)
                anterior = costes.get((origen, destino))
                # Varios vuelos del mismo par: nos quedamos con el arco mas corto.
                if anterior is None or metros < anterior:
                    costes[(origen, destino)] = metros
        for (origen, destino), metros in costes.items():
            self.sucesores[origen].append((destino, metros))

    def distancia_haversine_m(self, a, b):
        """Distancia ortodromica en metros entre dos aeropuertos."""
        lat_a, lon_a = self.coordenadas[a]
        lat_b, lon_b = self.coordenadas[b]
        seno_lat = math.sin((lat_b - lat_a) / 2)
        seno_lon = math.sin((lon_b - lon_a) / 2)
        raiz = seno_lat * seno_lat + math.cos(lat_a) * math.cos(lat_b) * seno_lon * seno_lon
        # min(1, ...) protege asin de errores de redondeo en puntos antipodales.
        return 2 * RADIO_TIERRA_KM * METROS_POR_KM * math.asin(min(1.0, math.sqrt(raiz)))

    def _calcular_factor_seguridad(self):
        """Factor rho <= 1 que hace consistente la heuristica pese al redondeo.

        haversine_km viene redondeado a 3 decimales, asi que el coste de un
        arco puede ser hasta 0,5 m MENOR que la distancia real entre sus
        extremos. La distancia en linea recta sin corregir podria entonces
        sobrestimar. Se toma

            rho = min( coste(a,b) / distancia(a,b) )  sobre todos los arcos

        (acotado a 1). Con h(n) = rho * distancia(n, meta) se cumple, para
        todo arco (a,b):

            h(a) - h(b) = rho * (d(a,meta) - d(b,meta))
                        <= rho * d(a,b)           (desigualdad triangular)
                        <= coste(a,b)             (definicion de rho)

        que es exactamente la condicion de consistencia.
        """
        factor = 1.0
        for origen, arcos in self.sucesores.items():
            for destino, metros in arcos:
                distancia = self.distancia_haversine_m(origen, destino)
                if distancia > 0:
                    factor = min(factor, metros / distancia)
        # Margen minimo adicional para absorber el error de coma flotante.
        return factor * (1 - 1e-9)

    def heuristica_hacia(self, destino):
        """Devuelve h(aeropuerto): distancia en linea recta corregida al destino."""
        factor = self.factor_seguridad
        distancia = self.distancia_haversine_m
        return lambda aeropuerto: factor * distancia(aeropuerto, destino)
