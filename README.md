# Ventanas frías en Huancané

Proyecto del Grupo 9 para el curso Inteligencia Artificial (1INF24) de la Pontificia Universidad Católica del Perú.

Estudiamos si la historia térmica reciente permite anticipar tres días consecutivos con temperaturas mínimas iguales o inferiores a −3 °C en una celda próxima a Huancané, Puno. Esta condición se plantea como un indicador para apoyar la planificación de la elaboración de chuño. La evaluación utiliza datos climáticos históricos; no mide la calidad del producto ni el resultado de los lotes.

Comparamos regresión logística, árbol de decisión, vecinos más cercanos y una combinación de las probabilidades de logística y árbol. Como referencias utilizamos persistencia y frecuencia mensual histórica.

## Código

- [Grupo9-Huancane.ipynb](Grupo9-Huancane.ipynb). Notebook de la entrega con preprocesamiento, ajuste, evaluación y gráficas.
- [codigo/experimento.py](codigo/experimento.py). Implementación de referencia que extrae la serie de los NetCDF originales.
- [codigo/requirements.txt](codigo/requirements.txt). Dependencias de la ejecución local de referencia.

## Datos

Utilizamos las temperaturas mínimas y máximas diarias de **PISCOt v1.2**, malla de 0,10°, para 1981–2020. La celda analizada está centrada en −15,225° de latitud y −69,755° de longitud.

El [CSV de la entrega](PISCOt_Huancane_1981_2020.csv) contiene las 14 610 observaciones diarias de la celda. La columna `fecha` usa el formato `AAAA-MM-DD`. Las columnas `tmin` y `tmax` están en °C.

Los NetCDF de origen están disponibles en el [repositorio de PISCOt en Figshare](https://doi.org/10.6084/m9.figshare.22712365.v3).

- [tmin_daily_1981_2020_010.nc](https://ndownloader.figshare.com/files/40343728)
- [tmax_daily_1981_2020_010.nc](https://ndownloader.figshare.com/files/40343707)

Durante la extracción se comprobaron las dimensiones, coordenadas, unidades y huellas de ambos archivos. El CSV reúne las dos series de la celda con la precisión de los datos extraídos.

## Ejecución en Google Colab

1. Descarga el notebook y el CSV de este repositorio.
2. Abre el `.ipynb` en [Google Colab](https://colab.research.google.com/) y ejecuta todas las celdas.
3. Selecciona `PISCOt_Huancane_1981_2020.csv` cuando aparezca el selector. Si el CSV ya está en la carpeta de trabajo, el notebook lo carga por nombre.

El notebook muestra las métricas y las gráficas. Las tablas completas, las decisiones de validación y las predicciones se guardan en `resultados_grupo9/`.

## Ejecución local

Para ejecutar el notebook en Jupyter, coloca el CSV en la misma carpeta que el `.ipynb` y ejecuta todas las celdas.

### Reproducción desde los NetCDF originales

Instala las dependencias en un entorno virtual y coloca los dos NetCDF en una carpeta `data`.

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
