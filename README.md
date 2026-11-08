# Ventana Andina

Entrega final · Grupo 9 · Inteligencia Artificial 1INF24 · PUCP

## Archivos

- **Grupo9-TA-Final.pdf**: informe con la plantilla del curso; cuatro páginas de contenido y bibliografía aparte.
- **Grupo9-TA-Final.docx**: versión editable para completar las contribuciones reales de los integrantes.
- **Grupo9-TA-Exposicion.pptx**: diez diapositivas editables. La guía exige este archivo, pero no fija una duración de exposición.
- **Grupo9-Experimento-Huancane.ipynb**: notebook completo que vuelve a entrenar, seleccionar y evaluar los modelos.
- **resultados/**: auditoría, procedencia, decisiones, predicciones y métricas de la ejecución original.
- **codigo/**: implementación del experimento, resumen descriptivo y versiones de dependencias.
- **VERIFICACION_REPRODUCIBILIDAD.json**: comparación de la ejecución original con la repetición local del notebook.

## Ejecutar en Google Colab

1. Abre https://colab.research.google.com/ y sube **Grupo9-Experimento-Huancane.ipynb**.
2. Conserva `MODE="rapido"` y ejecuta todas las celdas, en orden. No necesitas GPU ni autorizar el acceso a Drive.
3. Este modo incluye la serie diaria que se extrajo de los dos NetCDF originales. Comprueba su SHA-256 y vuelve a entrenar los modelos: no se limita a mostrar métricas guardadas.
4. La última celda contrasta las métricas obtenidas con las publicadas y muestra **VERIFICADO** si coinciden dentro de la tolerancia numérica declarada. Después descarga **resultados_grupo9.zip**.
5. Abre `metricas_prueba.csv` de ese ZIP. Para la comparación principal, filtra `thermal=-3` y `beta=0.5`. `principal=True` identifica el modelo elegido en validación, no al ganador escogido después de ver la prueba.

Se ejecutaron el experimento original y el notebook completo localmente; sus métricas coincidieron. La ejecución en la nube de Google Colab todavía no se ha realizado desde esta sesión. Cambian los tiempos de ejecución y pueden cambiar detalles numéricos según la plataforma; la comprobación automática permite detectarlo.

## Verificar desde los NetCDF

El modo `drive` vuelve a extraer la celda de los archivos grandes. Requiere que los dos archivos estén accesibles en Mi unidad, autorizar el montaje y, si la búsqueda automática no los encuentra, indicar su carpeta en `DATA`.

Carpeta del grupo: https://drive.google.com/drive/folders/1wa0wVfFqymjVHS-fftfSNGHR8gEX83WP

Archivos utilizados:

- `tmin_daily_1981_2020_010.nc`
- `tmax_daily_1981_2020_010.nc`

Se usa la resolución **010 (0,10°)**. La celda seleccionada está en −15,225° / −69,755°. Los hashes y tamaños originales están en `resultados/manifest_fuentes.json`; la auditoría está en `auditoria_datos.json`. Las descargas oficiales de Figshare también figuran en la bibliografía del informe. Los NetCDF completos no se incluyen en el repositorio.

## Cifras principales

La prueba contiene 900 emisiones de 2016–2020; 330 son positivas y pertenecen a 35 rachas frías. Para −3 °C y la selección por F0,5:

| Método | F0,5 | Brier |
|---|---:|---:|
| Logística, principal | 0,7916 | 0,1124 |
| Árbol | 0,7815 | 0,1226 |
| Vecinos | 0,7631 | 0,1232 |
| Mezcla | 0,7832 | 0,1130 |
| Frecuencia mensual | 0,6677 | 0,1659 |
| Persistencia | 0,7152 | 0,2089 |

La logística supera puntualmente las dos referencias; la mezcla no supera a ambos componentes en Brier. El informe reconoce este resultado negativo. Las predicciones representan una condición térmica del aire, no una medición del éxito de lotes de chuño.

## Repositorio y pendientes del grupo

Repositorio privado: https://github.com/GustavoGarciaPUCP/ventana-andina-huancane

Antes de entregar, completen los aportes reales de los cinco integrantes, revisen la versión presentada y concedan acceso de lectura a las cuentas de los evaluadores. Las contraseñas personales no se comparten. Los dos archivos que la guía nombra para Paideia son **Grupo9-TA-Final.pdf** y **Grupo9-TA-Exposicion.pptx**; este paquete y el notebook sirven para reproducir el trabajo.
