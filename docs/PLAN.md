# Plan de ejecución — Práctica 2: Búsqueda (Heurística y Optimización 2026-27)

Entrega: **viernes 4 de diciembre, 23:55** (límite fijo). Autores: 550260 y 522170.

Este documento es la referencia de *qué* hay que hacer y *en qué orden*. El *cómo se hizo y por qué* está en [PROCESO.md](PROCESO.md) y el texto de la memoria en [MEMORIA.md](MEMORIA.md).

---

## 1. Requisitos extraídos del enunciado

Cada requisito tiene un identificador para poder marcarlo en la lista de comprobación final (§7).

### 1.1 Generales

| Id | Requisito |
|----|-----------|
| G1 | Ficheros separados `estado`, `abierta`, `cerrada` (aquí `.py`) **en cada parte**. |
| G2 | Estructuras de datos implementadas **nativamente** (no usar `heapq`, `networkx`, etc. para el núcleo de la búsqueda). |
| G3 | Script Python 3.12 (`sol-1.py`, `sol-2.py`) con **exactamente dos argumentos**: fichero de entrada y fichero de salida. |
| G4 | Rutas absolutas o relativas; **si el nombre no lleva ruta, se asume el directorio del script**. |
| G5 | La solución se escribe **en pantalla y en el fichero de salida** (misma información). |
| G6 | `vertices.csv` y `edges.csv` se cargan automáticamente desde el directorio donde se ejecuta el script. |
| G7 | La solución devuelta tiene que ser **óptima** (si no, máximo 0,5 puntos). |
| G8 | Código organizado, nombres descriptivos, comentado. |
| G9 | La implementación debe corresponderse **íntegramente** con el modelo de la memoria. |

### 1.2 Parte 1 — distancia mínima (4 puntos)

| Id | Requisito |
|----|-----------|
| P1.1 | Modelo de espacio de estados: estados, operadores, precondiciones, postcondiciones, coste. |
| P1.2 | Se ignoran los horarios; solo cuenta que exista conexión origen→destino en `edges.csv`. |
| P1.3 | Algoritmo de **fuerza bruta** y algoritmo **heurístico**. |
| P1.4 | Entrada: línea 1 IATA origen, línea 2 IATA destino. |
| P1.5 | Salida: línea 1 distancia total en km (2 decimales, punto decimal); línea 2 recorrido `MAD - VIE - KSC - BTS`. |

### 1.3 Parte 2 — tiempo mínimo (3 puntos)

| Id | Requisito |
|----|-----------|
| P2.1 | Modelo de espacio de estados (igual que P1.1). |
| P2.2 | Se usan las horas UTC de despegue y aterrizaje. |
| P2.3 | La hora de inicio es dato de entrada. |
| P2.4 | Los horarios del 1-dic-2022 **se repiten todos los días**. |
| P2.5 | Holgura mínima (minutos) en **cada conexión**. |
| P2.6 | Algoritmo de **fuerza bruta** (no se pide heurística). |
| P2.7 | Entrada: origen, destino, `HH:MM`, holgura en minutos (4 líneas). |
| P2.8 | Salida: una línea por vuelo `MAD - VIE IBE31ZM 08:13 - 10:36`. |

### 1.4 Parte 3 — análisis (3 puntos)

| Id | Requisito |
|----|-----------|
| A1 | Factor de ramificación observado (fuerza bruta y heurística). |
| A2 | ¿Hay instancias infactibles? ¿Puede haber varias soluciones óptimas? |
| A3 | Casos variados; cómo afectan los parámetros a la dificultad; qué influye en el tiempo. |
| A4 | Tamaños máximos resolubles. |
| A5 | Comparación fuerza bruta vs heurística en la parte 1 (2 de los 3 puntos). |

### 1.5 Memoria y entrega

| Id | Requisito |
|----|-----------|
| M1 | PDF, **máximo 15 hojas** contando portada e índice. **Sin código fuente.** |
| M2 | Introducción, modelo de cada parte con notación algebraica, análisis. |
| M3 | Justificar las estructuras de datos elegidas. |
| E1 | `p2-550260-522170.zip` → directorio `p2-550260-522170/` con `550260-522170.pdf`, `autores.txt` (UTF-8), `parte-1/`, `parte-2/`. |
| E2 | Memoria aparte por Turnitin: `550260-522170.pdf`. |

---

## 2. Hechos comprobados sobre los datos

Comprobados con un script antes de diseñar nada (los números condicionan el diseño):

- 881 aeropuertos, 26.495 vuelos, 9.870 pares (origen, destino) distintos.
- Todos los vuelos despegan el 1-dic; 3.161 aterrizan el 2-dic (cruzan medianoche). Ninguno llega antes de salir.
- **712 vuelos tienen origen = destino** (0 km). No sirven para nada en ninguna de las dos partes y se descartan.
- Todos los vuelos de un mismo par tienen el mismo `haversine_km` → en la parte 1 el multigrafo se reduce a un grafo simple.
- `haversine_km` está **redondeado a 3 decimales**: difiere hasta ±0,0005 km de la distancia calculada con las coordenadas. Esto importa para la heurística (§3.1).
- 173 aeropuertos no tienen ninguna salida y 96 no tienen ninguna llegada → **existen instancias infactibles**.
- Las horas tienen segundos (`08:13:47`). El ejemplo del enunciado muestra `08:13` y `10:36` para `10:36:53` → la salida **trunca** a minutos, no redondea.
- Las distancias del ejemplo del enunciado (41,7 y 32,9 km) **no coinciden con los datos** (350,333 y 302,272). El ejemplo es ilustrativo; no se puede usar como test de regresión del valor numérico.

---

## 3. Decisiones de diseño (resumen; la justificación completa va en PROCESO.md)

### 3.1 Parte 1

- **Estado**: el aeropuerto actual. **Operador** `volar(a,b)`: precondición, existe conexión a→b; postcondición, estoy en b; coste, `haversine_km(a,b)`.
- **Costes en metros enteros** (`km × 1000`) para que las sumas y comparaciones sean exactas.
- **Fuerza bruta**: coste uniforme (Dijkstra). Es A\* con h = 0.
- **Heurística**: A\* con `h(n) = ρ · haversine(n, meta)` calculada con las coordenadas. `ρ ≤ 1` es un factor de seguridad calculado al cargar los datos (`ρ = mín(coste_csv / distancia_real)` sobre todas las aristas) que **garantiza consistencia pese al redondeo** del CSV. Sin ρ la heurística podría sobrestimar hasta 0,5 m por arista.
- **Abierta**: montículo binario indexado propio (inserción, extracción y *decrease-key* en O(log n)).
- **Cerrada**: tabla hash (consulta O(1)).

### 3.2 Parte 2

- **Estado**: (aeropuerto, instante de llegada). Tiempo en **segundos** desde las 00:00 del día 0.
- **Operador** `tomar(vuelo)`: precondición, el vuelo sale del aeropuerto actual; se toma su **primera salida diaria** no anterior a `t + holgura`; postcondición, (destino, hora de llegada); coste, espera + duración.
- **La holgura no se aplica al primer vuelo** (no es una conexión). ⚠️ Interpretación del enunciado; es un único punto del código por si hay que cambiarlo.
- **Fuerza bruta**: coste uniforme. **Poda por dominancia**: para un mismo aeropuerto, llegar antes nunca es peor (se puede esperar), así que la cerrada se indexa por aeropuerto.

### 3.3 Decisiones donde el enunciado no dice nada

| Caso | Decisión |
|------|----------|
| No hay ruta | Se escribe `No existe solucion` en pantalla y fichero. |
| Origen = destino | Parte 1: `0.00` y el código. Parte 2: salida vacía (0 vuelos). |
| Código IATA desconocido o entrada mal formada | Mensaje por `stderr`, código de salida 1, no se crea fichero. |
| Formato parte 2 | Solo el *callsign* (el enunciado mezcla nombre de aerolínea en 2 de 3 líneas del ejemplo, pero la especificación formal dice solo *callsign*). |
| `sol-1.py` con solo 2 argumentos | Ejecuta el heurístico (A\*). La fuerza bruta se lanza con `analisis.py`. |
| CSV | Se buscan en el directorio de trabajo y, si no están, junto al script. |

---

## 4. Estructura de ficheros

```
segunda practica/
├── docs/                      PLAN.md, PROCESO.md, MEMORIA.md (no se entregan)
├── data/                      CSV originales
└── p2-550260-522170/          ← lo que se comprime
    ├── autores.txt
    ├── 550260-522170.pdf      (al final)
    ├── parte-1/
    │   ├── estado.py  abierta.py  cerrada.py
    │   ├── grafo.py           carga de CSV, Haversine, factor ρ
    │   ├── busqueda.py        A* genérico (h=0 → fuerza bruta)
    │   ├── sol-1.py
    │   ├── analisis.py        comparación FB vs A*, experimentos
    │   ├── ejemplo.in / ejemplo.out
    │   └── vertices.csv, edges.csv
    └── parte-2/
        ├── estado.py  abierta.py  cerrada.py
        ├── horarios.py        carga de vuelos, aritmética de tiempo
        ├── busqueda.py        coste uniforme dependiente del tiempo
        ├── sol-2.py
        ├── analisis.py
        ├── ejemplo.in / ejemplo.out
        └── vertices.csv, edges.csv
tests/                         verificación independiente (no se entrega)
```

---

## 5. Fases de trabajo y asignación de modelo

Criterio: **modelo caro donde un error de lógica cuesta la nota; modelo barato donde el resultado se comprueba solo** (o pasa, o no pasa). Cada subagente arranca sin contexto, así que solo se delega lo que se puede describir en un encargo corto y autocontenido.

| Fase | Tarea | Modelo | Por qué |
|------|-------|--------|---------|
| 0 | Leer enunciado, analizar datos, este plan | Fable | Decide todo lo demás. |
| 1 | Modelo formal y código de búsqueda de ambas partes | Fable | Lógica crítica (optimalidad, consistencia, dominancia). Es poco código; delegarlo costaría más que escribirlo. |
| 2 | **Verificador independiente**: reimplementar el óptimo con otro algoritmo (Bellman-Ford) sin mirar nuestro código y comparar cientos de casos | Sonnet | Tarea mecánica y autocontenida; al no ver nuestro código no hereda nuestros errores. |
| 3 | Pruebas de interfaz: rutas, argumentos, casos límite, formato | Haiku | Ejecutar comandos y comparar salidas. |
| 4 | Experimentos y tablas de la parte 3 | Script + Fable | El script mide; interpretar exige criterio. |
| 5 | PROCESO.md y MEMORIA.md | Fable | Explicación y argumentación. |
| 6 | Word con el formato de la plantilla, PDF y zip | Sonnet | Conversión de formato, tras revisar el md. |

---

## 6. Estrategia de verificación

1. **Optimalidad** (G7): A\* = Dijkstra = Bellman-Ford independiente en todos los casos probados.
2. **Consistencia de h**: comprobar en todas las aristas y varias metas que `h(a) ≤ c(a,b) + h(b)`.
3. **Parte 2**: comparar con un verificador independiente por relajación; comprobar en cada solución que los vuelos existen, encadenan y respetan la holgura.
4. **Interfaz**: las cuatro formas de invocación del enunciado, desde otro directorio, y casos límite.
5. **Python 3.12**: no usar nada posterior (la máquina local tiene 3.13).

---

## 7. Lista de comprobación antes de entregar

- [ ] G1–G9, P1.x, P2.x verificados (ver resultados en PROCESO.md §7).
- [ ] `sol-1.py` y `sol-2.py` con permiso de ejecución y `#!/usr/bin/env python3`.
- [ ] Memoria ≤ 15 hojas, sin código, nombre `550260-522170.pdf`.
- [ ] `autores.txt` en UTF-8.
- [ ] El zip descomprime en `p2-550260-522170/`, sin `__pycache__` ni `.DS_Store`.
- [ ] **Revisión humana**: ambos autores pueden explicar el modelo y el código (lo exige el enunciado).
- [ ] Dudas abiertas resueltas con el profesor (§8).

---

## 8. Dudas abiertas para confirmar con el profesor

1. ¿La holgura se aplica también antes del primer vuelo? (Asumido: no.)
2. ¿Formato de la parte 2 con o sin nombre de aerolínea? (Asumido: solo *callsign*.)
3. ¿Qué imprimir si no hay solución? (Asumido: `No existe solucion`.)
4. ¿Hay que incluir los CSV en el zip? (Asumido: sí, en cada parte, para que funcione tal cual.)
