# Proceso de realización — Práctica 2: Búsqueda

Este documento explica **paso a paso qué se hizo y por qué**, con el razonamiento escrito de forma que una persona pueda seguirlo y detectar un fallo de lógica si lo hubiera. Cada apartado termina con un bloque **«Dónde podría estar el error»** que señala qué revisar.

Documentos relacionados: [PLAN.md](PLAN.md) (requisitos y fases) y [MEMORIA.md](MEMORIA.md) (texto a entregar).

---

## 0. Idea general en cuatro frases

1. Tenemos un mapa de aeropuertos unidos por vuelos.
2. **Parte 1**: buscar el camino con menos kilómetros, sin mirar horarios.
3. **Parte 2**: buscar el camino que llega antes, mirando horarios y dejando un margen entre vuelo y vuelo.
4. Las dos partes usan la misma receta: *tengo una lista de sitios pendientes de explorar (abierta), saco siempre el más prometedor, anoto que ya lo he visitado (cerrada) y añado a la lista los sitios a los que puedo ir desde él*.

---

## 1. Paso 1 — Mirar los datos antes de diseñar

Antes de escribir código se pasó un script de inspección sobre los CSV. Lo que salió y **qué decisión provocó**:

| Hecho observado | Consecuencia en el diseño |
|---|---|
| 881 aeropuertos, 26.495 vuelos, 9.870 pares distintos | El problema es pequeño: cualquier algoritmo correcto lo resuelve en milisegundos. La prioridad es la **corrección**, no exprimir velocidad. |
| Todos los vuelos de un mismo par tienen la misma distancia | En la parte 1 basta un arco por par (grafo simple). |
| 712 vuelos salen y llegan al mismo aeropuerto | Se descartan al cargar: no cambian de sitio. |
| `haversine_km` está redondeado a 3 decimales (±0,0005 km respecto a las coordenadas) | La heurística necesita un factor corrector (§3.3). **Este es el punto más delicado de la práctica.** |
| 173 aeropuertos sin salidas, 96 sin llegadas | Hay casos sin solución: hay que tratarlos. |
| Las horas llevan segundos; el enunciado muestra `10:36` para `10:36:53` | Se calcula en segundos y se **trunca** al imprimir. |
| El ejemplo del enunciado da 1880,56 km con tramos de 41,7 y 32,9 km, que no existen en los datos (son 350,333 y 302,272) | El ejemplo es ilustrativo. Nuestra salida para MAD→BTS es **1860,33 km por MAD - TLS - BTS**, que es más corta que la ruta del ejemplo calculada con datos reales (2.458,57 km). |

> **Dónde podría estar el error.** Si el profesor evalúa con *otros* CSV, el factor corrector se recalcula solo al cargar; nada está escrito a mano con valores de estos datos.

---

## 2. Paso 2 — Las tres estructuras pedidas

El enunciado exige tres ficheros: `estado`, `abierta` y `cerrada`.

### 2.1 `estado.py`

Contiene dos clases, y es importante no confundirlas:

- **Estado**: *dónde estoy*. En la parte 1 es el aeropuerto. En la parte 2 es el aeropuerto **y** la hora.
- **Nodo**: *cómo he llegado hasta aquí*. Guarda el estado, el coste acumulado `g`, y un puntero al nodo anterior (`padre`). Siguiendo los punteros hacia atrás se reconstruye la ruta.

### 2.2 `abierta.py` — montículo binario indexado

La lista abierta tiene que responder rápido a «dame el nodo más barato». Se implementa a mano un **montículo binario** (un vector que se comporta como un árbol donde cada padre es menor que sus hijos):

- `insertar` añade al final y hace «flotar» el nodo hacia arriba.
- `extraer_minimo` saca la raíz, pone el último en su lugar y lo «hunde».
- Las dos cuestan O(log n).

Además lleva un diccionario `estado → posición en el vector`. Sirve para que, si encuentro un camino **mejor** a un aeropuerto que ya estaba en abierta, pueda **sustituir** el nodo viejo en vez de meter un duplicado. Resultado: abierta tiene como mucho un nodo por aeropuerto.

No se usa `heapq` porque el enunciado pide implementar las estructuras nativamente.

### 2.3 `cerrada.py` — tabla hash

Diccionario `estado → nodo`. La pregunta «¿ya he expandido este aeropuerto?» se hace una vez por cada sucesor generado, así que debe ser O(1).

> **Dónde podría estar el error.** En `_flotar` y `_hundir` hay que actualizar el diccionario de posiciones cada vez que se mueve un nodo. Si se olvidara en algún sitio, `insertar` sustituiría el nodo equivocado. El verificador independiente (§6) lo detectaría como una distancia no óptima; no ha detectado ninguna.

---

## 3. Paso 3 — Parte 1: distancia mínima

### 3.1 El modelo, en palabras

- **Estado**: el aeropuerto donde estoy.
- **Estado inicial**: el aeropuerto de origen. **Meta**: estar en el de destino.
- **Operador `volar(a, b)`**:
  - *Precondición*: estoy en `a` y existe algún vuelo `a → b` en `edges.csv`.
  - *Postcondición*: estoy en `b`.
  - *Coste*: la distancia Haversine entre `a` y `b` (columna `haversine_km`).
- **Qué se minimiza**: la suma de costes de los operadores aplicados.

¿Por qué el estado es solo el aeropuerto? Porque lo que puedo hacer desde un aeropuerto no depende de cómo llegué. Si metiera más cosas en el estado (la ruta seguida, por ejemplo), dos formas de llegar a Viena serían estados distintos y se repetiría trabajo.

### 3.2 Los costes se guardan en metros enteros

`350.333 km` se guarda como `350333`. Motivo: los números con decimales en un ordenador no suman de forma exacta (`0.1 + 0.2 ≠ 0.3`). Con enteros, dos rutas que miden lo mismo dan *exactamente* el mismo número, y las comparaciones «¿es más corto?» nunca fallan por un redondeo. Solo al imprimir se divide entre 1000.

### 3.3 La heurística (el punto que más hay que entender)

**Idea.** A\* ordena la lista abierta por `f = g + h`, donde `g` es lo que llevo recorrido y `h` es una **estimación de lo que me falta**. La estimación natural es la distancia en línea recta (Haversine) desde donde estoy hasta el destino.

**Por qué funciona.** Para que A\* dé la solución óptima, `h` no puede exagerar: nunca puede decir «te faltan 500 km» si en realidad se puede llegar en 480. La línea recta es el camino más corto posible entre dos puntos de la esfera, así que ninguna combinación de vuelos puede medir menos. Eso se llama ser **admisible**.

Hay una propiedad más fuerte, ser **consistente**: para cada vuelo `a → b`,

```
h(a) ≤ coste(a, b) + h(b)
```

«Lo que estimo desde `a` no puede superar lo que cuesta ir a `b` más lo que estimo desde `b`.» Si se cumple, cada aeropuerto se expande una sola vez y nunca hay que reabrirlo. La línea recta la cumple por la desigualdad triangular.

**El problema que encontramos.** Los costes del CSV están redondeados a 3 decimales. Un vuelo cuya distancia real es 17,7924 km aparece como 17,792. Entonces la línea recta (17,7924) es **mayor** que el coste del vuelo (17,792): la heurística exagera por 0,4 metros. Es una violación minúscula, pero rompe la garantía matemática de optimalidad.

**La solución.** Se multiplica la línea recta por un factor ρ ligeramente menor que 1:

```
h(n) = ρ · línea_recta(n, destino)
ρ = el menor valor de  coste_csv(a,b) / línea_recta(a,b)  entre todos los vuelos
```

Con estos datos sale **ρ = 0,999975** (lo fija el vuelo LGA→TEB, de solo 17,8 km). 

**Demostración de que ahora sí es consistente**, para cualquier vuelo `a → b` con destino final `m`:

```
h(a) − h(b) = ρ · ( recta(a,m) − recta(b,m) )
            ≤ ρ · recta(a,b)          ← desigualdad triangular
            ≤ coste_csv(a,b)          ← por cómo se ha definido ρ
```

Y `h(destino) = 0`. Consistente ⇒ admisible ⇒ A\* óptimo.

El precio es despreciable: la heurística pierde un 0,0025 % de precisión.

**Comprobación empírica.** `analisis.py` recorre todos los arcos para 20 metas y mide la mayor violación de la desigualdad: sale **−0,000018 m** (negativa = se cumple en todos).

> **Dónde podría estar el error.**
> - Si alguien quitara el factor ρ, el programa seguiría dando resultados correctos en casi todos los casos, pero ya no estaría garantizado. No es un fallo que se vea probando.
> - El radio terrestre usado (6371,0088 km) es el que indica `README.md`. Si se usara otro (p. ej. 6371), ρ lo compensaría automáticamente porque se calcula a partir de los datos.

### 3.4 Los dos algoritmos son el mismo bucle

```
meter el origen en abierta
mientras abierta no esté vacía:
    sacar el nodo de menor f
    si es el destino → terminado, es óptimo
    meterlo en cerrada
    para cada aeropuerto vecino:
        si ya está en cerrada → ignorar
        si no → insertar en abierta (o mejorar el que hubiera)
si abierta se vacía → no existe solución
```

- **Fuerza bruta** = este bucle con `h = 0`. Es la búsqueda de coste uniforme (Dijkstra). Explora en círculos crecientes alrededor del origen, sin saber hacia dónde está el destino.
- **A\*** = este bucle con la `h` del §3.3. Explora preferentemente en dirección al destino.

Dos detalles que suelen ser fuente de errores y están cuidados:

1. **La prueba de meta se hace al sacar el nodo de abierta, no al generarlo.** Si se parase en cuanto *aparece* el destino como vecino, se podría devolver una ruta peor que otra que aún está en la lista.
2. **Desempate**: a igual `f` se prefiere menor `h` (más cerca del destino). No afecta al resultado, solo reduce expansiones.

> **Dónde podría estar el error.** `sol-1.py` ejecuta A\*. Si A\* y la fuerza bruta discreparan alguna vez, sería síntoma de heurística inconsistente. `analisis.py` los compara: 0 discrepancias en 500 casos.

---

## 4. Paso 4 — Parte 2: tiempo mínimo

### 4.1 El modelo, en palabras

- **Estado**: `(aeropuerto, instante)`. Ahora la hora sí importa: a las 08:00 puedo coger vuelos que a las 20:00 ya han salido.
- **Tiempo**: segundos enteros desde las 00:00 UTC del día en que empieza el viaje («día 0»). El instante 90.000 son las 01:00 del día 1.
- **Estado inicial**: `(origen, hora de inicio)`. **Meta**: cualquier estado cuyo aeropuerto sea el destino.
- **Operador `tomar(v)`** para un vuelo `v` de `a` a `b`:
  - *Precondición*: estoy en `a`. (Siempre se puede aplicar: si el vuelo de hoy ya salió, se toma el de mañana.)
  - *Efecto*: calculo `disponible = instante + holgura` (o solo `instante` si es el primer vuelo). Tomo la **primera salida diaria** de `v` que no sea anterior a `disponible`. Paso a `(b, salida + duración)`.
  - *Coste*: `llegada − instante`, es decir, espera más vuelo.
- **Qué se minimiza**: la suma de costes = hora de llegada al destino − hora de inicio.

### 4.2 Cómo se calcula «la primera salida diaria»

Un vuelo que sale a las 08:13:47 despega en los instantes `29.627`, `29.627 + 86.400`, `29.627 + 2·86.400`… Si estoy disponible en el instante `d`:

```
días = techo( (d − hora_salida) / 86400 ),  como mínimo 0
salida = hora_salida + días · 86400
```

Ejemplo: disponible a las 09:00 (32.400). `(32400 − 29627)/86400 = 0,03` → techo 1 → sale mañana a las 08:13:47.
Ejemplo: disponible a las 07:00 (25.200). Resultado negativo → 0 días → sale hoy.

### 4.3 La holgura

El enunciado dice «en cada **conexión** debe haber al menos…». Una conexión es el paso de un vuelo a otro, así que:

- Primer vuelo: basta con que salga a la hora de inicio o después.
- Resto: debe salir al menos `holgura` minutos después de aterrizar el anterior.

Está aislado en una constante (`HOLGURA_EN_PRIMER_VUELO = False` en `busqueda.py`).

> **Dónde podría estar el error.** Es una **interpretación**. Si el profesor entiende que también hay que esperar la holgura antes del primer vuelo, hay que poner la constante a `True`. Preguntarlo.

### 4.4 La poda por dominancia (por qué basta un nodo por aeropuerto)

Si se tomara el estado `(aeropuerto, instante)` al pie de la letra, habría miles de estados por aeropuerto (uno por cada hora de llegada posible). No hace falta, por este argumento:

> Si puedo estar en Viena a las 10:00 o a las 11:00, **la opción de las 10:00 nunca es peor**: quien llega a las 10:00 puede sentarse a esperar hasta las 11:00 y hacer exactamente lo mismo que el otro. Todo vuelo que pueda coger el de las 11:00 también lo puede coger el de las 10:00.

Por tanto, de todos los nodos de un mismo aeropuerto solo interesa el de llegada más temprana. En el código esto se consigue haciendo que `Estado.clave()` devuelva solo el aeropuerto: abierta y cerrada guardan un nodo por aeropuerto, el mejor.

¿Y la holgura no lo estropea? No: la holgura se aplica igual a todos los que llegan en vuelo, así que no cambia quién va por delante. El único caso especial es el nodo inicial (sin holgura), que es además el más temprano posible en el origen.

> **Dónde podría estar el error.** Este argumento depende de que **esperar sea gratis y siempre posible**. Si el problema tuviera, por ejemplo, un tiempo *máximo* de conexión, llegar antes podría ser peor y la poda dejaría de ser válida. El enunciado no impone nada así.

### 4.5 Por qué la fuerza bruta es óptima

Es la búsqueda de coste uniforme: se saca siempre el nodo con menor tiempo transcurrido. Como todos los costes son positivos (los vuelos duran al menos 15 minutos), cuando un aeropuerto sale de abierta ningún otro camino puede llegar antes a él: cualquier otro pasaría por un nodo que sigue en abierta con un tiempo ya mayor o igual.

### 4.6 Formato de salida

`MAD - VIE IBE31ZM 08:13 - 10:36`: origen, destino, *callsign*, salida y llegada truncadas al minuto. No se imprime el día: si un vuelo sale al día siguiente, la hora mostrada es la del reloj.

---

## 5. Paso 5 — Los scripts `sol-1.py` y `sol-2.py`

Ambos hacen lo mismo:

1. Comprobar que hay exactamente dos argumentos.
2. Resolver rutas: **un nombre sin carpeta se busca junto al script** (lo dice el enunciado); una ruta con carpeta se respeta tal cual.
3. Leer la entrada ignorando líneas en blanco, espacios y mayúsculas/minúsculas.
4. Cargar `vertices.csv` y `edges.csv` (primero del directorio de trabajo; si no, junto al script).
5. Buscar, imprimir y escribir **el mismo texto** en el fichero.

Casos especiales decididos (el enunciado no los define):

| Situación | Parte 1 | Parte 2 |
|---|---|---|
| No hay ruta | `No existe solucion` | `No existe solucion` |
| Origen = destino | `0.00` y el código | salida vacía (cero vuelos) |
| Entrada inválida o aeropuerto desconocido | error por `stderr`, código 1 | igual |

---

## 6. Paso 6 — Verificación

El enunciado es tajante: una solución no óptima vale como mucho 0,5 puntos. Por eso la verificación se hizo con **tres capas independientes**.

### 6.1 Verificador independiente (caja negra)

Un segundo modelo (Sonnet) escribió `tests/verificar.py` **sin leer nuestro código**, solo con la especificación del problema, usando **algoritmos distintos** (Bellman-Ford en la parte 1; corrección de etiquetas sin cola de prioridad en la parte 2). Así no puede heredar nuestros errores.

| Parte | Casos | Qué se comprueba | Resultado |
|---|---|---|---|
| 1 | 270 | pantalla = fichero; cada tramo existe; la suma coincide con la línea 1; la suma es **exactamente** el óptimo de Bellman-Ford; sin ruta ⇔ mensaje | **270 / 270** |
| 2 | 150 (88 con ruta) | pantalla = fichero; cada vuelo existe en el CSV; el encadenamiento respeta la holgura; la llegada simulada es **exactamente** la óptima, al segundo | **150 / 150** |

Reejecución: `python3 tests/verificar.py` desde `segunda practica/` (≈1 minuto).

### 6.2 Comparación interna fuerza bruta vs A\*

`parte-1/analisis.py`: 500 pares aleatorios, **0 discrepancias**. Además, mayor violación de consistencia = −0,000018 m.

### 6.3 Pruebas de interfaz

Un tercer modelo (Haiku) ejecutó 16 pruebas de línea de comandos por script: las cuatro formas de invocación del enunciado, ejecución desde otro directorio, número de argumentos incorrecto, fichero inexistente, aeropuerto desconocido, minúsculas, líneas en blanco, finales de línea de Windows, horas y holguras mal formadas, permisos de ejecución, cabecera `#!` e importaciones. **Todas superadas**; ninguna traza de Python en los errores; no se importa `heapq` ni ninguna biblioteca externa.

### 6.4 Lo que NO está verificado

- **No se ha ejecutado con Python 3.12** (la máquina tiene 3.13). El código no usa nada posterior a 3.8, pero conviene probarlo en los ordenadores del aula.
- Las interpretaciones del enunciado (holgura inicial, formato con solo *callsign*, mensaje sin solución) no se pueden verificar con pruebas: hay que preguntarlas.

---

## 7. Paso 7 — Experimentos para el análisis

Se generan con `analisis.py` de cada parte (semilla fija 2026, reproducibles). Los números y su interpretación están en [MEMORIA.md](MEMORIA.md) §4. Resumen:

- Parte 1: A\* expande de media **69 nodos frente a 385** de la fuerza bruta (82 % menos) y tarda 0,78 ms frente a 1,92 ms.
- Parte 2: la holgura y la hora de inicio cambian mucho la **duración del viaje** pero casi nada el **esfuerzo de búsqueda** (≈390 expansiones siempre).
- Escalado sintético del núcleo de búsqueda: 1 millón de nodos y 11 millones de arcos en 18 s (fuerza bruta) y 7 s (A\*).

---

## 8. Reparto de trabajo entre modelos

| Trabajo | Modelo | Motivo |
|---|---|---|
| Lectura del enunciado, análisis de datos, diseño, código de búsqueda, documentos | Fable | Lógica donde un error cuesta la nota. |
| Verificador independiente de optimalidad | Sonnet | Tarea autocontenida y mecánica; conviene que no vea nuestro código. |
| Pruebas de interfaz | Haiku | Ejecutar comandos y comparar. |

---

## 9. Qué debe revisar una persona antes de entregar

1. Leer §3.3 y §4.4 hasta poder explicarlos sin mirar: son los dos razonamientos que sostienen la optimalidad.
2. Confirmar con el profesor las cuatro dudas de [PLAN.md](PLAN.md) §8.
3. Ejecutar `./sol-1.py ejemplo.in ejemplo.out` y `./sol-2.py ejemplo.in ejemplo.out` en un ordenador del aula.
4. Decidir si se entregan `analisis.py` y los CSV dentro del zip (están permitidos como «ficheros adicionales»).
