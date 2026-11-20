<!-- Borrador de la memoria. Se pasará a Word con el formato de la plantilla de la práctica 1.
     Límite: 15 hojas con portada. Sin código fuente. -->

# PORTADA

Universidad Carlos III

**Heurística y Optimización**

Práctica 2: Búsqueda

Curso 2026-27

**Grupo: 01**

**Julio César Ruiz Sánchez** (NIA: 100522170)
**Denis Ángel Sánchez Rybianska** (NIA: 100550260)

---

# 1. Introducción

En esta práctica se resuelven dos problemas de búsqueda sobre una red real de vuelos (881 aeropuertos y 26.495 vuelos observados el 1 de diciembre de 2022). La memoria se organiza así:

- **Parte 1**: ruta de mínima distancia Haversine entre dos aeropuertos, ignorando horarios. Se resuelve con fuerza bruta y con búsqueda heurística.
- **Parte 2**: itinerario de mínimo tiempo de viaje teniendo en cuenta horarios y una holgura mínima en cada conexión. Se resuelve con fuerza bruta.
- **Parte 3**: análisis de resultados: factor de ramificación, infactibilidad, multiplicidad de óptimos, efecto de los parámetros y tamaños resolubles.

Para cada parte se describe primero el modelo como espacio de estados, después el algoritmo y por último las estructuras de datos. Toda la implementación está en Python 3 sin bibliotecas externas; las listas abierta y cerrada se han implementado de forma nativa.

Notación común: *V* es el conjunto de aeropuertos, *o* ∈ *V* el origen y *d* ∈ *V* el destino.

---

# 2. Parte 1: minimización de la distancia recorrida

## 2.1. Datos

- *V*: conjunto de aeropuertos; cada *a* ∈ *V* tiene coordenadas (φₐ, λₐ).
- *A* ⊆ *V* × *V*: conjunto de conexiones. (*a*, *b*) ∈ *A* si en `edges.csv` existe al menos un vuelo de *a* a *b* con *a* ≠ *b*.
- *c*(*a*, *b*) ∈ ℕ: distancia Haversine de la conexión en metros, tomada de la columna `haversine_km`.

Los horarios se ignoran, de modo que el multigrafo de 26.495 vuelos se reduce a un grafo dirigido simple de 9.657 arcos. Se ha comprobado que todos los vuelos de un mismo par tienen la misma distancia, por lo que la reducción no pierde información. Los 712 vuelos con origen igual a destino se descartan: no cambian el estado y nunca forman parte de un camino mínimo.

## 2.2. Espacio de estados

**Estado.** *s* = *a* ∈ *V*, el aeropuerto en el que se encuentra el viajero. El espacio de estados es *S* = *V*, con |*S*| = 881.

Se ha elegido la representación mínima. El conjunto de acciones disponibles y su coste dependen solo del aeropuerto actual y no del camino seguido (propiedad de Markov), así que añadir cualquier otro dato multiplicaría estados equivalentes sin aportar nada.

**Estado inicial.** *s*₀ = *o*.

**Estados meta.** *G* = {*d*}.

**Operador** volar(*a*, *b*):

| | |
|---|---|
| Precondición | *s* = *a* ∧ (*a*, *b*) ∈ *A* |
| Postcondición | *s′* = *b* |
| Coste | *c*(*a*, *b*) > 0 |

**Solución.** Una secuencia de aeropuertos π = ⟨*a*₀, *a*₁, …, *a*ₖ⟩ con *a*₀ = *o*, *a*ₖ = *d* y (*a*ᵢ₋₁, *a*ᵢ) ∈ *A* para todo *i*.

**Métrica a optimizar.**

  mín *z*(π) = Σᵢ₌₁..ₖ *c*(*a*ᵢ₋₁, *a*ᵢ)

## 2.3. Decisiones de modelado

- **Costes en metros enteros.** `haversine_km` tiene tres decimales, luego *c* = 1000 · km es un entero exacto. Con ello *g* se calcula sin error de coma flotante y las comparaciones entre caminos son exactas. El resultado se divide entre 1000 únicamente al mostrarlo.
- **Coste tomado del fichero y no recalculado.** El dato oficial del problema es la columna `haversine_km`; las coordenadas se usan solo para la heurística.

## 2.4. Algoritmo de fuerza bruta

Se usa la **búsqueda de coste uniforme** (Dijkstra): se expande siempre el nodo de menor coste acumulado *g*(*n*). Es no informada —no utiliza la posición del destino— y es completa y óptima porque todos los costes son estrictamente positivos. La prueba de meta se realiza al extraer el nodo de la lista abierta y no al generarlo; de lo contrario podría devolverse un camino que no es el mínimo.

## 2.5. Algoritmo heurístico: A\*

A\* expande el nodo de menor *f*(*n*) = *g*(*n*) + *h*(*n*). Ambos algoritmos comparten la misma implementación: la fuerza bruta es A\* con *h* ≡ 0.

### Heurística

Sea δ(*a*, *b*) la distancia Haversine entre dos aeropuertos calculada con sus coordenadas y el radio medio terrestre *R* = 6371,0088 km:

  δ(*a*, *b*) = 2*R* · arcsen √( sen²(Δφ/2) + cos φₐ · cos φ_b · sen²(Δλ/2) )

La heurística propuesta es

  ***h*(*n*) = ρ · δ(*n*, *d*)**,  con  ρ = mín( 1, mín₍ₐ,_b₎∈*A* *c*(*a*, *b*) / δ(*a*, *b*) )

**Justificación de δ.** La distancia ortodrómica es la longitud del camino más corto entre dos puntos de la esfera; ninguna sucesión de vuelos puede sumar menos. Procede de relajar el problema eliminando la restricción de que solo existen ciertas conexiones.

**Justificación de ρ.** Los costes del fichero están redondeados a tres decimales, así que *c*(*a*, *b*) puede ser hasta 0,5 m inferior a δ(*a*, *b*). Sin corrección, δ podría sobrestimar el coste real y se perdería la garantía de optimalidad. El factor ρ se calcula una sola vez al cargar los datos, en *O*(|*A*|). Con los datos de la práctica ρ = 0,999975, determinado por la conexión más corta de la red (LGA → TEB, 17,8 km).

**Consistencia.** Para todo (*a*, *b*) ∈ *A*:

  *h*(*a*) − *h*(*b*) = ρ · (δ(*a*, *d*) − δ(*b*, *d*)) ≤ ρ · δ(*a*, *b*) ≤ *c*(*a*, *b*)

La primera desigualdad es la triangular sobre la esfera y la segunda la definición de ρ. Además *h*(*d*) = 0. Por tanto *h* es **consistente**, y en consecuencia **admisible**. De ello se sigue que A\* es óptimo y que cuando un nodo se extrae de la lista abierta su *g* ya es mínimo: **ningún estado cerrado necesita reabrirse**.

Se ha comprobado empíricamente recorriendo todos los arcos para 20 metas: la mayor violación de la desigualdad es −1,8·10⁻⁵ m, es decir, se cumple siempre.

**Desempate.** A igualdad de *f* se extrae antes el nodo de menor *h*, que es el más cercano a la meta. No altera el coste de la solución; reduce expansiones entre nodos con la misma *f*.

## 2.6. Estructuras de datos

| Elemento | Estructura | Operaciones y coste | Justificación |
|---|---|---|---|
| Estado | Objeto con el código IATA | — | Representación mínima. |
| Nodo | Estado, *g*, *h*, puntero al padre | Reconstrucción del camino *O*(*k*) | El puntero al padre evita almacenar el camino completo en cada nodo. |
| Lista abierta | **Montículo binario indexado** (vector + tabla de posiciones) | Insertar, extraer mínimo y mejorar clave: *O*(log *n*). Pertenencia: *O*(1) | La operación crítica es extraer el mínimo. La tabla de posiciones permite sustituir un nodo cuando se halla un camino mejor al mismo estado, de modo que la lista contiene como máximo un nodo por estado (≤ \|*V*\|). |
| Lista cerrada | **Tabla hash** estado → nodo | Insertar y consultar: *O*(1) medio | La consulta de pertenencia se ejecuta una vez por sucesor generado. |
| Grafo | Lista de adyacencia: tabla hash aeropuerto → vector de (vecino, coste) | Generar sucesores: *O*(grado) | El grafo es disperso (11 arcos de media por aeropuerto frente a 880 posibles). |

Complejidad total: *O*((|*V*| + |*A*|) · log |*V*|) en tiempo y *O*(|*V*|) en memoria para ambos algoritmos en el peor caso.

---

# 3. Parte 2: minimización del tiempo de viaje

## 3.1. Datos

- *V*: aeropuertos. *F*: conjunto de vuelos diarios (25.783 tras descartar los 712 con origen igual a destino).
- Para cada vuelo *v* ∈ *F*: origen or(*v*), destino de(*v*), hora de salida dentro del día σ(*v*) ∈ [0, *D*) y duración τ(*v*) > 0.
- *D* = 86.400 s es la duración de un día.
- Parámetros de entrada: *o*, *d*, la hora de inicio *t*₀ y la holgura mínima *H* ≥ 0.

**Tiempo.** Todas las magnitudes temporales son **segundos enteros** contados desde las 00:00 UTC del día en que empieza el viaje. Los datos tienen precisión de segundos y se conserva íntegra; solo al mostrar el resultado se trunca al minuto, como hace el ejemplo del enunciado.

**Repetición diaria.** El vuelo *v* despega en los instantes σ(*v*) + *j* · *D*, con *j* = 0, 1, 2, … La duración τ(*v*) puede hacer que aterrice al día siguiente (ocurre en 3.161 vuelos).

## 3.2. Espacio de estados

**Estado.** *s* = (*a*, *t*) con *a* ∈ *V* y *t* ∈ ℕ: el viajero está en el aeropuerto *a* y ha llegado a él en el instante *t*.

El aeropuerto ya no basta: los vuelos que pueden tomarse y la espera necesaria dependen de la hora. El espacio de estados es infinito en principio, pero solo son alcanzables los estados cuya *t* es la hora de llegada de algún vuelo.

**Estado inicial.** *s*₀ = (*o*, *t*₀).

**Estados meta.** *G* = {(*d*, *t*) : *t* ≥ *t*₀}.

**Operador** tomar(*v*), aplicado en *s* = (*a*, *t*):

| | |
|---|---|
| Precondición | or(*v*) = *a* |
| Instante disponible | *e* = *t* si *s* = *s*₀;  *e* = *t* + *H* en otro caso |
| Salida efectiva | sal(*v*, *e*) = σ(*v*) + *D* · máx(0, ⌈(*e* − σ(*v*)) / *D*⌉) |
| Postcondición | *s′* = (de(*v*), sal(*v*, *e*) + τ(*v*)) |
| Coste | *c* = sal(*v*, *e*) + τ(*v*) − *t* |

sal(*v*, *e*) es la primera salida diaria de *v* no anterior a *e*. El coste es la suma de la espera en tierra y la duración del vuelo, y siempre es positivo.

**Métrica a optimizar.** Para un itinerario π = ⟨*v*₁, …, *v*ₖ⟩ que termina en (*d*, *t*ₖ):

  mín *z*(π) = Σᵢ *c*ᵢ = *t*ₖ − *t*₀

Es decir, minimizar el tiempo total de viaje equivale a minimizar la hora de llegada al destino.

## 3.3. Decisiones de modelado

- **El operador siempre es aplicable.** Como los horarios se repiten cada día, si la salida de hoy no es alcanzable se toma la de mañana. La restricción horaria no está en la precondición sino en el cálculo de la salida efectiva y, por tanto, en el coste.
- **Se toma siempre la primera salida válida.** Tomar una salida posterior del mismo vuelo llega más tarde al mismo aeropuerto y está dominado (véase 3.4), así que no se genera.
- **Holgura solo en las conexiones.** El enunciado la exige «en cada conexión». El primer vuelo no es una conexión, por lo que puede tomarse desde el mismo instante *t*₀; los siguientes deben despegar al menos *H* después del aterrizaje anterior.
- **Esperar no es un operador.** Queda implícito en el coste de tomar(*v*). Añadir un operador «esperar» introduciría infinitos estados intermedios inútiles.

## 3.4. Poda por dominancia

**Propiedad.** Sean (*a*, *t*₁) y (*a*, *t*₂) dos estados no iniciales con *t*₁ ≤ *t*₂. Para cualquier vuelo *v* que salga de *a*, sal(*v*, *t*₁ + *H*) ≤ sal(*v*, *t*₂ + *H*), porque sal es no decreciente en su segundo argumento. Luego el sucesor obtenido desde (*a*, *t*₁) llega a de(*v*) no más tarde que el obtenido desde (*a*, *t*₂). Por inducción, todo itinerario realizable desde (*a*, *t*₂) lo es desde (*a*, *t*₁) con llegada igual o anterior.

**Consecuencia.** De todos los estados de un mismo aeropuerto solo interesa el de menor *t*. Las listas abierta y cerrada se indexan por aeropuerto y conservan un único nodo por cada uno. El número de estados efectivamente explorados queda acotado por |*V*| = 881.

La propiedad se apoya en que esperar es gratuito y siempre posible; no se cumpliría si existiera un tiempo máximo de conexión. El estado inicial es el único sin holgura y es además el de menor instante en el origen, por lo que no rompe el argumento.

## 3.5. Algoritmo de fuerza bruta

Búsqueda de coste uniforme sobre *g*(*n*) = *t* − *t*₀. Se expande siempre el nodo con menor tiempo transcurrido y, para cada vuelo que sale de su aeropuerto, se genera el sucesor correspondiente. Como todos los costes son positivos, el primer nodo del aeropuerto destino que se extrae de la lista abierta corresponde a la llegada más temprana posible. Si la lista abierta se vacía, no existe itinerario.

## 3.6. Estructuras de datos

Las listas abierta (montículo binario indexado) y cerrada (tabla hash) son las de la parte 1, con las mismas justificaciones; cambia la clave de ordenación (*g* en lugar de *f*) y el nodo almacena además el vuelo tomado y su instante de salida para poder mostrar el itinerario. Los vuelos se guardan en una tabla hash aeropuerto → vector de vuelos salientes, de modo que generar los sucesores de un nodo cuesta *O*(vuelos salientes). El cálculo de la salida efectiva es aritmética entera en *O*(1), sin recorrer días.

Complejidad: *O*((|*V*| + |*F*|) · log |*V*|) en tiempo y *O*(|*V*|) en memoria.

---

# 4. Análisis de resultados

Las medidas se han obtenido con un script propio que ejecuta los algoritmos sobre casos aleatorios con semilla fija, por lo que son reproducibles. Los tiempos excluyen la carga de los ficheros (≈ 70 ms), que es la misma para todos los casos.

**Validación.** La optimalidad se ha contrastado con un verificador independiente basado en algoritmos distintos (Bellman-Ford y corrección de etiquetas): 270 casos de la parte 1 y 150 de la parte 2 coinciden exactamente con el óptimo de referencia. Además, A\* y fuerza bruta devuelven el mismo coste en los 500 casos de la tabla 1.

## 4.1. Parte 1: fuerza bruta frente a A\*

**Tabla 1.** 500 pares origen–destino aleatorios; 321 con solución. Medias por número de vuelos de la solución óptima.

| Vuelos | Casos | Expandidos FB | Expandidos A\* | Ahorro | Ramif. FB | Ramif. A\* | *b*\* FB | *b*\* A\* | ms FB | ms A\* |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5 | 90,0 | 1,0 | 98,9 % | 22,76 | 30,00 | 90,00 | 1,00 | 0,61 | 0,03 |
| 2 | 46 | 194,4 | 17,8 | 90,8 % | 17,49 | 41,68 | 12,40 | 2,69 | 1,08 | 0,29 |
| 3 | 96 | 346,3 | 45,2 | 86,9 % | 15,92 | 30,98 | 6,33 | 2,57 | 1,77 | 0,61 |
| 4 | 100 | 428,0 | 77,4 | 81,9 % | 15,10 | 25,58 | 4,10 | 2,25 | 2,08 | 0,87 |
| 5 | 54 | 505,5 | 111,5 | 77,9 % | 14,18 | 23,31 | 3,19 | 1,98 | 2,47 | 1,11 |
| 6 | 17 | 537,2 | 139,7 | 74,0 % | 13,66 | 20,41 | 2,61 | 1,90 | 2,54 | 1,41 |
| 7 | 2 | 608,0 | 379,0 | 37,7 % | 13,82 | 16,27 | 2,30 | 2,13 | 2,77 | 3,16 |
| 8 | 1 | 377,0 | 108,0 | 71,4 % | 15,32 | 20,78 | 1,92 | 1,59 | 1,98 | 1,40 |
| **Todos** | **321** | **384,6** | **69,1** | **82,0 %** | **15,57** | **28,84** | **7,04** | **2,32** | **1,92** | **0,78** |

*Ramif.*: sucesores generados por nodo expandido. *b*\*: factor de ramificación efectivo, solución de 1 + *b* + … + *b*ᵏ = *N* + 1 con *N* nodos expandidos y *k* vuelos.

**Factor de ramificación.** El grafo tiene 10,96 arcos salientes de media por aeropuerto y un máximo de 140 (AMS). El factor observado es mayor que la media del grafo en ambos algoritmos (15,6 y 28,8) porque los nodos que se expanden no son una muestra uniforme: los aeropuertos mejor conectados se alcanzan antes y se expanden con más frecuencia. El efecto es más acusado en A\*, que expande pocos nodos y casi todos son *hubs* situados en la dirección del destino. Que A\* tenga una ramificación bruta mayor no significa que trabaje más; la medida relevante es *b*\*, que pasa de **7,04 a 2,32**: la heurística convierte un árbol ancho en uno casi lineal.

**Efecto de la heurística.** A\* expande de media un 82 % menos de nodos y tarda un 59 % menos. El ahorro en tiempo es menor que el ahorro en nodos porque cada nodo generado por A\* requiere evaluar la fórmula de Haversine (seis funciones trigonométricas), mientras que en la fuerza bruta *h* es constante.

**Dependencia con la longitud de la solución.** El ahorro disminuye al crecer el número de vuelos: 98,9 % con un vuelo y alrededor del 75 % con seis. Dos razones: en rutas largas el destino suele ser un aeropuerto periférico al que solo se llega dando rodeos, de modo que la línea recta subestima mucho el coste real; y la fuerza bruta está acotada por el tamaño del grafo (como máximo 881 expansiones), por lo que su desventaja no puede seguir creciendo.

**Caso desfavorable.** En las dos soluciones de siete vuelos A\* expande menos nodos pero tarda más (3,16 ms frente a 2,77 ms). Cuando la heurística orienta poco, su coste de evaluación deja de compensar.

**Ejemplo.** MAD → SYD (17.692,73 km por MAD - DXB - SYD): la fuerza bruta expande 719 de los 744 aeropuertos alcanzables desde Madrid, porque Sídney es de los más lejanos; A\* expande 13.

## 4.2. Parte 2

**Tabla 2.** 300 pares aleatorios, hora de inicio 00:00; 196 con solución en todas las configuraciones.

| Holgura (min) | Duración media (h) | Vuelos | Expandidos | Generados | Ramif. | ms |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 29,31 | 4,48 | 401,1 | 19.068 | 58,12 | 5,11 |
| 30 | 31,11 | 4,19 | 400,9 | 19.366 | 58,95 | 5,19 |
| 60 | 32,63 | 4,04 | 396,9 | 19.364 | 59,32 | 5,75 |
| 120 | 35,60 | 3,89 | 388,6 | 19.324 | 60,23 | 5,10 |
| 240 | 41,46 | 3,67 | 381,0 | 19.265 | 62,26 | 5,94 |
| 480 | 52,99 | 3,55 | 386,6 | 19.682 | 62,96 | 5,41 |
| 1440 | 87,77 | 3,28 | 393,2 | 20.055 | 63,42 | 5,56 |

**Tabla 3.** Mismos pares, holgura de 60 minutos.

| Hora de inicio | Duración media (h) | Vuelos | Expandidos | Ramif. |
|---:|---:|---:|---:|---:|
| 00:00 | 32,63 | 4,04 | 396,9 | 59,32 |
| 06:00 | 30,31 | 4,06 | 379,2 | 63,13 |
| 12:00 | 30,25 | 4,09 | 384,3 | 62,27 |
| 18:00 | 31,64 | 4,01 | 390,1 | 60,27 |
| 23:00 | 32,31 | 4,01 | 393,8 | 61,18 |

**Factor de ramificación.** Cada aeropuerto tiene de media 29,27 vuelos salientes y un máximo de 546. El factor observado ronda 60 por el mismo sesgo hacia los *hubs* que en la parte 1. Es entre dos y cuatro veces mayor que en la parte 1 porque aquí cada vuelo es un operador distinto, aunque varios unan el mismo par de aeropuertos; la lista abierta se queda solo con el que llega antes a cada destino.

**Los parámetros cambian la solución, no la dificultad.** Al aumentar la holgura de 0 a 1440 minutos la duración media se triplica (de 29,3 a 87,8 horas) y las soluciones usan menos vuelos (de 4,48 a 3,28), porque cada conexión se encarece y compensa volar más directo. Sin embargo, el número de nodos expandidos se mantiene entre 381 y 401 y el tiempo en torno a 5,5 ms. Con la hora de inicio ocurre lo mismo: salir a las 06:00 o a las 12:00 acorta el viaje unas dos horas respecto a medianoche, porque hay más vuelos próximos, pero el esfuerzo no varía.

La explicación está en la poda por dominancia: el número de estados explorados está acotado por el número de aeropuertos, no por el número de instantes posibles. La holgura y la hora de inicio reordenan las llegadas, pero no cambian cuántos aeropuertos hay que cerrar antes de alcanzar el destino.

**Ejemplo.** MAD → BTS con inicio a las 00:00 y 60 minutos de holgura: MAD-FRA (05:32–07:55), FRA-VIE (09:18–10:23), VIE-KSC (12:27–13:04), KSC-BTS (14:13–14:46); 14 h 46 min en total. El enunciado propone un itinerario de tres vuelos con la misma hora de llegada: ambos son óptimos.

## 4.3. Instancias infactibles

Sí existen, y son frecuentes: **el 35,8 %** de los pares aleatorios de la parte 1 (179 de 500) y **el 34,7 %** de los de la parte 2 (104 de 300) no tienen solución. La causa es estructural: 173 aeropuertos no tienen ningún vuelo de salida en los datos y 96 no tienen ninguno de llegada, porque solo se dispone de las observaciones de un día.

En la parte 2 **la holgura y la hora de inicio no generan infactibilidad**: al repetirse los horarios cada día, siempre se puede esperar a la siguiente salida. Lo confirma la tabla 2, donde el número de casos factibles es 196 con cualquier holgura. La factibilidad depende únicamente de la conectividad, y es la misma en ambas partes.

Una instancia infactible es el **peor caso** para la búsqueda: hay que agotar todos los aeropuertos alcanzables antes de concluir que no hay ruta (744 expansiones desde MAD). En este caso A\* no aporta ninguna ventaja sobre la fuerza bruta.

## 4.4. Multiplicidad de soluciones óptimas

**Parte 1.** Es posible pero poco habitual: de 2.973 pares alcanzables analizados, solo **13 (0,44 %)** admiten más de un camino de distancia mínima. Las distancias tienen precisión de metros y es raro que dos rutas distintas sumen exactamente lo mismo.

**Parte 2.** Es mucho más habitual. El tiempo total lo determina la hora de llegada del último vuelo; si este es el único que llega pronto al destino, todos los tramos anteriores admiten alternativas con tal de enlazar a tiempo. En el ejemplo MAD → BTS con holgura 0, el tramo FRA-VIE puede hacerse con el vuelo de las 08:02 o con el de las 09:18, y también vale la ruta directa MAD-VIE del enunciado: todas enlazan con el mismo VIE-KSC de las 12:27 y llegan a las 14:46.

En ambos casos el algoritmo devuelve **una** solución óptima, determinada por el orden de extracción de la lista abierta. El coste devuelto es siempre el óptimo; el recorrido concreto puede no ser único.

## 4.5. Qué influye en el tiempo de resolución y tamaños máximos

Con los datos de la práctica cualquier instancia se resuelve en menos de 10 ms de búsqueda. El tiempo total de ejecución (≈ 80 ms en la parte 1) está dominado por la lectura de `edges.csv`. Los factores que influyen son, por orden de importancia:

1. **El tamaño del grafo** (|*V*| y número de arcos o vuelos), que acota el trabajo en el peor caso.
2. **La lejanía del destino** en la métrica optimizada: la fuerza bruta expande todos los estados más baratos que la solución.
3. **La existencia de solución**: los casos infactibles obligan a la exploración completa.
4. **La calidad de la heurística** (solo parte 1): cuanto más directa es la ruta óptima, más informa la línea recta.
5. **Los parámetros de la parte 2** (hora y holgura) no influyen de forma apreciable.

Para estimar tamaños máximos se ha ejecutado el núcleo de búsqueda de la parte 1 sobre grafos geométricos sintéticos con el mismo grado medio que la red real (11 arcos por nodo):

**Tabla 4.** Escalado sobre grafos sintéticos (media de 3 casos).

| Nodos | Arcos | FB: tiempo | FB: expandidos | A\*: tiempo | A\*: expandidos |
|---:|---:|---:|---:|---:|---:|
| 10.000 | 110.000 | 0,04 s | 5.762 | 0,01 s | 1.235 |
| 100.000 | 1.100.000 | 0,78 s | 63.083 | 0,34 s | 18.465 |
| 1.000.000 | 11.000.000 | 17,91 s | 706.380 | 6,81 s | 161.438 |

El crecimiento es prácticamente lineal con un término logarítmico, como predice la complejidad *O*((|*V*| + |*A*|) log |*V*|). Un grafo mil veces mayor que la red real se resuelve en segundos. El límite práctico lo impone la **memoria** necesaria para almacenar el grafo (varios gigabytes con un millón de nodos en Python), no el tiempo de búsqueda. La parte 2 escala de la misma forma gracias a la poda por dominancia; sin ella, el número de estados crecería con el número de vuelos y no con el de aeropuertos.

---

# 5. Conclusiones

- Los dos problemas se han modelado como espacios de estados con la representación mínima suficiente: el aeropuerto en la parte 1 y el par (aeropuerto, instante) en la parte 2.
- En la parte 1, la distancia en línea recta es una heurística natural, pero el redondeo de los datos la hace ligeramente inconsistente. El factor ρ, calculado a partir de los propios datos, restablece la garantía formal de optimalidad con una pérdida de información del 0,0025 %.
- A\* reduce el factor de ramificación efectivo de 7,04 a 2,32 y expande un 82 % menos de nodos que la fuerza bruta, aunque su ventaja disminuye en rutas largas y desaparece en instancias sin solución.
- En la parte 2, la poda por dominancia acota el espacio explorado por el número de aeropuertos; por eso la holgura y la hora de inicio modifican la solución pero no la dificultad.
- Un tercio de las instancias son infactibles por la conectividad de los datos, y la multiplicidad de óptimos es anecdótica en distancia (0,44 %) pero habitual en tiempo.
