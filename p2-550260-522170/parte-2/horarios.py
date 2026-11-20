"""Carga de los vuelos y aritmetica de tiempos de la parte 2.

Cada fila de edges.csv es un vuelo observado el 1 de diciembre de 2022. El
enunciado indica que ese horario se repite todos los dias, asi que de cada
vuelo solo se guarda su hora de salida dentro del dia y su duracion.
"""

import csv
import os
from datetime import datetime

SEGUNDOS_POR_DIA = 86400
FORMATO_FECHA = "%Y-%m-%dT%H:%M:%SZ"


def localizar_csv(nombre, directorio_script):
    """Busca un CSV en el directorio de trabajo y, si no esta, junto al script."""
    for directorio in (os.getcwd(), directorio_script):
        ruta = os.path.join(directorio, nombre)
        if os.path.isfile(ruta):
            return ruta
    raise FileNotFoundError(f"no se encuentra {nombre}")


class Vuelo:
    """Vuelo diario.

    hora_salida -- segundos desde las 00:00 UTC a los que despega cada dia
    duracion    -- segundos de vuelo (puede cruzar la medianoche)
    """

    __slots__ = ("origen", "destino", "callsign", "hora_salida", "duracion")

    def __init__(self, origen, destino, callsign, hora_salida, duracion):
        self.origen = origen
        self.destino = destino
        self.callsign = callsign
        self.hora_salida = hora_salida
        self.duracion = duracion

    def proxima_salida(self, disponible_desde):
        """Primer instante >= disponible_desde en que despega este vuelo.

        El vuelo sale en los instantes hora_salida + 86400*k (k = 0, 1, 2...).
        Se busca el menor k que no sea anterior a disponible_desde: es el
        techo de (disponible_desde - hora_salida) / 86400, acotado a 0.
        """
        retraso = disponible_desde - self.hora_salida
        dias = max(0, -(-retraso // SEGUNDOS_POR_DIA))   # division entera hacia arriba
        return self.hora_salida + dias * SEGUNDOS_POR_DIA


class Horarios:
    """Aeropuertos conocidos y vuelos que salen de cada uno."""

    def __init__(self, ruta_vertices, ruta_vuelos):
        self.salidas = {}   # aeropuerto -> lista de Vuelo que despegan de el
        with open(ruta_vertices, newline="", encoding="utf-8") as fichero:
            for fila in csv.DictReader(fichero):
                self.salidas[fila["acronym"]] = []
        with open(ruta_vuelos, newline="", encoding="utf-8") as fichero:
            for fila in csv.DictReader(fichero):
                origen, destino = fila["origin"], fila["destination"]
                # Un vuelo que vuelve al mismo aeropuerto solo consigue llegar
                # mas tarde al mismo sitio: nunca mejora una solucion.
                if origen == destino:
                    continue
                despegue = datetime.strptime(fila["departure_time_utc"], FORMATO_FECHA)
                aterrizaje = datetime.strptime(fila["arrival_time_utc"], FORMATO_FECHA)
                hora_salida = despegue.hour * 3600 + despegue.minute * 60 + despegue.second
                duracion = int((aterrizaje - despegue).total_seconds())
                self.salidas[origen].append(
                    Vuelo(origen, destino, fila["callsign"].strip(), hora_salida, duracion))

    def existe(self, aeropuerto):
        return aeropuerto in self.salidas


def hora_a_segundos(texto):
    """Convierte 'HH:MM' en segundos desde las 00:00."""
    partes = texto.split(":")
    if len(partes) != 2:
        raise ValueError(f"hora no valida: {texto}")
    horas, minutos = int(partes[0]), int(partes[1])
    if not (0 <= horas < 24 and 0 <= minutos < 60):
        raise ValueError(f"hora no valida: {texto}")
    return horas * 3600 + minutos * 60


def segundos_a_hora(instante):
    """Hora del dia 'HH:MM' de un instante absoluto, truncando los segundos.

    Se trunca (no se redondea) porque asi lo hace el ejemplo del enunciado:
    el vuelo IBE31ZM aterriza a las 10:36:53 y se muestra como 10:36.
    """
    segundos_del_dia = instante % SEGUNDOS_POR_DIA
    return f"{segundos_del_dia // 3600:02d}:{segundos_del_dia % 3600 // 60:02d}"
