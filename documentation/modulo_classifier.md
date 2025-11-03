# Validacion resultados clasificadores

Se implementaron los clasificadores Catboost y LightGBM para utilizarlos como filtro del alto numero de potenciales roles generados por la implementacion de similitud.

Acontinuacion se presentaran los resultados obtenidos por cada uno de estos modelos:

## Metricaz de evaluacion de entrenamiento

Las métricas utilizadas para comparar el rendimiento de los modelos fueron Precisión, Recall, ROC AUC y PR AUC. Los resultados del entrenamiento estan en la siguiente tabla.

| model | test_precision | test_recall | test_roc_auc | test_pr_auc |
| :--- | :--- | :--- | :--- | :--- |
| LightGBM | 0.8327 | 0.7715 | 0.9584 | 0.8940 |
| CatBoost | 0.8783 | 0.8542 | 0.9724 | 0.9308 |


## Validacion de resultados

Se evaluó el impacto de ambos clasificadores como un filtro sobre los roles potenciales generados por el modelo de similitud (utilizando la base generada con el umbral de 0.8). El objetivo era calibrar el umbral de confianza (score) óptimo del clasificador. Para ello, se midió cómo variaba el recall (sobre asignaciones reales) y el volumen de recomendaciones al aplicar distintos niveles de confianza.

Catboost data:

| Confidence | Recall | Recomendaciones |
| :--- | :--- | :--- |
| Sin filtro | 71.16 | 66332 |
| 0.5 | 41.16 | 10351 |
| 0.6 | 38.07 | 8469 |
| 0.7 | 32.47 | 6759 |
| 0.8 | 27.39 | 4791 |
| 0.9 | 21.40 | 2387 |

LightGBM data:

| Confidence | Recall | Recomendaciones |
| :--- | :--- | :--- |
| Sin filtro | 71.16 | 66332 |
| 0.5 | 37.03 | 10354 |
| 0.6 | 31.61 | 7821 |
| 0.7 | 25.43 | 5754 |
| 0.8 | 20.37 | 3850 |
| 0.9 | 19.63 | 1929 |

## Implementacion final

En los resultados se pude ver que en general Catboost supero en todas las pruebas a lighGBM, por lo que este sera el clasificador que quede implementado en el prototipo final.

Encuanto a la confianza, se utilizará un umbral  bajo (ej. 0.5) en la versión inicial. El objetivo es presentar un volumen mayor de recomendaciones al equipo de Gestión de Acceso para recopilar su feedback. Este umbral se irá incrementando a medida que el modelo se refine con la retroalimentación de los usuarios.