# Metricaz de comparacion de resultados:

1. Dunn Index

Mide la separación entre los clusters y la compacidad dentro de cada cluster.
Un valor más alto indica clusters bien separados y compactos (mejor clustering).
Se calcula como la mínima distancia entre clusters dividida por la máxima distancia dentro de un cluster.

2. Silhouette Score

Evalúa qué tan similar es un punto a su propio cluster comparado con otros clusters.
Va de -1 a 1: valores cercanos a 1 indican buen clustering, valores cercanos a 0 indican clusters solapados, y valores negativos indican mala asignación.
Se calcula para cada punto y luego se promedia.

3. Davies-Bouldin Index

Mide la relación entre la dispersión dentro de los clusters y la distancia entre clusters.
Un valor más bajo indica mejor clustering (clusters más compactos y separados).
Se calcula como el promedio de la peor relación de dispersión/distancia para cada cluster.