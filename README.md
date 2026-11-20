# Heurística y Optimización — Práctica 2: Búsqueda

Curso 2026-27, Universidad Carlos III de Madrid.

Búsqueda de rutas aéreas sobre una red real de vuelos (881 aeropuertos, 26.495 vuelos del 1 de diciembre de 2022):

- **Parte 1** — ruta de mínima distancia Haversine. Fuerza bruta (coste uniforme) y A\* con heurística de distancia en línea recta.
- **Parte 2** — itinerario de mínimo tiempo de viaje con horarios diarios y holgura mínima en cada conexión.

Python 3 sin bibliotecas externas; listas abierta (montículo binario indexado) y cerrada (tabla hash) implementadas a mano.

## Estructura

```
p2-550260-522170/        contenido de la entrega
├── parte-1/             sol-1.py, estado.py, abierta.py, cerrada.py, ...
└── parte-2/             sol-2.py, estado.py, abierta.py, cerrada.py, ...
docs/                    PLAN.md, PROCESO.md, MEMORIA.md y generador del Word
tests/verificar.py       verificador independiente de optimalidad
data/                    datos originales (OpenSky + OpenFlights, ver data/README.md)
```

## Uso

```bash
cd p2-550260-522170/parte-1 && ./sol-1.py ejemplo.in ejemplo.out
cd p2-550260-522170/parte-2 && ./sol-2.py ejemplo.in ejemplo.out
python3 tests/verificar.py
```

## Datos

Los vuelos proceden del OpenSky COVID-19 Flight Dataset (DOI 10.5281/zenodo.7923702), de uso no comercial, y los aeropuertos de OpenFlights. Detalles en `data/README.md`.
