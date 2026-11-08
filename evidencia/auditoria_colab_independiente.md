# Auditoría independiente de la ejecución de Colab del usuario

Fecha: 8 de noviembre de 2026. Archivo recibido: `C:/Users/51924/Downloads/resultados_grupo9_drive.zip`, SHA-256 `3826797a25fa389a1d3ef661b1c5b0862d20d829d63e3a88c6f0e8de81262e8a`.

Se revisaron en lectura los 43 archivos previamente extraídos a `work/entrega_final/auditoria_colab_usuario`, frente a `outputs/entrega_final/resultados`. **No se ejecutó el código recibido, no se cargó ningún joblib y no se modificaron los resultados.** Se utilizaron rutinas independientes de lectura de CSV/JSON y cálculo de métricas.

## 1. Dictamen

La ejecución recibida es coherente con el experimento y reproduce sus resultados y conclusiones. No se detectaron discrepancias materiales de datos, selección de modelos, avisos, métricas o hipótesis. Hay una diferencia real de entorno que debe documentarse: Python y NumPy de Colab difieren de los locales. Las pequeñas diferencias de coma flotante no alteran decisiones ni cifras del informe a la precisión publicada.

`verificacion_informe.json` declara `ejecucion_en_colab: true`, origen NetCDF y controles automáticos superados. Esta revisión contrasta las salidas aportadas por el usuario; no significa que el agente haya iniciado una sesión propia de Colab ni autenticado su cuenta de Drive. A partir de esta entrega, ya corresponde informar que **el usuario ejecutó el notebook en Colab y se auditaron sus resultados**, en lugar de decir que solo existe ejecución local.

## 2. Procedencia y código

- Los manifiestos JSON de fuentes coinciden exactamente como objetos: nombres, tamaños y huellas de los dos NetCDF originales. Tmin: `2f655bbba2a45fa09fb66a0de04a3aed5ea21fb771bae1531076cae722805d66`; Tmax: `d2f0a8dda879c8c49a892cea11cf51c206f1402b0b5ddf0aeb178e53e2f25f62`.
- La serie diaria tiene 14 610 filas y coincide valor por valor con la original, incluidos sus controles de validez. Fechas ordenadas 1981–2020, sin duplicados, huecos, no finitos ni Tmin>Tmax; no hay ventanas descartadas.
- `codigo_ejecutado.py` coincide como texto normalizado con la fuente previamente auditada. Se analizó sintácticamente, sin ejecutarlo. Su huella lógica UTF-8 es `e01425d6c6f3e55c18d0b14a99eae358366d4a083a5140274a77f9101784db68` y coincide con ambos freezes. Las diferencias de fin de línea Windows/Linux no deben confundirse con cambios de programa.
- Los principales, configuraciones y α son los mismos. Los objetos de decisiones presentan once diferencias exclusivamente numéricas, con máximo absoluto `3.33e−16`, en probabilidades/umbrales; ningún cambio categórico o de conteos.

## 3. Recálculo independiente de las 36 filas

Se leyeron las predicciones completas de −2, −3 y −4 °C: 900 fechas únicas en cada archivo. Para cada definición, dos criterios de umbral y seis métodos, se recalcularon VP, FP, FN, VN, precisión, exhaustividad, F0.5, F1 y Brier.

Los conteos coinciden exactamente en las 36 filas. Los errores máximos absolutos respecto del CSV recibido, debidos a representación decimal, fueron:

| Métrica | Error máximo absoluto |
|---|---:|
| Precisión | 4.85e−13 |
| Exhaustividad | 4.85e−13 |
| F0.5 | 4.92e−13 |
| F1 | 4.87e−13 |
| Brier | 4.82e−13 |

Todos quedan por debajo de la tolerancia de auditoría `1e−10`. Se utilizaron los avisos guardados para no reconstruir decisiones desde probabilidades redondeadas.

## 4. Comparación con las salidas originales

Las siguientes comparaciones se hicieron por filas y campos, normalizando las convenciones de texto/fin de línea:

| Archivo / conjunto | Filas | Resultado |
|---|---:|---|
| Métricas de prueba | 36 | Valores idénticos |
| Métricas anuales de prueba | 180 | Valores idénticos |
| Métricas de validación | 36 | Valores idénticos |
| Resumen de candidatos CV | 36 | Valores idénticos |
| Pliegues CV | 108 | Valores idénticos |
| Selección de α | 15 | Valores idénticos |
| Predicciones a −2 y −3 °C | 900 cada una | Valores idénticos |
| Predicciones a −4 °C | 900 | Una probabilidad difiere en ≈1e−14; todos los avisos iguales |
| Auditoría de escalado | 96 | Seis diferencias flotantes, máximo ≈5.26e−18 |
| Intervalos de diferencias bootstrap | 114 | Cuatro diferencias flotantes, máximo ≈1e−16 |
| Métricas de réplicas bootstrap | 36 000 | Valores idénticos |
| Diferencias de réplicas bootstrap | 38 000 | 176 diferencias flotantes, máximo ≈1e−13 |

Las diferencias anteriores cumplen las tolerancias `rtol=1e−10, atol=1e−12`; ninguna es material. Los inicios de remuestreo calendario `.npy` coinciden por bytes con el original. Hay 1000 réplicas; el mínimo de positivos por réplica es 179 y no hay métricas F0.5 o Brier no estimables en esta ejecución.

## 5. Comprobación independiente de escaladores

La auditoría recibida tiene 96 filas: tres definiciones térmicas, dos métodos escalados y 16 atributos. Todas indican 5400 filas de entrenamiento y ausencia de validación/prueba en el ajuste.

Se reconstruyeron independientemente los 16 atributos a partir de la serie diaria recibida, con el calendario completo, rezagos y seno/coseno de denominador 365/366. Se seleccionaron solo las 5400 emisiones de 1981–2010. Las medias y desviaciones poblacionales obtenidas coinciden con las guardadas dentro del redondeo del CSV: error máximo de media ≈`4.86e−11` y de escala ≈`4.73e−12`. La media transformada reconstruida con esos parámetros ya redondeados es, como máximo, ≈`3.30e−11`. Esto no indica uso de prueba en el escalado.

Esta comprobación no carga modelos serializados; contrasta los parámetros declarados con el entrenamiento disponible y con el código previamente auditado.

## 6. Resultados e interpretación para el informe y la guía

Para el objetivo principal −3 °C, la logística fue seleccionada en validación, con C=0.1 y τ≈0.551970. La mezcla conservó α=0.75. En prueba hay 330 ventanas positivas entre 900 fechas, organizadas en 35 rachas; se mantienen sus conteos anuales y las 56 discrepancias de aviso entre logística y árbol.

| Método | VP | FP | FN | VN | F0.5 | Brier |
|---|---:|---:|---:|---:|---:|---:|
| Logística principal | 272 | 75 | 58 | 495 | 0.791618 | 0.112431 |
| Persistencia | 236 | 94 | 94 | 476 | 0.715152 | 0.208889 |
| Frecuencia mensual | 207 | 98 | 123 | 472 | 0.667742 | 0.165874 |
| Árbol | 241 | 62 | 89 | 508 | 0.781453 | 0.122625 |
| Vecinos | 239 | 70 | 91 | 500 | 0.763091 | 0.123214 |
| Mezcla | 271 | 79 | 59 | 491 | 0.783237 | 0.113003 |

Para explicar los resultados: de 347 avisos de la logística, 272 correspondieron a la etiqueta y 75 fueron falsas alarmas; de 330 ventanas reales, detectó 272 y omitió 58. Su precisión es 0.7839 y su exhaustividad 0.8242. **F0.5=0.7916 no significa que el 79.16 % de todos los días fue clasificado correctamente**; es un resumen ponderado de precisión y exhaustividad.

La principal supera puntualmente a ambas referencias en F0.5, tal como exigía la hipótesis predefinida. La mezcla mejora al árbol en Brier pero empeora ligeramente a la logística en `+0.000572`, de modo que la hipótesis complementaria sigue sin apoyo. El intervalo exploratorio mezcla−logística incluye cero; no demuestra una diferencia confirmatoria. La mezcla no debe presentarse como necesariamente superior por combinar algoritmos.

La sensibilidad F1 conserva el aumento de falsos positivos y la reducción de omisiones al bajar el umbral; no cambia el principal de la hipótesis original. Ninguna de estas salidas mide calidad del chuño, pérdidas evitadas, beneficios económicos o desempeño de parcela.

## 7. Diferencias reales de entorno y tiempos

| Componente | Ejecución local original | Colab del usuario |
|---|---|---|
| Python | 3.12.14 | **3.13.18** |
| NumPy cargado | 2.5.4 | **2.4.6** |
| pandas | 3.1.1 | 3.1.1 |
| scikit-learn | 1.9.1 | 1.9.1 |

Debe utilizarse la versión realmente registrada por el módulo en `freeze.json`; no basta el texto de versiones solicitadas al instalador. No hay base para atribuir un motivo exacto al desacuerdo de NumPy sin el historial del kernel: una biblioteca ya cargada antes de instalar otra versión es una explicación posible, no una conclusión de esta auditoría.

Colab registra: lectura/control ≈7.94 s; preparación ≈27.17 s; prueba con bootstrap ≈75.73 s. Son tiempos de esta ejecución y las fases no equivalen necesariamente a las medidas de la primera implementación local, donde preparación incluía pasos que después se separaron. No afirmar que un entorno es más rápido mediante esa comparación.

## 8. Cambios necesarios en la documentación

1. Conservar tablas, cifras principales, hipótesis y conclusiones: la reproducción no exige alterarlas.
2. Añadir evidencia de la ejecución realizada por el usuario en Colab y de su auditoría independiente; actualizar la afirmación anterior de «Colab no verificado» para no dejar información obsoleta.
3. Informar versiones reales por entorno y, si se incluyen tiempos de Colab, rotularlos como tales. No sustituir versiones de la ejecución local por versiones de Colab como si hubiera una única ejecución.
4. En la guía explicativa, separar temperatura umbral (−3 °C), probabilidad estimada y umbral de aviso (≈0.552), y explicar los conteos con denominadores correctos.
5. Mantener pendientes de acceso de los JPs al repositorio privado y contribuciones del grupo; la ejecución de Colab no resuelve esos asuntos ni valida el uso agrícola operacional.
