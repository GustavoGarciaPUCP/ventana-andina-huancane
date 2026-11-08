# Auditoría final independiente

Revisor: agente crítico independiente. Fechas de revisión: 7 y 8 de noviembre de 2026. Se revisaron archivos existentes en modo de lectura; no se modificaron código, resultados ni documentos finales. Este archivo conserva la evidencia y los límites de la revisión.

## 1. Comprobación numérica independiente

Se contrastaron `work/entrega_final/informe_final_texto.md`, las tablas del DOCX y las salidas de `outputs/entrega_final/resultados`.

Se recalcularon desde los archivos de predicciones **las 36 filas de métricas de prueba**: tres definiciones térmicas (−3, −2 y −4 °C), dos criterios de selección de umbral (β=0.5 y β=1) y seis métodos. Para cada fila se verificaron VP, FP, FN y VN de forma exacta y se recalcularon Brier y F0.5 con tolerancia absoluta de 1e−10 respecto del CSV de métricas. Las 36 filas superaron la comprobación. No se volvió a seleccionar ningún modelo con resultados de prueba.

La comprobación leyó los avisos guardados por fecha para evitar reconstruir decisiones con probabilidades redondeadas en CSV. Brier se recalculó con las probabilidades publicadas; la tolerancia cubre su representación decimal.

También se contrastaron:

- Configuraciones, α, umbrales y modelo principal con `freeze.json`.
- Las cuatro tablas numéricas del DOCX con métricas, intervalos y resultados anuales.
- Los 35 episodios de prueba y sus conteos anuales con `resumen_descriptivo.json`.
- Los porcentajes mensuales y de entrenamiento con los archivos de prevalencia y descripción mensual.
- Las versiones y los tiempos informados con los archivos de ejecución.
- La huella SHA-256 del código con `freeze.json`: coincide. Huella auditada: `1f82b9968beb5cbcff849860ed6b9d3ae89a74a60d96aa35c08cfd3a5b3a4191`.

Para la definición principal −3 °C y β=0.5, las cifras verificadas fueron:

| Comprobación | Resultado |
|---|---:|
| Ventanas de prueba / positivas | 900 / 330 |
| Modelo principal elegido en validación | Regresión logística |
| C / α de mezcla | 0.1 / 0.75 |
| Umbral principal | 0.5519700035643216 |
| VP / FP / FN / VN de logística | 272 / 75 / 58 / 495 |
| F0.5 de logística | 0.791618160652 |
| Diferencia F0.5 frente a persistencia | +0.076466645500 |
| Diferencia F0.5 frente a frecuencia mensual | +0.123876225168 |
| Brier logística / mezcla / árbol | 0.112431201147 / 0.113003361877 / 0.122625183315 |

La conclusión del informe es coherente: la hipótesis principal queda apoyada puntualmente bajo su criterio predefinido; la complementaria no, porque la mezcla no mejora a logística en Brier. La sensibilidad F1 informa el aumento de avisos/falsos positivos y la reducción de omisiones sin sustituir al modelo principal de la evaluación original. Los intervalos se describen correctamente como exploratorios.

## 2. Alcance y requisitos del documento revisado

El PDF auditado tenía cuatro páginas de contenido y una de referencias, dentro del máximo de ocho páginas de contenido de la guía final. Incluía los apartados del formato completo, bibliografía y resultados reales. Las contribuciones se conservaron en blanco por orden expresa del usuario. No se detectaron fallos materiales de correspondencia entre informe y salidas. Se sugirió definir brevemente C como inverso de fuerza de regularización; el agente principal indicó que incorporaría esa aclaración.

## 3. Auditoría de preprocesamiento y separación temporal

Se revisó `outputs/entrega_final/codigo/experimento.py` en lectura. El código:

- Selecciona explícitamente `tmin` y `tmax`, verifica la celda, comprueba coincidencia de fechas, detiene la ejecución ante duplicados/desorden y reconstruye un calendario diario antes de crear rezagos.
- Trata valores enmascarados como ausentes; descarta ventanas que tocan datos no finitos o Tmin>Tmax, sin imputar ni eliminar extremos válidos.
- Usa siete mínimas, siete máximas y seno/coseno con denominador 365/366 del año de emisión. La etiqueta considera solo t+1, t+2 y t+3; mantiene las 180 fechas candidatas anuales.
- Ajusta la estandarización dentro de cada entrenamiento mediante pipelines para logística y vecinos; el árbol utiliza valores originales.
- Selecciona hiperparámetros en las tres etapas temporales y comprueba que las etiquetas de entrenamiento terminan antes de la evaluación. Ajusta α, umbrales y principal únicamente en 2011–2015; prueba usa modelos entrenados con 1981–2010.
- Estima la frecuencia mensual solo con entrenamiento y conserva fechas/máscara comunes. Usa probabilidades distintas más una opción sin avisos en validación, con reglas de desempate declaradas.
- Mantiene Brier para réplicas sin positivos; F0.5/F1 son no estimables en ese caso. El bootstrap emplea días calendario, bloques dentro de temporada y muestras pareadas para todos los métodos.

No se identificó un paso metodológico omitido que requiera añadir PCA, SMOTE, imputación o eliminación automática de extremos.

## 4. Comprobación directa de los NetCDF originales para el notebook revisado

El 8 de noviembre se abrieron los originales locales `work/tmin_daily_1981_2020_010.nc` y `work/tmax_daily_1981_2020_010.nc`, sin reentrenar ni escribir resultados. Las dos huellas SHA-256 coinciden con el manifiesto de fuentes de la ejecución informada:

| Archivo | SHA-256 |
|---|---|
| Tmin | `2f655bbba2a45fa09fb66a0de04a3aed5ea21fb771bae1531076cae722805d66` |
| Tmax | `d2f0a8dda879c8c49a892cea11cf51c206f1402b0b5ddf0aeb178e53e2f25f62` |

Se verificó que ambas variables tienen dimensiones `(time, latitude, longitude)`, calendario `proleptic_gregorian`, tiempo en días desde 1981-01-01 y metadatos globales que identifican temperatura en °C. La celda elegida coincide con −15.225 / −69.755. Sus 14 610 valores diarios coinciden **exactamente**, incluidos los valores binarios representados en float64, con la celda CSV de la ejecución auditada; no hay valores no finitos.

La mínima extraída varía de aproximadamente −13.78 a 6.88 °C y la máxima de 6.95 a 21.82 °C. Los atributos `min`/`max` de las variables NetCDF no describen correctamente todos esos extremos de esta celda; no deben utilizarse como límites para recortar los datos. El código auditado no los utiliza para ese fin.

Se llamó únicamente a la función pura de construcción de ejemplos y se comprobaron 7200 candidatas, 180 por cada año, 16 atributos y validez de todas las ventanas. Los positivos reconstruidos coinciden: 2263 en entrenamiento, 335 en validación y 330 en prueba para −3 °C.

**Conclusión sobre el nuevo notebook:** leer los originales NetCDF no obliga a cambiar los resultados; las entradas numéricas son exactamente las mismas. Debe conservarse el cálculo en precisión original, el orden de atributos y el protocolo. Cambiar el contenedor de un programa incrustado por celdas Python legibles y una ruta de Drive editable es una corrección de entrega y visibilidad, no una razón para añadir técnicas ni alterar el experimento. La ejecución del notebook reconstruido aún requiere su propia comprobación; esta revisión de entradas no equivale a ejecutarlo en Colab.

Mejora de protección de entrada, sin modificar el experimento: comprobar explícitamente dimensiones y °C antes de indexar cada variable, o verificar la huella esperada del original. El lector actual registra esos metadatos pero no exige su contenido. Para los dos originales auditados son correctos; no se encontró un fallo material de unidades o dimensiones en los resultados entregados.

Riesgo material al trasladar el CLI a celdas: `prepare()` y `test()` calculan `sha(__file__)`, pero `__file__` normalmente no está definido al ejecutar funciones directamente en un notebook. Se debe usar una ruta explícita a la fuente exportada para mantener la huella. El bloque `if __name__ == '__main__': main()` tampoco debe ejecutarse como celda de notebook, porque activaría `argparse` con argumentos del kernel. Se comunicaron ambos puntos al agente que reconstruye el notebook; no se modificó el código durante esta auditoría.

## 5. Límites y pendientes reales

- La segunda ejecución del notebook registrada en `VERIFICACION_REPRODUCIBILIDAD.json` fue **local**. No se ejecutó en la nube de Google Colab ni se comprobó aquí una sesión autenticada de Drive.
- La comparación local registrada informa coincidencia de métricas, CV, α, intervalos y resumen con tolerancias indicadas. No debe presentarse como evidencia de una ejecución remota.
- Las comprobaciones directas de NetCDF prueban igualdad de entradas; la identidad numérica de una ejecución remota nueva dependerá también de conservar versiones y del entorno numérico. No se garantiza igualdad binaria entre cualquier plataforma.
- Los accesos de los JPs/evaluadores al repositorio privado siguen pendientes del grupo. Debe concederse lectura mediante cuentas; no se deben inventar accesos ni compartir contraseñas.
- Las contribuciones individuales siguen pendientes del grupo y se dejan en blanco por autorización expresa. No se han inventado aportes.
- La evaluación sigue siendo retrospectiva sobre una reconstrucción climática; no demuestra beneficios económicos, calidad del chuño, operación en parcelas ni disponibilidad histórica de entradas en tiempo real.

## 6. Segunda revisión del notebook legible con Drive

Fecha: 8 de noviembre de 2026, después de la reconstrucción. Archivo entregable revisado: `outputs/entrega_final/Grupo9-Huancane-Colab-Drive.ipynb`, SHA-256 `a302ea6124a2a86e0d62160b1096d227417a636fa70c67e04ce4f05b79fe53b1`.

### Estructura y ejecución

- Contiene 50 celdas, de las cuales 33 son código Python. El código completo de las celdas supera análisis sintáctico con AST.
- No hay base64, llamadas a `exec`, `eval` o `compile`, funciones `main`, ni referencias ejecutables a `__file__` en el notebook. Las funciones del experimento están definidas directamente en celdas legibles. El texto de cabecera usado al exportar código no se evalúa como programa.
- Incluye `drive.mount('/content/drive')` al detectar Colab. La variable `CARPETA_DATOS` queda vacía para que el usuario pegue su propia ruta; acepta una carpeta del sistema montado, busca los dos NetCDF por nombres exactos y rechaza duplicados o enlaces web de Drive.
- La copia opcional a disco temporal no cambia los originales. No se inserta un CSV de datos ni se cargan modelos o predicciones anteriores para entrenar. La tabla de referencia numérica aparece después de la prueba y se utiliza únicamente para contrastar resultados.
- Se inspeccionó la copia ejecutada `work/entrega_final/ejecucion_drive/Notebook-ejecutado-localmente.ipynb`: sus 33 celdas de código tienen contadores consecutivos de 1 a 33 y no hay salidas de error. Al comparar las fuentes de todas las celdas con el entregable limpio, solo cambia la celda de configuración: ruta local y bandera de copia; el resto del código coincide.

### Validación de entrada y huella

Se revisó el nuevo `validar_metadatos`. Se confirmó independientemente, mediante lecturas y sustituciones de metadatos en memoria, que acepta el NetCDF original y rechaza: unidad K, paso de malla 0.05 y dimensiones `(time, longitude, latitude)`. No se escribieron NetCDF modificados. Esto coincide con `work/entrega_final/pruebas_entrada.json`.

Las funciones y sus parámetros se exportan mediante `inspect.getsource`; la huella lógica del código ya no depende de un nombre de archivo disponible solo en CLI. La huella guardada en el nuevo freeze es `e01425d6c6f3e55c18d0b14a99eae358366d4a083a5140274a77f9101784db68` y coincide al normalizar la fuente exportada con la lectura de texto estándar de Python y codificarla en UTF-8. En Windows el archivo puede contener CRLF, por lo que esa huella lógica no debe confundirse con el hash de bytes sin normalización; la comprobación interna usa la misma representación lógica antes y después de congelar.

### Escalado visible

Se verificó `auditoria_escalado.csv` de la nueva ejecución: **96 filas**, equivalentes a tres umbrales × dos métodos escalados × 16 atributos. Todas indican 5400 observaciones de ajuste, periodo 1981–2010 y ausencia de validación/prueba en el ajuste. La máxima media transformada absoluta es aproximadamente `6.11e−16`.

La función de auditoría no se limita a escribir esas etiquetas: compara `n_samples_seen_`, `mean_` y `var_` de cada scaler ajustado con los datos reales de entrenamiento y comprueba la media transformada. Los scalers de los pliegues anteriores siguen ajustándose dentro de sus pipelines y se comprueban durante `select_config`.

### Correspondencia con resultados originales

Se compararon directamente **los bytes completos** de nueve CSV de la nueva ejecución contra los originales, con igualdad exacta en todos ellos:

1. `metricas_prueba.csv`.
2. `metricas_prueba_anuales.csv`.
3. `alpha_validacion.csv`.
4. `cv_resumen.csv`.
5. `bootstrap_intervalos_diferencias.csv`.
6. `eda_mensual_entrenamiento.csv`.
7. `predicciones_prueba_m2.csv`.
8. `predicciones_prueba_m3.csv`.
9. `predicciones_prueba_m4.csv`.

También coinciden exactamente los objetos de decisiones del nuevo freeze y del original, así como el JSON descriptivo. Por tanto, la reconstrucción del notebook y los controles nuevos no alteraron la selección, los avisos, las probabilidades publicadas ni los resultados auditados.

**Conformidad:** no se detectaron fallos materiales pendientes en esta segunda revisión. La evidencia corresponde a un kernel Jupyter local real y a extracción desde NetCDF originales. No se ha realizado autenticación OAuth de Drive ni ejecución en la nube Colab; el montaje de Drive está implementado, pero esa interacción permanece sin verificar. Los accesos de evaluadores y las contribuciones individuales continúan como pendientes reales del grupo.
