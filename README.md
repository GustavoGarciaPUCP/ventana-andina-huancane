# Ventana Andina

Entrega revisada el 8 de noviembre de 2026 · Grupo 9 · 1INF24 · PUCP

## Archivos

**Grupo9-Huancane-Colab-Drive.ipynb** es el notebook recomendado. **Grupo9-Experimento-Huancane.ipynb** contiene la misma versión para conservar el enlace anterior. Ambos muestran código Python normal, separado por etapas. No contienen datos comprimidos incrustados ni un programa convertido en una cadena enorme.

- **Grupo9-TA-Final.pdf**: informe con la plantilla del curso y bibliografía.
- **Grupo9-TA-Final.docx**: editable para completar las contribuciones reales.
- **Grupo9-TA-Exposicion.pptx**: presentación editable, con una lámina de preprocesamiento.
- **codigo/**: implementación y dependencias.
- **resultados/**: controles de calidad, diagnóstico, parámetros del escalado, decisiones y resultados.
- **evidencia/Notebook-ejecutado-localmente.ipynb**: ejecución en un kernel Jupyter local, con tablas y gráficos; no acredita autenticación en Google Drive.
- **VERIFICACION_REPRODUCIBILIDAD.json**: contraste de esta ejecución con los resultados anteriores.

## Ejecutar con tus datos de Drive

1. Abre https://colab.research.google.com/ y sube **Grupo9-Huancane-Colab-Drive.ipynb**.
2. Ejecuta las celdas en orden. La sección 1 comprueba las dependencias; requiere Python 3.12 o superior y no necesita GPU.
3. En **2. Conectar Google Drive**, autoriza el montaje de tu cuenta.
4. En **3. Pegar la ruta de la carpeta**, completa `CARPETA_DATOS` con una ruta como `/content/drive/MyDrive/TA_IA/PISCOt`. Puedes copiarla desde el panel de archivos de Colab. El enlace web de una carpeta no reemplaza esa ruta.
5. Si la carpeta es compartida, añádela a Mi unidad mediante un acceso directo y comprueba que Colab la muestre. Carpeta del grupo: https://drive.google.com/drive/folders/1wa0wVfFqymjVHS-fftfSNGHR8gEX83WP .
6. Continúa ejecutando. Se muestra la lista de archivos de la carpeta y se seleccionan exactamente `tmin_daily_1981_2020_010.nc` y `tmax_daily_1981_2020_010.nc`.
7. Por defecto se copian al almacenamiento temporal de Colab, aproximadamente 1,28 GB, para acelerar la lectura. No se modifican tus originales.
8. Al final se comprueban las cifras principales y se descarga **resultados_grupo9_drive.zip**.

Se utiliza la malla **010 (0,10°)** del protocolo. Los archivos 005 pueden estar en la carpeta, pero no se mezclan con esta resolución. Si hay dos copias de un archivo requerido, indica una carpeta más específica; el programa evita elegir una al azar.

## Preprocesamiento aplicado

1. **Validación del origen:** nombres, dimensiones, coordenadas, malla, Celsius y hashes de los dos NetCDF.
2. **Control de calidad:** calendario diario completo, orden temporal, duplicados, ausentes/no finitos y Tmin≤Tmax.
3. **Ventanas válidas:** un día inválido excluye cualquier emisión que lo utilice en los siete días de historia o tres de objetivo. No se imputa la etiqueta. En estos originales no se encontraron días inválidos.
4. **Diagnóstico de extremos:** estadísticas y rangos intercuartílicos mensuales de 1981–2010. Se conservan extremos válidos. Los atributos min/max del NetCDF no se utilizan para recortar: no describen todos los extremos de esta celda.
5. **Atributos:** siete mínimas, siete máximas y seno/coseno del día del año. Los tres días futuros solo se utilizan como etiqueta.
6. **Escalado:** StandardScaler dentro de logística y KNN, ajustado solo con entrenamiento de cada pliegue. Se reutiliza para validación/prueba. El árbol se evalúa sin escalar.
7. **Auditoría del escalado:** `auditoria_escalado.csv` conserva medias, escalas, tamaño y periodo de ajuste de los modelos finales: 96 filas, tres definiciones × dos modelos escalados × 16 atributos.
8. **Separación temporal:** entrenamiento 1981–2010, validación 2011–2015 y prueba 2016–2020. Hay pliegues crecientes dentro del entrenamiento. α, umbrales y principal se fijan antes de prueba.

No se aplican SMOTE, PCA ni imputación por rutina: cambiarían el protocolo sin evidencia que lo justifique. Los controles y transformaciones anteriores constituyen el preprocesamiento y quedan visibles en el notebook.

## Verificación

El notebook se verificó localmente y el grupo lo ejecutó después en Colab. Se auditó su ZIP: 26 CSV coinciden dentro de la precisión numérica, se recalcularon 36 filas de métricas y se comprobaron 96 registros del escalado. Colab utilizó Python 3.13.18 y NumPy 2.4.6; el entorno local utilizó 3.12.14 y 2.5.4. Las decisiones y los conteos no cambiaron. La evidencia del usuario está en evidencia/colab_usuario y su revisión en evidencia/auditoria_colab_independiente.md.

La prueba principal mantiene 900 emisiones, 330 positivas y 35 rachas frías. F0,5: logística 0,7916; persistencia 0,7152; mensual 0,6677. Brier: mezcla 0,113003 frente a 0,112431 de logística. La hipótesis complementaria sigue sin apoyo.

En tu ZIP, abre `metricas_prueba.csv` y filtra `thermal=-3` y `beta=0.5`. `principal=True` indica la elección en validación. `verificacion_informe.json` registra si datos y cifras coinciden. Las cifras se comprueban después de evaluar; no se retocan modelos para forzar la coincidencia.

## Pendientes del grupo

Repositorio privado: https://github.com/GustavoGarciaPUCP/ventana-andina-huancane

Completen las contribuciones reales, revisen la versión presentada y concedan lectura a los evaluadores. Los nombres para Paideia siguen siendo **Grupo9-TA-Final.pdf** y **Grupo9-TA-Exposicion.pptx**. Los resultados térmicos no demuestran por sí solos éxito de lotes ni pérdidas económicas evitadas.

Las huellas de los datos se calculan por bytes. La huella lógica del programa utiliza las funciones y parámetros como texto normalizado, para funcionar de la misma manera en Windows y Colab.

## Archivos para comprender y revisar

Grupo9-Guia-Resultados-y-Defensa.pdf explica NetCDF, el feedback, el preprocesamiento, los resultados y los requisitos del PDF académico. Es material de estudio independiente del informe formal. El Word final incluye la ejecución real de Colab.
