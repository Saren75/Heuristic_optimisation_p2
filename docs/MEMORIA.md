<!-- Borrador de la memoria. Se pasará a Word con el formato de la plantilla de la práctica 1.
     Límite: 15 hojas con portada. Sin código fuente.
     Notación alineada con el temario de la asignatura (búsqueda.pdf y capítulo 5 del libro de ejercicios). -->

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

- **Parte 1**: ruta de mínima distancia Haversine entre dos aeropuertos, ignorando horarios. Se resuelve con un algoritmo de fuerza bruta (Dijkstra) y con uno heurístico (A\*).
- **Parte 2**: itinerario de mínimo tiempo de viaje teniendo en cuenta horarios y una holgura mínima en cada conexión. Se resuelve con Dijkstra.
- **Parte 3**: análisis de resultados: factor de ramificación, infactibilidad, multiplicidad de óptimos, efecto de los parámetros y tamaños resolubles.

Para cada parte se describe el espacio de estados (estados, operadores, estado inicial y meta), sus parámetros (tamaño, factor de ramificación *b* y profundidad *d*), el algoritmo elegido y las estructuras de datos. Toda la implementación está en Python 3 sin bibliotecas externas; las listas ABIERTA y CERRADA se han implementado de forma nativa.

**Notación.** Se sigue la del temario: *g*(*n*) es el coste desde el nodo inicial hasta *n*, *h*(*n*) la estimación heurística hasta la meta y *f*(*n*) = *g*(*n*) + *h*(*n*); *g*\*(*n*), *h*\*(*n*) y *f*\*(*n*) son los valores reales y *C*\* el coste de la solución óptima. *k*(*nᵢ*, *nⱼ*) es el coste del arco entre dos nodos, *b* el factor de ramificación y *d* la profundidad. La red de vuelos se representa con un grafo *G*(*V*, *E*), cuyos vértices son aeropuertos identificados por su código IATA; *origen* y *destino* designan los aeropuertos de la entrada.

---

# 2. Parte 1: minimización de la distancia recorrida

## 2.1. Información estática

Como en las soluciones de la asignatura, la información que no cambia durante la búsqueda se define una sola vez y es accesible desde todos los estados, en lugar de copiarse en cada uno:

- *G*(*V*, *E*): grafo dirigido. Hay un vértice por aeropuerto (|*V*| = 881) y un arco *eᵢⱼ* ∈ *E* si en `edges.csv` existe al menos un vuelo de *vᵢ* a *vⱼ* con *vᵢ* ≠ *vⱼ*. Resultan |*E*| = 9.657 arcos.
- *dist*(*eᵢⱼ*) ∈ ℕ: distancia Haversine del arco en metros, tomada de la columna `haversine_km`.
- (*v.lat*, *v.lon*): coordenadas de cada aeropuerto, usadas solo por la heurística.

Los horarios se ignoran, de modo que los 26.495 vuelos se reducen a un arco por par de aeropuertos; se ha comprobado que todos los vuelos de un mismo par tienen la misma distancia, por lo que la reducción no pierde información. Los 712 vuelos con origen igual a destino se descartan: no cambian el estado y nunca forman parte de un camino mínimo.

## 2.2. Espacio de estados

**Estados.** Un estado *s* tiene un único atributo, *s.iata* ∈ *V*: el aeropuerto en el que se encuentra el viajero. Se ha elegido la representación mínima porque los operadores aplicables y su coste dependen solo del aeropuerto actual y no del camino seguido; añadir cualquier otro dato multiplicaría estados equivalentes sin aportar nada.

**Estado inicial.** *s.iata* = *origen*. **Estado final** (descripción explícita): *s.iata* = *destino*.

**Operadores.**

| Operador | Precondiciones | Postcondiciones | Coste |
|---|---|---|---|
| volar(*vᵢ*, *vⱼ*) | *s.iata* = *vᵢ* ∧ *eᵢⱼ* ∈ *E* | *s′.iata* = *vⱼ* | *k* = *dist*(*eᵢⱼ*) |

**Coste de un nodo y métrica a optimizar.** *g*(*n*) es la suma de los costes *k* de los arcos recorridos desde el nodo inicial. Se minimiza la distancia total:

  *C*\* = mín *g*(*n*), con *n* nodo final

**Tamaño del espacio de estados.** Como mucho |*V*| = 881 estados, uno por aeropuerto. No todos son alcanzables: 173 aeropuertos no tienen ningún vuelo de salida y 96 ninguno de llegada; desde MAD, por ejemplo, se alcanzan 744.

**Factor de ramificación.** Es el grado de salida de cada vértice: *b* = |*E*|/|*V*| = 10,96 de media y 140 como máximo (AMS).

**Profundidad.** La solución es un camino simple, luego *d* ≤ |*V*| − 1. En los experimentos la profundidad de la solución óptima varía entre 1 y 8 (tabla 1).

## 2.3. Decisiones de modelado

- **Costes en metros enteros.** `haversine_km` tiene tres decimales, luego 1000 · km es un entero exacto. Con ello *g*(*n*) se calcula sin error de coma flotante y las comparaciones entre caminos son exactas. El resultado se divide entre 1000 únicamente al mostrarlo.
- **Coste tomado del fichero y no recalculado.** El dato oficial del problema es la columna `haversine_km`; las coordenadas se usan solo para la heurística.
- **Todos los costes son positivos y finitos**: *k* ≥ ε = 17,8 km (la conexión más corta, LGA → TEB), y cada nodo tiene un número finito de sucesores. Son dos de las tres condiciones que exige la admisibilidad de A\*.

## 2.4. Algoritmo de fuerza bruta: Dijkstra

Siguiendo el criterio del temario para elegir un algoritmo de fuerza bruta:

- Los costes son **arbitrarios** (no unitarios), lo que descarta la búsqueda en amplitud.
- **Abundan las transposiciones**: el grafo tiene ciclos y se puede llegar a un mismo aeropuerto por muchos caminos. Eso descarta las estrategias del primero en profundidad (ramificación y acotación en profundidad, profundización iterativa), que no detectan nodos repetidos.

Se elige por tanto **Dijkstra**, el algoritmo del mejor primero con *f*(*n*) = *g*(*n*). Es admisible porque los costes son estrictamente positivos. La prueba de meta se realiza al extraer el nodo de ABIERTA y no al generarlo; de lo contrario podría devolverse un camino que no es el mínimo.

## 2.5. Algoritmo heurístico: A\*

A\* es el mismo algoritmo del mejor primero con *f*(*n*) = *g*(*n*) + *h*(*n*); Dijkstra es el caso extremo *h*(*n*) = 0. Ambos comparten la implementación. Se prefiere A\* a IDA\* por la misma razón de las transposiciones; la desventaja de A\* (memoria exponencial) no es relevante con solo 881 estados.

### Obtención de la heurística por relajación

Se relaja la restricción de que solo se puede volar entre aeropuertos conectados (precondición *eᵢⱼ* ∈ *E* del operador volar). En el problema relajado se vuela directamente al destino y el coste óptimo es la distancia ortodrómica δ entre ambos, calculada con las coordenadas y el radio medio terrestre *R* = 6371,0088 km:

  δ(*vᵢ*, *vⱼ*) = 2*R* · arcsen √( sen²(Δφ/2) + cos φᵢ · cos φⱼ · sen²(Δλ/2) )

La heurística propuesta es

  ***h*(*n*) = ρ · δ(*n.iata*, *destino*)**,  con  ρ = mín( 1, mín₍ᵢ,ⱼ₎ *dist*(*eᵢⱼ*) / δ(*vᵢ*, *vⱼ*) )

**Por qué hace falta ρ.** La relajación garantiza que δ es admisible respecto a las distancias reales. Pero los costes del fichero están redondeados a tres decimales, así que *dist*(*eᵢⱼ*) puede ser hasta 0,5 m **menor** que δ(*vᵢ*, *vⱼ*): sin corrección, la heurística podría superar a *h*\* en un arco directo. El factor ρ se calcula una sola vez al cargar los datos, en *O*(|*E*|). Con los datos de la práctica ρ = 0,999975.

**Monotonía (consistencia).** Para todo arco *eᵢⱼ* ∈ *E*:

  *h*(*nᵢ*) − *h*(*nⱼ*) = ρ · (δ(*vᵢ*, *destino*) − δ(*vⱼ*, *destino*)) ≤ ρ · δ(*vᵢ*, *vⱼ*) ≤ *k*(*nᵢ*, *nⱼ*)

La primera desigualdad es la triangular sobre la esfera y la segunda la definición de ρ. Por tanto *h*(*nᵢ*) ≤ *k*(*nᵢ*, *nⱼ*) + *h*(*nⱼ*): la heurística es **monótona**. Se ha comprobado además empíricamente recorriendo todos los arcos para 20 metas: la mayor violación de la desigualdad es −1,8·10⁻⁵ m, es decir, se cumple siempre.

**Admisibilidad.** Sumando la desigualdad anterior a lo largo de cualquier camino de *n* a la meta, y como *h*(meta) = 0, se obtiene *h*(*n*) ≤ *h*\*(*n*) para todo *n*: la heurística es **admisible**. Junto con los costes ≥ ε > 0 y el número finito de sucesores, A\* es **admisible** (encuentra la solución óptima).

La monotonía aporta algo más: cuando un nodo se extrae de ABIERTA su *g*(*n*) ya es *g*\*(*n*). Por eso, en el procedimiento del mejor primero, un sucesor que ya está en CERRADA se descarta directamente: **nunca hace falta redirigir punteros de nodos cerrados**. Si está en ABIERTA con peor *g*, se sustituye.

**Ejemplo de cálculo.**

| Nodo (*n.iata*) | Destino | δ (km) | *h*(*n*) (km) | *h*\*(*n*) (km) | Camino óptimo |
|---|---|---:|---:|---:|---|
| MAD | BTS | 1.853,040 | 1.852,993 | 1.860,330 | MAD - TLS - BTS |
| MAD | SYD | 17.672,850 | 17.672,410 | 17.692,734 | MAD - DXB - SYD |
| TLS | BTS | 1.323,192 | 1.323,159 | 1.323,192 | TLS - BTS |

En los tres casos *h*(*n*) ≤ *h*\*(*n*). El último muestra la necesidad de ρ: cuando el camino óptimo es un vuelo directo, δ coincide con *h*\* hasta el último decimal y basta el redondeo del fichero para que δ lo supere.

**Información de la heurística.** Como 0 ≤ ρ · δ(*n*) ≤ *h*\*(*n*) para todo *n*, la heurística propuesta está **más informada** que la de Dijkstra (*h* = 0) y, según el temario, debe expandir menos nodos. La tabla 1 lo confirma. Evaluarla cuesta *O*(1) (seis funciones trigonométricas), lo que respeta el equilibrio entre el coste de calcular *h* y el ahorro de búsqueda.

**Desempate.** A igualdad de *f* se extrae antes el nodo de menor *h*, que es el más cercano a la meta. Es un criterio propio: no altera el coste de la solución y reduce expansiones entre nodos con la misma *f*.

## 2.6. Estructuras de datos

| Elemento | Estructura | Operaciones y coste | Justificación |
|---|---|---|---|
| Estado | Objeto con el atributo *iata* | — | Representación mínima. |
| Nodo | Estado, *g*, *h*, puntero al padre | Reconstrucción del camino *O*(*d*) | El puntero al padre evita almacenar el camino completo en cada nodo. |
| ABIERTA | **Montículo binario indexado** (vector + tabla de posiciones) | Insertar, extraer mínimo y mejorar *g*: *O*(log *n*). Pertenencia: *O*(1) | La operación crítica es extraer el mínimo. La tabla de posiciones permite sustituir un nodo cuando se halla un camino mejor al mismo estado, de modo que ABIERTA contiene como máximo un nodo por estado (≤ \|*V*\|). |
| CERRADA | **Tabla hash** estado → nodo | Insertar y consultar: *O*(1) medio | La consulta se ejecuta una vez por sucesor generado para detectar transposiciones. |
| *G*(*V*, *E*) | Lista de adyacencia: tabla hash aeropuerto → vector de (vecino, coste) | Generar sucesores: *O*(*b*) | Información estática compartida. El grafo es disperso (11 arcos de media por vértice frente a 880 posibles). |

**Complejidad.** En un árbol de búsqueda el coste sería *O*(*b*ᵈ). Al detectar transposiciones con CERRADA cada estado se expande como mucho una vez, y el coste queda acotado por el tamaño del espacio de estados: *O*((|*V*| + |*E*|) · log |*V*|) en tiempo y *O*(|*V*|) en memoria, para ambos algoritmos.

---

# 3. Parte 2: minimización del tiempo de viaje

## 3.1. Información estática

- *V*: aeropuertos. *F*: conjunto de vuelos diarios (25.783 tras descartar los 712 con origen igual a destino).
- Cada vuelo *v* ∈ *F* tiene los atributos *v.origen*, *v.destino*, *v.callsign*, *v.salida* ∈ [0, *D*) (hora de despegue dentro del día) y *v.duracion* > 0.
- *D* = 86.400 s es la duración de un día.
- Parámetros de entrada: *origen*, *destino*, la hora de inicio *t*₀ y la holgura mínima *H* ≥ 0.

**Tiempo.** Todas las magnitudes temporales son **segundos enteros** contados desde las 00:00 UTC del día en que empieza el viaje. Los datos tienen precisión de segundos y se conserva íntegra; solo al mostrar el resultado se trunca al minuto, como hace el ejemplo del enunciado.

**Repetición diaria.** El vuelo *v* despega en los instantes *v.salida* + *j* · *D*, con *j* = 0, 1, 2, … Su duración puede hacer que aterrice al día siguiente (ocurre en 3.161 vuelos).

## 3.2. Espacio de estados

**Estados.** Un estado *s* tiene dos atributos: *s.iata* ∈ *V*, el aeropuerto en el que está el viajero, y *s.t* ∈ ℕ, el instante en que llegó a él. El aeropuerto ya no basta: los vuelos que pueden tomarse y la espera necesaria dependen de la hora. Es la misma representación que usa la solución de la asignatura para el problema de devolución de equipajes (ejercicio 20 del capítulo de búsqueda), restringida a un único viajero.

**Estado inicial.** *s.iata* = *origen*, *s.t* = *t*₀. **Estado final** (descripción implícita): *s.iata* = *destino*, con cualquier *s.t*.

**Operadores.** Sea *e*(*s*) el instante a partir del cual se puede embarcar: *e*(*s*) = *s.t* en el estado inicial y *e*(*s*) = *s.t* + *H* en cualquier otro. La primera salida diaria de *v* no anterior a *e* es

  sal(*v*, *e*) = *v.salida* + *D* · máx(0, ⌈(*e* − *v.salida*) / *D*⌉)

| Operador | Precondiciones | Postcondiciones | Coste |
|---|---|---|---|
| tomar(*v*) | *s.iata* = *v.origen* | *s′.iata* = *v.destino* ∧ *s′.t* = sal(*v*, *e*(*s*)) + *v.duracion* | *k* = *s′.t* − *s.t* |

El coste es la suma de la espera en tierra y la duración del vuelo. Como en el ejercicio de equipajes, **depende del estado completo** (de *s.t*) y no solo del operador; siempre es positivo: *k* ≥ ε = 15 min, la duración mínima de un vuelo en los datos.

**Métrica a optimizar.** *g*(*n*) = *n.t* − *t*₀ es el tiempo transcurrido desde el inicio, igual a la suma de los costes de los operadores aplicados. Se minimiza el tiempo total de viaje:

  *C*\* = mín *g*(*n*) = mín *n.t* − *t*₀, con *n* nodo final

Minimizar el tiempo total equivale a minimizar la hora de llegada al destino.

**Tamaño del espacio de estados.** Si *T* es el conjunto de instantes distintos en que se puede llegar a un aeropuerto, el tamaño es |*V*| × |*T*|, como en la solución de la asignatura. En los datos hay 20.767 horas de llegada distintas dentro del día, y cada una se repite en los días sucesivos, de modo que |*T*| ≈ 20.767 × (días del horizonte) + 1. Tras la poda por dominancia (3.4) solo se explora un estado por aeropuerto: como mucho |*V*| = 881.

**Factor de ramificación.** En el modelo de la asignatura, que genera todas las salidas de cada vuelo, *b* sería tan alto como α · |*A*|, con |*A*| destinos alcanzables desde el aeropuerto actual y α llegadas distintas a cada uno. Aquí se genera un sucesor por vuelo diario (solo su primera salida válida), así que *b* es el número de vuelos que salen del aeropuerto: 29,27 de media y 546 como máximo. Equivale a α · |*A*| con |*A*| = 10,96 destinos y α = 2,67 vuelos por destino de media.

**Profundidad.** Por la dominancia nunca se vuelve a un aeropuerto ya cerrado, luego *d* ≤ |*V*| − 1. En los experimentos la solución usa entre 3 y 4,5 vuelos de media (tabla 2).

## 3.3. Decisiones de modelado

- **El operador siempre es aplicable.** Como los horarios se repiten cada día, si la salida de hoy no es alcanzable se toma la de mañana. La restricción horaria no está en la precondición sino en el cálculo de la salida efectiva y, por tanto, en el coste.
- **Se genera solo la primera salida válida de cada vuelo.** Tomar una salida posterior del mismo vuelo llega más tarde al mismo aeropuerto y está dominado (véase 3.4). Es una poda propia respecto al modelo de la asignatura, y es la que reduce *b* de α · |*A*| por día a un sucesor por vuelo.
- **Holgura solo en las conexiones.** El enunciado la exige «en cada conexión». El primer vuelo no es una conexión, por lo que puede tomarse desde el mismo instante *t*₀; los siguientes deben despegar al menos *H* después del aterrizaje anterior.
- **Esperar no es un operador.** Queda implícito en el coste de tomar(*v*). Añadir un operador «esperar» introduciría infinitos estados intermedios inútiles.

## 3.4. Poda por dominancia

**Propiedad.** Sean *s*₁ y *s*₂ dos estados no iniciales del mismo aeropuerto con *s*₁.*t* ≤ *s*₂.*t*. Para cualquier vuelo *v* que salga de él, sal(*v*, *s*₁.*t* + *H*) ≤ sal(*v*, *s*₂.*t* + *H*), porque sal es no decreciente en su segundo argumento. Luego el sucesor de *s*₁ llega a *v.destino* no más tarde que el de *s*₂. Por inducción, todo itinerario realizable desde *s*₂ lo es desde *s*₁ con llegada igual o anterior.

**Consecuencia.** De todos los estados de un mismo aeropuerto solo interesa el de menor *t*. Por eso dos nodos con el mismo *iata* se tratan como una **transposición** aunque su *t* difiera: ABIERTA y CERRADA se indexan por aeropuerto y conservan un único nodo por cada uno, el de llegada más temprana.

La propiedad se apoya en que esperar es gratuito y siempre posible; no se cumpliría si existiera un tiempo máximo de conexión. El estado inicial es el único sin holgura y es además el de menor instante en el origen, por lo que no rompe el argumento.

## 3.5. Algoritmo de fuerza bruta: Dijkstra

El criterio es el de la parte 1: costes arbitrarios y abundancia de transposiciones, lo que lleva a **Dijkstra**, el mismo que recomienda la solución de la asignatura para el problema de equipajes. Se expande siempre el nodo con menor *g*(*n*) y, para cada vuelo que sale de su aeropuerto, se genera el sucesor correspondiente. Como todos los costes son ≥ ε > 0, el primer nodo final que se extrae de ABIERTA corresponde a la llegada más temprana posible, y por la dominancia ningún nodo cerrado necesita reabrirse. Si ABIERTA se vacía, no existe itinerario.

## 3.6. Estructuras de datos

ABIERTA (montículo binario indexado) y CERRADA (tabla hash) son las de la parte 1, con las mismas justificaciones; cambia la clave de ordenación (*g* en lugar de *f*) y el nodo almacena además el vuelo tomado y su instante de salida para poder mostrar el itinerario. Los vuelos son información estática: una tabla hash aeropuerto → vector de vuelos salientes, de modo que generar los sucesores de un nodo cuesta *O*(*b*). El cálculo de la salida efectiva es aritmética entera en *O*(1), sin recorrer días.

Complejidad: *O*((|*V*| + |*F*|) · log |*V*|) en tiempo y *O*(|*V*|) en memoria.

---

# 4. Análisis de resultados

Las medidas se han obtenido con un script propio que ejecuta los algoritmos sobre casos aleatorios con semilla fija, por lo que son reproducibles. Los tiempos excluyen la carga de los ficheros (≈ 70 ms), que es la misma para todos los casos.

**Validación.** La optimalidad se ha contrastado con un verificador independiente basado en algoritmos distintos (Bellman-Ford y corrección de etiquetas): 270 casos de la parte 1 y 150 de la parte 2 coinciden exactamente con el óptimo de referencia. Además, A\* y fuerza bruta devuelven el mismo coste en los 500 casos de la tabla 1.

## 4.1. Parte 1: fuerza bruta frente a A\*

**Tabla 1.** Dijkstra (fuerza bruta, FB) frente a A\*. 500 pares origen–destino aleatorios; 321 con solución. Medias agrupadas por la profundidad *d* (número de vuelos) de la solución óptima.

| *d* | Casos | Expandidos FB | Expandidos A\* | Ahorro | Ramif. FB | Ramif. A\* | *b*\* FB | *b*\* A\* | ms FB | ms A\* |
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

*Ramif.*: factor de ramificación observado, sucesores generados por nodo expandido. *b*\*: factor de ramificación efectivo, el valor que haría que un árbol uniforme de profundidad *d* tuviera los *N* nodos expandidos: 1 + *b*\* + (*b*\*)² + … + (*b*\*)ᵈ = *N* + 1.

**Factor de ramificación.** El factor del grafo es *b* = 10,96 de media y 140 como máximo (AMS). El factor observado es mayor que la media del grafo en ambos algoritmos (15,6 y 28,8) porque los nodos que se expanden no son una muestra uniforme: los aeropuertos mejor conectados se alcanzan antes y se expanden con más frecuencia. El efecto es más acusado en A\*, que expande pocos nodos y casi todos son *hubs* situados en la dirección del destino. Que A\* tenga una ramificación bruta mayor no significa que trabaje más; la medida relevante es *b*\*, que pasa de **7,04 a 2,32**: la heurística convierte un árbol ancho en uno casi lineal. Es la confirmación empírica de que ρ · δ está más informada que *h* = 0.

**Efecto de la heurística.** A\* expande de media un 82 % menos de nodos y tarda un 59 % menos. El ahorro en tiempo es menor que el ahorro en nodos porque cada nodo generado por A\* requiere evaluar la fórmula de Haversine (seis funciones trigonométricas), mientras que en la fuerza bruta *h* es constante.

**Dependencia con la profundidad.** El ahorro disminuye al crecer *d*: 98,9 % con un vuelo y alrededor del 75 % con seis. Dos razones: en rutas largas el destino suele ser un aeropuerto periférico al que solo se llega dando rodeos, de modo que la línea recta subestima mucho el coste real; y la fuerza bruta está acotada por el tamaño del grafo (como máximo 881 expansiones), por lo que su desventaja no puede seguir creciendo.

**Caso desfavorable.** En las dos soluciones con *d* = 7, A\* expande menos nodos pero tarda más (3,16 ms frente a 2,77 ms). Cuando la heurística orienta poco, su coste de evaluación deja de compensar: es el equilibrio entre el coste de *h* y el ahorro de búsqueda que advierte el temario.

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

**Factor de ramificación.** El factor del modelo es *b* = 29,27 vuelos salientes de media y 546 como máximo. El factor observado ronda 60 por el mismo sesgo hacia los *hubs* que en la parte 1. Es entre dos y cuatro veces mayor que en la parte 1 porque aquí cada vuelo es un operador distinto, aunque varios unan el mismo par de aeropuertos; ABIERTA se queda solo con el que llega antes a cada destino. Sin la poda de salidas posteriores (3.3) el factor sería α · |*A*| por cada día del horizonte.

**Los parámetros cambian la solución, no la dificultad.** Al aumentar la holgura de 0 a 1440 minutos la duración media se triplica (de 29,3 a 87,8 horas) y las soluciones usan menos vuelos (de 4,48 a 3,28), porque cada conexión se encarece y compensa volar más directo. Sin embargo, el número de nodos expandidos se mantiene entre 381 y 401 y el tiempo en torno a 5,5 ms. Con la hora de inicio ocurre lo mismo: salir a las 06:00 o a las 12:00 acorta el viaje unas dos horas respecto a medianoche, porque hay más vuelos próximos, pero el esfuerzo no varía.

La explicación está en la poda por dominancia: el número de estados explorados está acotado por |*V*|, no por el tamaño |*V*| × |*T*| del espacio de estados. La holgura y la hora de inicio reordenan las llegadas, pero no cambian cuántos aeropuertos hay que cerrar antes de alcanzar el destino.

**Ejemplo.** MAD → BTS con inicio a las 00:00 y 60 minutos de holgura: MAD-FRA (05:32–07:55), FRA-VIE (09:18–10:23), VIE-KSC (12:27–13:04), KSC-BTS (14:13–14:46); 14 h 46 min en total. El enunciado propone un itinerario de tres vuelos con la misma hora de llegada: ambos son óptimos.

## 4.3. Instancias infactibles

Sí existen, y son frecuentes: **el 35,8 %** de los pares aleatorios de la parte 1 (179 de 500) y **el 34,7 %** de los de la parte 2 (104 de 300) no tienen solución. La causa es estructural: 173 aeropuertos no tienen ningún vuelo de salida en los datos y 96 no tienen ninguno de llegada, porque solo se dispone de las observaciones de un día.

En la parte 2 **la holgura y la hora de inicio no generan infactibilidad**: al repetirse los horarios cada día, siempre se puede esperar a la siguiente salida. Lo confirma la tabla 2, donde el número de casos factibles es 196 con cualquier holgura. La factibilidad depende únicamente de la conectividad, y es la misma en ambas partes.

Una instancia infactible es el **peor caso** para la búsqueda: hay que agotar todos los aeropuertos alcanzables antes de concluir que no hay ruta (744 expansiones desde MAD). En este caso A\* no aporta ninguna ventaja sobre la fuerza bruta.

## 4.4. Multiplicidad de soluciones óptimas

**Parte 1.** Es posible pero poco habitual: de 2.973 pares alcanzables analizados, solo **13 (0,44 %)** admiten más de un camino de distancia mínima. Las distancias tienen precisión de metros y es raro que dos rutas distintas sumen exactamente lo mismo.

**Parte 2.** Es mucho más habitual. El tiempo total lo determina la hora de llegada del último vuelo; si este es el único que llega pronto al destino, todos los tramos anteriores admiten alternativas con tal de enlazar a tiempo. En el ejemplo MAD → BTS con holgura 0, el tramo FRA-VIE puede hacerse con el vuelo de las 08:02 o con el de las 09:18, y también vale la ruta directa MAD-VIE del enunciado: todas enlazan con el mismo VIE-KSC de las 12:27 y llegan a las 14:46.

En ambos casos el algoritmo devuelve **una** solución óptima, determinada por el orden de extracción de ABIERTA. El coste devuelto es siempre el óptimo; el recorrido concreto puede no ser único.

## 4.5. Qué influye en el tiempo de resolución y tamaños máximos

Con los datos de la práctica cualquier instancia se resuelve en menos de 10 ms de búsqueda. El tiempo total de ejecución (≈ 80 ms en la parte 1) está dominado por la lectura de `edges.csv`. Los factores que influyen son, por orden de importancia:

1. **El tamaño del espacio de estados explorable** (|*V*|) **y el factor de ramificación** (|*E*| o |*F*|), que acotan el trabajo en el peor caso.
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

El crecimiento es prácticamente lineal con un término logarítmico, como predice la complejidad *O*((|*V*| + |*E*|) log |*V*|): al detectar transposiciones no aparece el crecimiento *O*(*b*ᵈ) del árbol de búsqueda. Un grafo mil veces mayor que la red real se resuelve en segundos. El límite práctico lo impone la **memoria** necesaria para almacenar el grafo (varios gigabytes con un millón de nodos en Python), no el tiempo de búsqueda. La parte 2 escala de la misma forma gracias a la poda por dominancia; sin ella, el número de estados crecería con el número de vuelos y no con el de aeropuertos.

---

# 5. Conclusiones

- Los dos problemas se han modelado como espacios de estados con la representación mínima suficiente: el aeropuerto en la parte 1 y el par (aeropuerto, instante) en la parte 2.
- En la parte 1, la distancia en línea recta se obtiene por relajación de restricciones, pero el redondeo de los datos le haría perder la monotonía y la admisibilidad. El factor ρ, calculado a partir de los propios datos, garantiza *h*(*n*) ≤ *h*\*(*n*) con una pérdida de información del 0,0025 %.
- A\*, con una heurística más informada que la de Dijkstra, reduce el factor de ramificación efectivo de 7,04 a 2,32 y expande un 82 % menos de nodos que la fuerza bruta, aunque su ventaja disminuye en rutas largas y desaparece en instancias sin solución.
- En la parte 2, la poda por dominancia acota el espacio explorado por |*V*| en lugar de |*V*| × |*T*|; por eso la holgura y la hora de inicio modifican la solución pero no la dificultad.
- Un tercio de las instancias son infactibles por la conectividad de los datos, y la multiplicidad de óptimos es anecdótica en distancia (0,44 %) pero habitual en tiempo.
