# Protocolo SP-06 de pronóstico de mortalidad prematura por enfermedades no transmisibles en América Latina

**Versión 1.0 · 9 de noviembre de 2026**  
**Título en inglés** — Deep Learning and Explainable Forecasting of Premature Non-Communicable Disease Mortality in Latin America.

## 1. Resumen y justificación

Estudio ecológico longitudinal de pronóstico, basado en registros nacionales agregados. Se estimará la tasa anual de mortalidad prematura entre 30 y 69 años por enfermedades cardiovasculares, cáncer, diabetes y enfermedades respiratorias crónicas. La pregunta principal es si agregar historia demográfica y socioeconómica mejora el pronóstico a un año frente a la misma red con historia exclusiva de mortalidad. Se compararán ocho estrategias en orígenes temporales comunes y se publicarán errores, intervalos y cambios en la clasificación de países. El nivel territorial es el país y el uso previsto es la planificación poblacional.

La comparación entre países exige separar el envejecimiento poblacional, los cambios reales en las tasas y las diferencias en cobertura o certificación. Una red multivariante puede aprender patrones compartidos, pero la frecuencia anual limita la información disponible. La comparación con modelos simples y una ablación con arquitectura común permite estimar cuánto aportan las covariables en este contexto.

## 2. Población, periodo y unidad

Países candidatos preespecificados: ARG, BOL, BRA, CHL, COL, CRI, CUB, DOM, ECU, SLV, GTM, HTI, HND, MEX, NIC, PAN, PRY, PER, URY y VEN. Ventana candidata 1990–último año con registro disponible, limitada a años comparables en CIE-10. Evaluar hombres y mujeres por separado. Unidad de captura país × sexo × año × edad quinquenal. Unidad de modelado país × sexo × causa, con una serie adicional para la suma de las cuatro causas. Horizontes anuales h=1…5. Exigir al menos 12 años consecutivos hasta el origen, ocho estratos de edad y cobertura nacional ≥85%. Informar exclusiones por año y país, con sensibilidad al 90% y 95%. Evitar extrapolar registros de áreas parciales a la población nacional.

Para el contraste confirmatorio, fijar un panel de países y ambos sexos con resultados observables en los orígenes previstos y comunicar a qué países aplica el estimando. Conservar panel variable como análisis de sensibilidad. La interfaz permite panel variable, por lo que el investigador debe preparar el panel común antes de ese contraste. Cada causa y horizonte se evalúan con los mismos pares observados entre modelos.

## 3. Fuentes y armonización

1. **OMS** — Descargar registros de causa básica, listas CIE y documentación de formatos, geografía y completitud. Retener residentes y defunciones agregadas nacionales. Crear una tabla versionada de equivalencias de país y sexo. Leer los formatos de edad de cada extracto, agrupar 30–34 a 65–69, excluir edad desconocida e informar su proporción. Validar códigos detallados y evitar duplicar totales y subtotales. Rechazar listas abreviadas sin equivalencia verificable. [WHO Mortality Database](https://www.who.int/data/data-collection-tools/who-mortality-database)
2. **UN WPP** — Usar población de mitad de año por edad y sexo, expresada en personas. Verificar que la geografía del denominador coincide con el numerador. Usar estimaciones históricas y documentar la revisión. Las proyecciones demográficas sirven para escenarios futuros de conteos si se dispone de tasas específicas por edad. Una tasa estandarizada sola no permite estimar el número de defunciones. [World Population Prospects](https://population.un.org/wpp/)
3. **Banco Mundial** — Usar PIB por habitante PPA en dólares internacionales constantes (NY.GDP.PCAP.PP.KD) y población urbana porcentual (SP.URB.TOTL.IN.ZS). Congelar definiciones, unidad y fecha de descarga. Como sensibilidad, evaluar pobreza o desigualdad si hay cobertura comparable, con desfases y selección dentro de desarrollo. [World Development Indicators](https://wdi.worldbank.org/tables)
4. **IHME GBD** — Contrastar con estimaciones de defunciones y población por edad, sexo, año y causa de una misma edición. Armonizar las definiciones antes de comparar. Propagar draws si están disponibles y autorizados. Tratar GBD como sensibilidad a subregistro y redistribución de causas mal definidas, dado que sus insumos pueden compartir registros con OMS. No mezclar sus estimaciones con conteos OMS en la serie principal. [GBD Results](https://vizhub.healthdata.org/gbd-results/)

Antes de importar, congelar archivos, versión, fecha de publicación y descarga, hash SHA-256, responsable, mapeo CIE y tabla de exclusiones. Revisar signos, claves, duplicados, saltos de cobertura, sumas por causa y discrepancias entre OMS y denominadores oficiales. Un cero se acepta si el registro lo reporta explícitamente o su esquema garantiza que la ausencia de un código equivale a cero. Un estrato desconocido queda fuera. Las covariables ausentes se permiten. Los archivos históricos disponibles en cada origen son preferibles. Con una edición revisada única, etiquetar la prueba como retrospectiva con información revisada y cuantificar el efecto de desfases de publicación. El pipeline comienza en el CSV armonizado y no ejecuta conectores de descarga ni mapeos CIE de los proveedores.

## 4. Desenlaces y diccionario de datos

CIE-10: I00–I99 cardiovascular, C00–C97 cáncer, E10–E14 diabetes, J30–J98 respiratorias crónicas para la definición operativa alineada con OPS. Repetir con J40–J47 como sensibilidad a la definición respiratoria. Las cuatro clases son disjuntas. Para cada grupo etario a, calcular mₐ = Dₐ/Pₐ. El desenlace principal Y = 100 000 × Σ wₐmₐ usa pesos OMS normalizados dentro de 30–69: [7.61, 7.15, 6.59, 6.04, 5.37, 4.55, 3.72, 2.96] / 43.99. La tasa total suma las tasas específicas de las cuatro causas. Como desenlace secundario descriptivo calcular, a partir de tasas quinquenales combinadas, qₐ = 5mₐ/(1+2.5mₐ) y P30–70 = 1−∏(1−qₐ), según el método de tabla de vida. La implementación pronostica Y. [Estándar mundial OMS](https://seer.cancer.gov/stdpopulations/world.who.html) · [Definición del ODS 3.4.1](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/probability-of-dying-between-exact-ages-30-and-70-from-any-of-cardiovascular-disease-cancer-diabetes-or-chronic-respiratory-%28-%29) · [Notas técnicas de OPS](https://www.paho.org/en/enlace/technical-notes)

| Campo | Tipo, unidad y dominio | Fuente y regla |
|---|---|---|
| iso3 | Texto ISO alfa-3 | Mapeo OMS/WPP/WDI. Parte de la clave. |
| sex | F o M | Sexo registrado. Parte de la clave. |
| year | Entero 1950–2100 | Año calendario de ocurrencia. Parte de la clave. |
| age | Entero 30, 35, …, 65 | Límite inferior del grupo. Parte de la clave. |
| population | Real positivo en personas | WPP. Mismo ámbito que las defunciones. |
| coverage | Proporción [0,1] | Completitud documentada del registro. Obligatoria. No equivale a fracción geográfica cubierta. |
| cvd | Entero ≥0 | OMS, I00–I99. |
| cancer | Entero ≥0 | OMS, C00–C97. |
| diabetes | Entero ≥0 | OMS, E10–E14. |
| resp | Entero ≥0 | OMS, J30–J98. |
| gdp | Real positivo, nullable | WDI PIB por habitante PPA constante. Igual por grupo etario. |
| urban | Real [0,100], nullable | WDI porcentaje urbano. Igual por grupo etario. |
| series | Texto país/sexo/causa | Identificador de serie. Causa total o específica. |
| y | Real ≥0 por 100 000 | Tasa estandarizada derivada. |
| log_gdp, urban, share60 | Reales | Log natural de gdp, porcentaje urbano y fracción de 60–69 dentro de 30–69. Rezago de un año en el modelo. |
| origin, horizon | Enteros | Último año de entrenamiento y distancia al objetivo. Año objetivo = origin + horizon. |
| observed, forecast | Reales por 100 000 | Tasa observada nullable y pronóstico puntual. |
| lower90, upper90 | Reales nullable | Límites predictivos calibrados al 90% nominal. |
| scale | Real ≥0 | Cambio absoluto medio del ingenuo de un paso en historia disponible. |
| run_id, created_at | UUID, timestamptz | Identidad y fecha de ejecución PostgreSQL. |
| input_sha256, settings, metrics | Texto, JSONB, JSONB | Huella de entrada, configuración y resultados agregados. |

## 5. Hipótesis y tamaño muestral

Contraste principal a h=1 y causa total. Para cada par país-origen, promediar entre sexos la pérdida absoluta escalada por el mismo denominador histórico. Sea d la pérdida LSTM multivariante menos LSTM univariante. El estimando Δ es la media de d con igual peso por país y origen. H₀: Δ ≥ 0. H₁: Δ < 0. Se declarará superioridad si el límite superior del IC bilateral al 95% queda por debajo de cero. Se planifica detectar una diferencia absoluta de 0.10 en MASE. Para estabilidad, comparar la desviación estándar de la pérdida media entre orígenes, S = SD(L_mult) − SD(L_uni). H₀ secundaria: S ≥ 0. H₁: S < 0. Evaluar formalmente solo si el contraste principal supera el criterio, y acompañar de pérdidas por origen. No interpretar falta de significación como equivalencia. Las comparaciones entre otras arquitecturas, sexos, causas y horizontes son exploratorias, con IC y tamaños de efecto.

Planificación aproximada pareada: n_ef = [(z₀.₉₇₅ + z₀.₈₀)σd/δ]². Con α bilateral 0.05, potencia 80%, σd=0.35 y δ=0.10, n_ef=96.15, redondeado a 97. Estas cifras son supuestos de diseño, que se recalibrarán con un piloto anterior a los orígenes de evaluación. Los registros de defunciones, sexos, causas y horizontes repetidos no son réplicas independientes.

Con C países y T orígenes, aproximar n_ef = 0.85CT / [(1+(C−1)ρc) × Dt], con Dt = 1+2Σₖ₌₁…T−1(1−k/T)ρtᵏ. 0.85 representa 15% de pérdida informativa. Se supone correlación separable, intercambiable entre países en un año y AR(1) entre años, con ρt=0.30. Los mínimos del script son:

| Orígenes evaluables | ρc = 0 | ρc = 0.05 | ρc = 0.15 |
|---:|---:|---:|---:|
| 8 | 25 | Inviable | Inviable |
| 12 | 17 | 91 | Inviable |
| 16 | 13 | 33 | Inviable |
| 20 | 11 | 20 | Inviable |

El objetivo bajo dependencia moderada es 20 países × 20 orígenes, o 400 comparaciones brutas. Requeriría al menos 32 años consecutivos con un entrenamiento inicial de 12 años para h=1. La factibilidad depende de los registros CIE-10 disponibles. Si no se alcanza la información requerida, presentar inferencia exploratoria y diferencia mínima detectable con la información observada. En piloto estimar σd y dependencia por bloques. Simular paneles con la estructura de faltantes y de correlación observadas y repetir el procedimiento de evaluación para verificar potencia empírica. Para entrenamiento, evaluar curvas de aprendizaje por número de países y años, con varios orígenes internos. La potencia del contraste de pérdidas no determina el tamaño suficiente para entrenar TFT.

## 6. Arquitecturas

Entradas por ventana: tensor B × 6 × F, donde F=4 en multivariante, con mortalidad histórica y tres covariables rezagadas. La LSTM univariante usa F=1 y conserva la identidad de serie. Cada objetivo contiene cinco años siguientes, enmascarados si el valor todavía no está disponible en el origen de entrenamiento. Covariables se toman hasta el año previo en cada posición. La implementación presupone disponibilidad efectiva con ese rezago. Si las fechas de publicación exigen rezagos mayores, construir el panel de disponibilidad correspondiente antes de interpretar resultados operativos.

| Modelo | Arquitectura ejecutable |
|---|---|
| Ingenuo | Y del origen para cada h. |
| ARIMA | Ajuste por serie ARIMA(1,1,0), sin estacionalidad. Extrapolación recursiva de 1 a 5 años. |
| Ridge | Cinco regresiones directas globales. Aplanar 6×4 rezagos, añadir one-hot de serie, imputar por columna, estandarizar y ajustar con penalización L2 α=10. |
| XGBoost | Cinco regresores globales de pérdida cuadrática, mismas entradas, rutas de faltantes aprendidas. 120 árboles de profundidad 2, tasa 0.05, semilla 606. |
| LSTM | Encoder de una capa de 24 unidades. Concatenar estado final con embedding de serie de 8 dimensiones. Capa lineal 32→5. Minimizar error cuadrático de objetivos disponibles. Ablación LSTM_uni elimina las covariables. |
| TFT compacto | Embedding de serie de 24 dimensiones, contexto mediante red residual con puerta. Proyección y GRN de 24 unidades por variable. Selección softmax por paso dependiente de contexto. Encoder y decoder LSTM de 24 unidades. Decoder con embedding del horizonte y contexto, sin covariables futuras. Enriquecimiento estático, atención causal de dos cabezas, conexión residual y salida de tres cuantiles por horizonte. Pérdida pinball 0.05/0.50/0.95. La implementación adapta TFT con atención multicabeza estándar y usa la cabeza 0.50 para la evaluación común. |
| Híbrido | Descomposición local nivel + pendiente de mínimos cuadrados en los seis rezagos. Extrapolar desde la última tasa. LSTM global aprende el residuo por horizonte, condicionado a la historia y covariables. Pronóstico = tendencia extrapolada + residuo estimado. |

Las redes imputan por mediana y escalan por desviación estándar con parámetros de entrenamiento. Si una columna carece de valores se usa cero para la imputación neuronal. La etiqueta se centra y escala con valores disponibles del origen. AdamW a 0.003, lotes 64, 30 épocas por defecto, clipping de gradiente a 1 y semilla 606. Truncar pronósticos a cero. No se impone reconciliación entre pronósticos de causa y total. La tasa total se ajusta directamente para el análisis primario. [Artículo original de TFT](https://doi.org/10.1016/j.ijforecast.2021.03.012)

## 7. Validación y análisis

1. **Desarrollo.** Graficar series y cobertura. Estimar cambio porcentual anual con regresión sobre log-tasa positiva. Explorar quiebres con regresión segmentada de 0–2 puntos, segmentos de al menos cinco años y selección BIC. Contrastar con cambios de codificación, cobertura y pandemia. Reportar años 2020–2022 por separado. Mantener análisis de quiebres descriptivo, con ajuste exclusivo a los datos previos al corte cuando sirva para decidir arquitectura.
2. **Rolling origin.** Fijar orígenes de desarrollo y evaluación antes de estimar resultados. En cada corte t reajustar usando exclusivamente etiquetas ≤t. El código usa hiperparámetros fijos y un historial de longitud creciente dentro del tramo consecutivo. Si se comparan hiperparámetros, seleccionar con orígenes internos anteriores a cada corte y congelar la receta antes de examinar la evaluación final. Evaluar h=1…5 cuando existan observaciones. Registrar n por modelo, país, sexo, causa y horizonte, y reportar el último año disponible por país. El último corte global incluye las series elegibles en ese año.
3. **Pérdidas.** Reportar MAE=media(|e|), RMSE=√media(e²), MASE=media(|e|/escala) y cobertura y amplitud de intervalos. Escala = cambio absoluto medio consecutivo del historial del corte. Cuando la escala sea cero excluir ese par solo de MASE. La app reporta métricas agrupadas por causa/horizonte y contraste con peso igual por país dentro del origen. Analizar heterogeneidad por sexo, cobertura y país a partir del CSV de predicciones.
4. **Inferencia.** Bootstrap móvil de 2 000 réplicas con bloques de 3 orígenes consecutivos que incluyen todo el panel de países en cada año. Mantener apareados modelos, observaciones y sexos. Sensibilidad con longitudes 2–5, reportar IC percentil y número de orígenes. Los IC son aproximados, especialmente con pocas ventanas independientes. Inferencia condicional a la composición del panel y periodo. Para extrapolación geográfica, ejecutar evaluación separada con países retenidos y una arquitectura sin embedding de identidad o con embedding de país desconocido.
5. **Incertidumbre.** Radio del intervalo = estadístico de orden ceil[0.9(n+1)] de errores absolutos fuera de muestra, agrupados por método, causa y horizonte, con año observado ≤t. Si el rango excede n se reporta intervalo ausente. Límites max(0, pronóstico−radio) y pronóstico+radio. La dependencia y los cambios de régimen limitan garantías teóricas. Verificar cobertura por horizonte, país y sexo. Separar la incertidumbre predictiva de revisiones, medición, cobertura de registro y trayectorias de escenario.
6. **Explicabilidad.** TreeSHAP en XGBoost para el último origen por horizonte. Agregar importancia absoluta de los rezagos de cada variable y reportar identidad de serie por separado. Analizar heterogeneidad de signos y dependencia entre predictores en análisis secundario. Las atribuciones describen el modelo y no identifican efectos de política. [MASE](https://doi.org/10.1016/j.ijforecast.2006.03.001) · [SHAP](https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html)

## 8. Escenarios y traducción a salud pública

Para cada sexo y horizonte, ordenar países por la tasa total esperada y mostrar intervalos, disponibilidad del registro y distancia al promedio regional. Calcular percentiles regionales sobre el mismo conjunto de países. Etiquetar los países con alta mortalidad esperada y alta incertidumbre para revisión epidemiológica. El orden no debe interpretarse como una diferencia estadísticamente identificada si los intervalos se superponen.

Escenario base: pronóstico del modelo preespecificado o del modelo seleccionado solo con orígenes de desarrollo. Escenarios normativos: reducción adicional de 2% anual y aumento adicional de 2% anual, calculados como pronóstico base × (1+g)^h, g=−0.02 o +0.02. Son perturbaciones de planificación sobre tasas, no efectos atribuibles a cambios específicos en PIB o urbanización. Para escenarios condicionados en covariables futuras, se requiere una extensión del decoder que use proyecciones con fecha de emisión conocida. Debe validarse retrospectivamente con ediciones históricas. Usar WPP por edad para traducir a defunciones solo tras ajustar y validar tasas específicas por edad.

## 9. Gobernanza y reproducibilidad

Usar únicamente datos nacionales agregados conforme a términos de las fuentes. Solicitar determinación institucional de revisión ética antes de la ejecución formal. Registrar fuente, edición, exclusiones, umbrales y cambios del protocolo. Separar permisos de migración y escritura. Usar conexión PostgreSQL con TLS verificado si está fuera del equipo, credenciales fuera del repositorio y acceso a la app restringido. Definir responsable, retención según convenio y restauración probada de respaldos. Publicar código, parámetros y resultados agregados con licencias compatibles. Registrar hash, entorno, semilla, parámetros y fechas de corte. Congelar una ejecución por versión del análisis.

## 10. Productos científicos y alcance

El estudio entregará métricas comparables por causa y horizonte, contrastes de valor incremental de covariables, pronósticos a cinco años, perfiles por país y sensibilidad a calidad de registro. La novedad evaluable es combinar validación temporal, una ablación pareada, múltiples fuentes y explicación de rezagos en el contexto latinoamericano. Para un manuscrito competitivo en salud pública o informática sanitaria, documentar transportabilidad, incertidumbre y exclusiones, y publicar resultados desfavorables. Usar los elementos pertinentes de TRIPOD+AI adaptados al nivel ecológico. El potencial de publicación en Q1 depende de la cobertura, la calidad de la validación y la contribución demostrada. [TRIPOD+AI](https://www.bmj.com/content/385/bmj-2023-078378)

La aplicación valida el panel preparado y ejecuta estandarización, ocho métodos, rolling origin, métricas, intervalos, bootstrap, SHAP, escenarios normativos y persistencia. También explora quiebres por BIC sobre el tramo consecutivo más reciente de cada serie positiva, con penalización que cuenta la ubicación y el cambio de pendiente. Los análisis con ediciones históricas, comparación OMS–GBD y validación geográfica se especifican para la ejecución científica con datos reales. Los resultados sintéticos sirven para la comprobación técnica.
