# Correcciones finales y preparación de SP-06 para RPMESP

Fecha de consulta y edición: 23 de noviembre de 2026.

## Dictamen
El paquete está corregido para revisión final de autores. **No está habilitado para envío**: faltan datos y declaraciones personales y no se pudo certificar la normativa editorial actual. El portal oficial respondió HTTP 468 y el navegador mostró SafeLine WAF. No se eludió el bloqueo. La página alternativa oficial en SciELO conserva instrucciones legadas y un enlace a instrucciones de 2014; no acredita reglas vigentes.

Referencia científica inmutable: `56c31dff521ec31aff92231544ac4736dacdd381`. Rama editorial independiente: `codex/rpmesp-editorial-20261123`. Los documentos originales y 78 archivos protegidos de entrada conservan sus huellas. No se modificaron modelos, datos, ensayos, parámetros ni predicciones originales.

## Cambios efectuados
| Área | Corrección |
|---|---|
| Portada | Página independiente, títulos bilingües y título corto de cinco palabras; datos no acreditados se identifican sin inventarlos. |
| Formato | Arial 10 y cuerpo 1,5 según referencia histórica 2019; Carta y márgenes 2,5 cm son decisiones provisionales. Tablas a 1,1 por legibilidad, excepción declarada. Sin encabezado o pie personalizado; numeración simple. La carta usa Arial 11 y 1,15 como formato de correspondencia, no como norma del manuscrito. |
| Ecuaciones | Se reconstruyeron únicamente las siete existentes con OMML. La número 5 incorpora fracción 1/N, multiplicación, sumatoria i=1…N, subíndices, acento de predicción y delimitadores absolutos matemáticos. RMSE tiene radical estructurado. No se agregaron ecuaciones al estudio. |
| Palabras clave | Se retiraron las notas provisionales del cuerpo. Aprendizaje Automático, Mortalidad y Predicción se verificaron directamente en DeCS y MeSH. Noncommunicable Diseases se confirmó en MeSH 2026; su equivalente español se corroboró con una captura publicada de DeCS. La recuperación primaria de esa ficha española no se completó durante mantenimiento y figura como no verificada en el checklist. No se inventó un descriptor de validación. |
| Salud pública | Se añadió un párrafo de justificación epidemiológica y uno de interpretación para Perú, manteniendo el vacío de conocimiento y evitando afirmaciones de utilidad operativa. MAE Perú Ridge 0,4202574022726697; persistencia 0,4166666666666661; diferencia +0,0035907356060036477 pp, descriptiva. |
| Resultados | Se cotejaron registros y se recalcularon métricas e intervalos, sin nuevos ajustes de modelos. Se conserva ausencia de superioridad concluyente, presupuestos limitados, carácter retrospectivo de la extensión y falta de información de bandas 0–100 %. |
| Tablas y figuras | Tres tablas y tres figuras principales; tablas editables adicionales. Figuras principales y Figura S1 en PNG, JPEG y TIFF 600 dpi y originales SVG. No se afirma aceptación vigente de esos formatos sin normativa accesible. |
| Bibliografía | Once referencias conservadas. Título portugués exacto de Malta 2025 corregido con fuente primaria y nota de errata 2026, DOI 10.1590/0102-311XER038825. Se añadió número 8 al volumen 40 de Roberts. Crossref corroboró seis DOI; dos consultas respondieron 429 y se contrastaron con PubMed/PMC y la revista. Las fuentes WDI/OMS y NeurIPS se verificaron en sus páginas oficiales. No se incorporó literatura irrelevante. |
| Suplemento | Numeración consecutiva Tabla S1–S23 y Figura S1; referencias internas ajustadas. Las 22 ecuaciones ampliadas permanecen en suplemento. Se conservan parámetros reales, métricas, errores por país/año y trazabilidad. |
| Autores y ética | Se prepararon matriz CRediT, campos de financiación/COI, determinación ética y aprobación individual sin respuestas ni firmas inventadas. Plantilla ICMJE oficial descargada sin completar. No se reconstruye declaración jurada propia bajo apariencia oficial. |
| Asistencia IA | Declaración de uso real de Codex incorporada al manuscrito, carta y control de autores. Requiere revisión de los autores y comprobación de la política específica vigente RPMESP. |
| Postulación | Carta preparada como borrador pendiente. No se presume ineditismo, aprobación de ambos autores, ausencia de conflictos o ausencia de envío simultáneo. No se realizó envío a la revista. |

## Normativa y fuentes verificadas
Consulta oficial actual: https://rpmesp.ins.gob.pe/index.php/rpmesp/pages/view/instrucciones y https://rpmesp.ins.gob.pe/index.php/rpmesp/about/submissions. Ambos accesos bloqueados. La referencia de 2019 se usa únicamente para preparación provisional: https://rpmesp.ins.gob.pe/index.php/rpmesp/article/viewFile/5025/3447. No se presenta como norma vigente.

Fuentes y reglas por requisito se registran en `SP06_Checklist_Editorial_RPMESP.xlsx` y `Fuentes_Normativas.json`. Márgenes, tamaño de papel, formatos admitidos, límites actuales y modo de cargar suplementos, documentos oficiales, política IA y procedimiento OJS deben revalidarse. Las fuentes externas ICMJE y CRediT no sustituyen las reglas específicas de RPMESP.

Descriptores primarios consultados: https://decs.bvsalud.org/es/ths/resource/?id=56143; https://decs.bvsalud.org/es/ths/resource/?id=28632; https://decs.bvsalud.org/es/ths/resource/?id=5678. MeSH: https://meshb.nlm.nih.gov/record/ui?ui=D000073296 y fichas D000069550, D009026, D005544. Se utiliza Predicción/Forecasting, distinto de Pronóstico/Prognosis. La equivalencia española ENT está corroborada en una captura publicada del portal, pero su ficha primaria no se recuperó durante mantenimiento: no se califica como plenamente verificada.

Fuentes bibliográficas adicionales para corrección: https://pmc.ncbi.nlm.nih.gov/articles/PMC12561175/; https://pubmed.ncbi.nlm.nih.gov/41779526/; https://pubmed.ncbi.nlm.nih.gov/30942336/; DOI registrados en Verificacion_Bibliografica_Crossref.json. La errata se señala por su existencia y no se atribuye a ella un cambio cuantitativo que no se haya comprobado.

Formulario oficial: https://www.icmje.org/downloads/coi_disclosure.docx, descargado desde el enlace de https://www.icmje.org/disclosure-of-interest/. Se conserva sin completar. Su SHA-256 figura en Formularios_Oficiales/Procedencia_ICMJE.json. La declaración jurada vigente RPMESP no pudo descargarse y sigue pendiente.

## Comprobación de resultados
```json
{
  "reference_commit": "56c31dff521ec31aff92231544ac4736dacdd381",
  "raw_rows": 440,
  "experiments": 65,
  "predictions_checked": 7800,
  "trial_counts": {
    "baselines": 0,
    "ablations": 10800,
    "trees": 240,
    "forest_both": 120
  },
  "metric_fields_recomputed": 260,
  "bootstrap_intervals_verified": 65,
  "max_metric_difference": 2.220446049250313e-16,
  "who_cells": 38,
  "who_metrics_verified": true,
  "originals_unchanged": 78,
  "training_reexecuted": false
}
```

Los 260 campos MAE/RMSE/MASE/diferencia y los 65 IC por país coincidieron con los archivos, dentro de 1e-12. Se comprobaron 38 celdas principales OMS y sus métricas e intervalo. Estas operaciones recalculan resultados archivados: no constituyen un nuevo entrenamiento ni una repetición completa de Optuna.

| Resultado | Fuente |
|---|---|
| 440 observaciones, 20 países, 2000–2021 | sp06_crisp/wdi_mortality.csv |
| Candidato exploratorio y 65 configuraciones | sp06_crisp/science/comparison.csv |
| Comparación armonizada de once métodos | sp06_crisp/science/final_audit/common_budget_10.csv |
| 7800 predicciones y 11160 ensayos | lotes baselines, ablations, trees, forest_both |
| IC y selección dependiente | science/final_audit/selection_temporal_sensitivity.csv |
| Cobertura y ancho retrospectivo | science/examined_coverage.csv |
| Resultados Perú y por año | science/errors_by_iso3.csv; errors_by_year.csv |
| Extensión OMS | science/final_audit/extension_protocol.json, extension_evaluation.csv, extension_metrics.json |

## Control documental y visual
```json
{
  "word_counts": {
    "body": 2778,
    "resumen": 194,
    "abstract": 183,
    "messages": 73
  },
  "pages": {
    "SP06_Manuscrito_RPMESP_Listo_Para_Revision_Final": 17,
    "SP06_Material_Suplementario_RPMESP": 27,
    "SP06_Carta_Presentacion_RPMESP": 1,
    "SP06_Documentacion_Autores_Pendiente": 3,
    "SP06_Tablas_Editables_RPMESP": 3
  },
  "checklist": {
    "CUMPLE": 22,
    "PENDIENTE": 11,
    "NO VERIFICADO": 7
  },
  "readiness": "NO ENVIAR",
  "main_native_equations": 7,
  "supplement_native_equations": 22,
  "supplement_tables": "S1–S23"
}
```

Los tres elementos tabulares principales coinciden celda por celda con el manuscrito original. Se abrieron los cinco Word editados con Microsoft Word y se exportaron para inspección de sus páginas como PNG. No se detectaron elementos fuera de página; se revisaron fórmulas, figuras y cabeceras repetidas. El renderizador de la habilidad usa LibreOffice, no disponible en esta instalación: se empleó Word nativo con Poppler como alternativa. No se afirma equivalencia de paginación entre ambos programas.

La hoja se creó con el runtime de artefactos, con validación de estados, fórmulas de conteo, formatos condicionales y encabezados congelados. La prueba de resolver un pendiente mantuvo NO ENVIAR. El checklist actualizado registra 23 cumplidos, 10 pendientes y 7 no verificados. Se revisaron las cuatro regiones renderizadas.

Las filas de tablas no se dividen; tablas extensas del suplemento continúan en varias páginas con encabezados repetidos. Las tablas/figuras principales se conservan al final, cada elemento en página propia. Las bandas y gráficos se recalcularon visualmente desde los mismos registros. Se mantienen cuatro decimales en métricas pequeñas para no ocultar sus diferencias; la regla editorial de redondeo actual requiere confirmación.

## Confirmaciones necesarias
Carrera o escuela; titularidad del ORCID de Alexs y ORCID de Jose; dirección postal si es exigida; CRediT; ratificación individual de COI; determinación ética institucional; originalidad y difusión previa; ausencia o existencia de envío simultáneo; aprobación final y firmas; declaración completa del uso de IA. Las preguntas al usuario no recibieron información sustitutiva: «continúa» no se interpretó como confirmación.

## Revisión de los ejemplos docentes
Se conservaron como referencia los nueve PDF ya examinados en la revisión anterior: 05/06 son idénticos por SHA-256 y las dos versiones JME representan un solo trabajo. No se trasladan procedimientos de clasificación ni resultados hipotéticos a la regresión SP-06. Sus originales permanecen sin cambios.

## Archivos preparados
Manuscrito, suplemento, figuras ZIP, carta borrador, checklist XLSX, documentación de autores, tablas editables separadas, formulario ICMJE original, CSV de parámetros y trazabilidad y registros QA/normativos. El paquete y la rama editorial no constituyen un envío a la revista ni una aceptación de sus condiciones.

## Actualización con datos comunicados por Alexs
23 de noviembre de 2026. Afiliación de ambos: Universidad Nacional de Trujillo, Guadalupe, Perú. Ambos son estudiantes de octavo ciclo, no un grado académico obtenido. Corresponsal: Alexs Jhon Arribasplata Revilla, g303300420@unitru.edu.pe, +51 922 290 901. Se declara ausencia de financiamiento y conflictos de intereses. Repositorio: https://github.com/Alessito123/SP-06. No se presume aprobación final, firmas ni ratificación individual de Jose. Pendientes: carrera/unidad, ORCID, CRediT, ética, originalidad y envío simultáneo, aprobación y firmas, política IA y normativa vigente.

El cuadro de control anterior corresponde a la primera entrega; lo sustituye el checklist actualizado: 23 cumplidos, 10 pendientes y 7 no verificados. Word se exportó otra vez; se revisaron visualmente las páginas modificadas. La copia se ubica en editorial/rpmesp-20261123-autores para preservar el documento abierto por el usuario.
