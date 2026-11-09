# Ventanas frías en Huancané

Proyecto del Grupo 9 para el curso Inteligencia Artificial (1INF24) de la Pontificia Universidad Católica del Perú.

Estudiamos si la historia térmica reciente permite anticipar tres días consecutivos con temperaturas mínimas iguales o inferiores a −3 °C en una celda próxima a Huancané, Puno. Esta condición se plantea como un indicador para apoyar la planificación de la elaboración de chuño. La evaluación utiliza datos climáticos históricos; no mide la calidad del producto ni el resultado de los lotes.

Comparamos regresión logística, árbol de decisión, vecinos más cercanos y una combinación de las probabilidades de logística y árbol. Como referencias utilizamos persistencia y frecuencia mensual histórica.

## Código

- [Grupo9-Huancane-Colab-Drive.ipynb](Grupo9-Huancane-Colab-Drive.ipynb): notebook para ejecutar el experimento en Google Colab con datos de Drive.
- [codigo/experimento.py](codigo/experimento.py): implementación del preprocesamiento, selección de modelos y evaluación.
- [codigo/requirements.txt](codigo/requirements.txt): dependencias de la ejecución local de referencia.

## Datos

Utilizamos las temperaturas mínimas y máximas diarias de **PISCOt v1.2**, malla de 0,10°, para 1981–2020. La celda analizada está centrada en −15,225° de latitud y −69,755° de longitud.

Los archivos originales están disponibles en el [repositorio de PISCOt en Figshare](https://doi.org/10.6084/m9.figshare.22712365.v3):

- [tmin_daily_1981_2020_010.nc](https://ndownloader.figshare.com/files/40343728)
- [tmax_daily_1981_2020_010.nc](https://ndownloader.figshare.com/files/40343707)

El programa comprueba la procedencia, dimensiones, coordenadas, unidades y huellas de estos archivos antes de extraer la serie. Los datos originales se descargan por separado.

## Ejecución en Google Colab

1. Guarda los dos NetCDF en una carpeta de Google Drive.
2. Abre [Google Colab](https://colab.research.google.com/) y carga `Grupo9-Huancane-Colab-Drive.ipynb`.
3. Ejecuta las celdas en orden. En la sección **Conectar Google Drive**, autoriza el montaje de tu cuenta.
4. En **Pegar la ruta de la carpeta**, asigna `CARPETA_DATOS`, por ejemplo `/content/drive/MyDrive/TA_IA/PISCOt`. Para una carpeta compartida, añade antes un acceso directo a Mi unidad.
5. Continúa la ejecución. Al terminar se muestran las métricas y se descarga `resultados_grupo9_drive.zip`, con predicciones, tablas y gráficos.

Se requiere Python 3.12 o superior. No se necesita GPU. Por defecto, el notebook copia los archivos al almacenamiento temporal de Colab para acelerar su lectura; los originales de Drive se conservan.

## Ejecución local

Instala las dependencias en un entorno virtual y coloca los dos NetCDF en una carpeta `data`:

```bash
python -m pip install -r codigo/requirements.txt
python codigo/experimento.py all --data-dir data --out-dir resultados
```

La fase `prepare` permite ejecutar por separado el preprocesamiento y la selección. La fase `test` utiliza los modelos y decisiones guardados por `prepare` para evaluar el periodo reservado.

## Diseño del experimento

El preprocesamiento comprueba calendario, duplicados, valores ausentes, finitud y consistencia entre mínimas y máximas. Se conservan los extremos válidos. Los 16 atributos son las mínimas y máximas de los últimos siete días y dos componentes del calendario anual. Logística y vecinos incorporan un escalado aprendido exclusivamente con el entrenamiento de cada etapa.

El entrenamiento abarca 1981–2010, con tres particiones internas crecientes para elegir hiperparámetros mediante Brier. La validación de 2011–2015 determina el peso de la mezcla, los umbrales de aviso y el modelo principal. La prueba de 2016–2020 conserva esas decisiones y evalúa los seis métodos en las mismas fechas. La métrica principal es F₀,₅, acompañada de precisión, exhaustividad, F₁ y Brier; también se examinan variación anual, sensibilidad térmica e intervalos exploratorios por bloques.

En la ejecución principal, la logística obtuvo F₀,₅ = 0,7916, frente a 0,7152 de persistencia y 0,6677 de frecuencia mensual. La mezcla mejoró al árbol en Brier, pero no a la logística. Estas cifras corresponden a 900 emisiones de prueba y a la etiqueta térmica definida, con ventanas solapadas.

## Referencia de los datos

Huerta, A. et al. (2023). *High-resolution grids of daily air temperature for Peru — the new PISCOt v1.2 dataset*. Scientific Data, 10, 847. https://doi.org/10.1038/s41597-023-02777-w
