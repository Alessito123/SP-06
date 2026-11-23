"""Build the review manuscript and closing report from verified audit artifacts."""
import csv
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/"sp06_crisp/science/final_audit"
data=json.loads((FOLDER/"document_data.json").read_text(encoding="utf8"))
extension=json.loads((FOLDER/"extension_metrics.json").read_text(encoding="utf8"))
f=lambda x,n=3:f"{float(x):.{n}f}".replace(".",",")
def document(title):
 d=Document()
 s=d.sections[0]
 s.top_margin=s.bottom_margin=Inches(.78)
 s.left_margin=s.right_margin=Inches(.85)
 normal=d.styles["Normal"]
 normal.font.name="Calibri";normal.font.size=Pt(11)
 normal.paragraph_format.line_spacing=1.12
 normal.paragraph_format.space_after=Pt(7)
 for name,size,color in [("Title",23,"000000"),("Heading 1",15,"102A43"),("Heading 2",12,"087E8B")]:
  d.styles[name].font.size=Pt(size);d.styles[name].font.color.rgb=RGBColor.from_string(color)
 borders=d.styles["Title"].element.xpath(".//w:pBdr")
 for border in borders:border.getparent().remove(border)
 d.add_paragraph(title,"Title")
 footer=s.footer.paragraphs[0];footer.alignment=2
 footer.add_run("SP-06 · ")
 page=OxmlElement("w:fldSimple");page.set(qn("w:instr"),"PAGE");footer._p.append(page)
 return d
def p(d,text):d.add_paragraph(text)
def h(d,text):d.add_heading(text,level=1)
def table(d,title,headers,rows,note):
 cap=d.add_paragraph(title);cap.runs[0].bold=True
 cap.paragraph_format.keep_with_next=True
 t=d.add_table(rows=1,cols=len(headers))
 for cell,v in zip(t.rows[0].cells,headers):cell.text=str(v)
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
 for row in rows:
  cells=t.add_row().cells
  for cell,value in zip(cells,row):cell.text=str(value)
 for i,row in enumerate(t.rows):
  row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
  for cell in row.cells:
   for paragraph in cell.paragraphs:
    paragraph.paragraph_format.space_after=Pt(4)
    paragraph.paragraph_format.keep_with_next=i==0
    for run in paragraph.runs:run.font.size=Pt(9);run.bold=i==0
 for style in ("top","bottom","left","right","insideH","insideV"):
  border=OxmlElement("w:"+style);border.set(qn("w:val"),"nil")
  if t._tbl.tblPr.find(qn("w:tblBorders")) is None:t._tbl.tblPr.append(OxmlElement("w:tblBorders"))
  t._tbl.tblPr.find(qn("w:tblBorders")).append(border)
 for cell in t.rows[0].cells:
  borders=OxmlElement("w:tcBorders");bottom=OxmlElement("w:bottom")
  bottom.set(qn("w:val"),"single");bottom.set(qn("w:sz"),"6");borders.append(bottom)
  cell._tc.get_or_add_tcPr().append(borders)
 p(d,"Nota. "+note)
def figure(d,name,title,note):
 cap=d.add_paragraph(title);cap.runs[0].bold=True;cap.paragraph_format.keep_with_next=True
 d.add_picture(str(FOLDER/name),width=Inches(6.3))
 d.paragraphs[-1].paragraph_format.keep_with_next=True
 p(d,"Nota. "+note)

d=document("Pronóstico anual de mortalidad prematura por enfermedades no transmisibles en América Latina")
p(d,"Annual forecasting of premature noncommunicable disease mortality in Latin America")
p(d,"Alexs Jhon Arribasplata Revilla · g303300420@unitru.edu.pe · ORCID 0009-0006-9147-478X")
p(d,"Jose Alberto Herrera Torres · g273300220@unitru.edu.pe")
p(d,"Afiliaciones, grados académicos y ORCID pendiente por confirmar con los autores.")
h(d,"Resumen")
p(d,"Objetivos. Comparar pronósticos nacionales a un año de mortalidad prematura por enfermedades no transmisibles y evaluar su reproducibilidad e incertidumbre. Materiales y métodos. Se analizaron 440 observaciones de 20 países entre 2000 y 2021. Se ejecutaron 65 configuraciones de once métodos mediante seis orígenes anuales de 2013–2018, con optimización temporal interna y referencias de persistencia. Se examinó la sensibilidad a selección múltiple y dependencia temporal. Una extensión de la OMS evaluó parámetros congelados en 2022–2023, con 19 países en el análisis principal. Resultados. El menor error absoluto medio exploratorio fue 0,308 puntos porcentuales para Ridge con cinco rezagos y predicción de diferencias, frente a 0,317 de persistencia. La diferencia fue −0,009 puntos, con intervalo del 95 % de −0,027 a 0,007. En la extensión, los errores fueron 0,625 y 0,632, respectivamente. Las 7 800 predicciones archivadas se reprodujeron en un entorno limpio. Conclusiones. La ganancia observada fue pequeña e incierta. La reproducción técnica fortaleció la trazabilidad, mientras que la evaluación temporal y la calibración limitaron las afirmaciones de utilidad predictiva.")
p(d,"Palabras clave: enfermedades no transmisibles, pronóstico, mortalidad, aprendizaje automático, reproducibilidad.")
h(d,"Abstract")
p(d,"Objectives. To compare one-year national forecasts of premature noncommunicable disease mortality and assess reproducibility and uncertainty. Materials and methods. We analyzed 440 observations from 20 countries between 2000 and 2021. We evaluated 65 configurations of eleven methods across six annual rolling origins from 2013 through 2018, with inner temporal optimization and persistence benchmarks. We examined sensitivity to multiple-experiment selection and temporal dependence. A WHO release extension evaluated frozen hyperparameters in 2022–2023, with 19 countries in the primary analysis. Results. The lowest exploratory mean absolute error was 0.308 percentage points for ridge regression with five lags and difference prediction, versus 0.317 for persistence. The difference was −0.009 points, with a 95% interval from −0.027 to 0.007. Extension errors were 0.625 and 0.632, respectively. All 7,800 archived predictions were reproduced in a clean environment. Conclusions. Observed gains were small and uncertain. Technical reproduction strengthened traceability, while temporal evaluation and calibration findings limited claims of predictive usefulness.")
p(d,"Keywords: noncommunicable diseases, forecasting, mortality, machine learning, reproducibility.")
h(d,"Introducción")
p(d,"La probabilidad de morir entre las edades exactas de 30 y 70 años por enfermedades cardiovasculares, cáncer, diabetes o enfermedades respiratorias crónicas permite vigilar una parte relevante de la mortalidad prematura. El indicador 3.4.1 se expresa en porcentaje y se obtiene mediante tasas por edad y métodos de tablas de vida. Las estimaciones nacionales publicadas por la OMS y el Banco Mundial ofrecen una base comparable para analizar trayectorias poblacionales, condicionada por la calidad y la edición de los datos (1,2).")
p(d,"Un pronóstico a un año puede ayudar a planificar la vigilancia, pero su utilidad requiere una referencia adecuada. Cuando el indicador cambia lentamente, repetir el último valor observado puede competir con modelos ajustados. Además, las observaciones de un país y los años sucesivos comparten información. La evaluación temporal debe reproducir qué datos estaban disponibles para cada pronóstico y reconocer la dependencia entre observaciones (3).")
p(d,"Las guías de reporte y valoración de sesgo de modelos predictivos promueven transparencia en datos, selección y evaluación (4,5). En este estudio se adaptan esos principios a series ecológicas nacionales. El objetivo fue comparar métodos de pronóstico, cuantificar su incertidumbre y comprobar si los resultados podían reconstruirse a partir del código y los parámetros archivados.")
h(d,"Materiales y métodos")
p(d,"Se realizó un análisis ecológico retrospectivo de 20 países latinoamericanos. El panel principal de World Development Indicators incluyó 22 observaciones anuales por país, de 2000 a 2021, para ambos sexos y las cuatro causas combinadas. Se verificaron claves, rangos y cobertura. La unidad analítica fue el país-año y el desenlace fue probability_pct. La Tabla 1 detalla los bloques de análisis.")
table(d,"Tabla 1. Datos y periodos de evaluación",["Componente","Cobertura","Uso"],[
 ["Panel WDI","20 países; 2000–2021; 440 filas","Análisis histórico"],
 ["Historia común","Cinco años anteriores consecutivos","Comparación de variables sobre las mismas celdas"],
 ["Backtest externo","2013–2018; 120 país-año","Evaluación exploratoria"],
 ["Validación interna","Tres orígenes anteriores a cada año externo","Optimización temporal"],
 ["Periodo examinado","2019–2021","Sensibilidad de baselines y cobertura"],
 ["Extensión OMS","2022–2023; 19 países; 38 país-año","Evaluación temporal adicional"]
],"El nuevo backtest temporal es distinto del protocolo geográfico histórico. Los objetivos elegibles con cinco rezagos comienzan en 2005.")
p(d,"Se compararon persistencia, deriva amortiguada, media móvil de tres años, ETS con tendencia amortiguada, ARIMA(1,1,0), Ridge, Elastic Net, Random Forest, XGBoost, HistGradientBoosting y CatBoost. La deriva usó la media de las tres diferencias previas multiplicada por 0,5. Los baselines se fijaron antes de la ejecución. Los modelos ajustables utilizaron tres o cinco rezagos o cinco rezagos más diferencias, cambio relativo, media, pendiente, volatilidad y distancia respecto de la tendencia. Todas las variables se calcularon con años anteriores al objetivo.")
p(d,"Los modelos ajustables predijeron el nivel transformado mediante log(1+y) o el cambio anual. En el primer caso se aplicó expm1 a la salida y en el segundo se sumó el cambio al último valor observado. Las predicciones se acotaron a 0–100 %. Para comparar ablaciones se exigió historia de cinco años en todas las configuraciones. Ridge y Elastic Net ajustaron la estandarización dentro de su pipeline.")
p(d,"Cada origen externo de 2013–2018 utilizó todos los objetivos anteriores y evaluó el año siguiente. Optuna minimizó el MAE porcentual medio en los tres orígenes temporales anteriores al año externo (6). Se fijaron semilla 606 y diez ensayos iniciales de TPE. Se completaron presupuestos de 10, 30 y 60 para Ridge, Elastic Net e HistGradientBoosting y de diez para los otros tres árboles. Se desactivó la poda debido a los pocos bloques internos. La Figura 1 presenta el esquema.")
figure(d,"figure1_rolling.png","Figura 1. Ventanas expansivas de la evaluación temporal","Las barras indican los años objetivo de ajuste y los puntos el año externo evaluado. Cada origen tiene tres validaciones temporales internas.")
p(d,"Se reportaron MAE y RMSE en puntos porcentuales (pp), MASE con escala histórica de persistencia por país, diferencias de MAE y porcentaje de países con menor error. Los intervalos percentiles del 95 % remuestrearon 20 trayectorias nacionales completas con 5 000 réplicas. Una sensibilidad añadió bloques de uno, dos y tres años y un máximo de desviaciones absolutas para las 65 configuraciones. Este análisis condicionó a las predicciones ya ajustadas, con alcance exploratorio. No se predefinió un umbral mínimo de relevancia epidemiológica.")
p(d,"Se compararon el cuantil empírico, el rango conformal agrupado y el máximo por bloque anual sobre errores estrictamente anteriores al año evaluado. Se midieron cobertura y ancho por país y año. Cuando el rango solicitado excedió el número de bloques disponibles, el algoritmo devolvió todo el soporte 0–100 %. La dependencia y los cambios de distribución impiden trasladar automáticamente una garantía marginal de intercambiabilidad a este panel (7).")
p(d,"El periodo 2019–2021 ya había sido examinado durante el desarrollo y se conservó como tal. La búsqueda final encontró una edición de OMS con resultados hasta 2023. Antes de descargar el panel completo se congeló una extensión temporal en el commit 1d4cb56. Se excluyó Perú del análisis principal porque sus valores nuevos habían sido consultados en el sondeo. Se reajustó Ridge con cinco rezagos y objetivo de diferencias hasta 2021 en la serie OMS homogénea, manteniendo alfa 3,34804236045702 del último origen original. Se evaluaron pronósticos a un paso en 2022–2023. El valor de 2022 estuvo disponible para predecir 2023. La edición revisó también la historia, por lo que la extensión se interpretó como retrospectiva y entre versiones de fuente (2,8).")
p(d,"Se instaló un entorno científico nuevo en un clon limpio con Python 3.12.9 y versiones congeladas. Se reajustaron las 65 configuraciones con los parámetros guardados y se compararon sus predicciones. Las pruebas de integración repitieron una búsqueda breve de Optuna en procesos independientes. GitHub Actions ejecutó las pruebas en un runner Windows independiente. Los archivos conservan semillas, versiones, huellas, parámetros y resultados por origen.")
p(d,"Se analizaron estimaciones nacionales públicas agregadas. Los autores deberán confirmar la evaluación ética institucional aplicable y las declaraciones editoriales. El uso previsto es investigación y vigilancia poblacional.")
h(d,"Resultados")
p(d,"La auditoría confirmó 440 observaciones completas sin claves duplicadas. La huella del archivo LF almacenado en Git fue 26cc4eb59d77493b19d4a0e3d71a3024401c767cd46892f27bcc532d21ac0d70. La copia Windows con CRLF tuvo una huella distinta y valores idénticos. Se conservaron ambos identificadores y una representación canónica.")
p(d,"En la comparación descriptiva armonizada de tres rezagos, objetivo de diferencias y diez ensayos por búsqueda, Ridge obtuvo MAE de 0,310 pp y persistencia de 0,317 pp. La Tabla 2 muestra todos los métodos. Los errores por modelo y sus intervalos se presentan en la Figura 2. Esta armonización se formuló después de inspeccionar la búsqueda amplia y mantiene carácter exploratorio.")
common=data["common"]
common=[row for row in common if row["budget"]==0 or row["target"]=="difference"]
common.sort(key=lambda row:row["MAE"])
table(d,"Tabla 2. Comparación descriptiva con presupuesto armonizado",["Método","MAE","RMSE","MASE","Δ MAE","IC95 % de Δ"],[
 [row["model"],f(row["MAE"]),f(row["RMSE"]),f(row["MASE"]),f(row["delta_MAE"]),f'{f(row["CI_lower"])} a {f(row["CI_upper"])}'] for row in common
],"MAE, RMSE y diferencia en pp. Los métodos ajustables usaron tres rezagos y diez ensayos para predecir el cambio. Los baselines tuvieron especificación fija. Los intervalos condicionan a los modelos entrenados y no corrigen toda la selección.")
figure(d,"figure2_common.png","Figura 2. Diferencias de MAE frente a persistencia","Valores negativos favorecen al modelo. Las barras muestran intervalos percentiles por países para la comparación armonizada.")
p(d,"Entre las 65 configuraciones, el menor MAE observado fue 0,3076 pp para Ridge con cinco rezagos y 60 ensayos, frente a 0,3167 pp de persistencia. La diferencia fue −0,0091 pp, con IC95 % de −0,0265 a 0,0066 pp. Ridge tuvo menor error en el 50 % de los países. La sensibilidad simultánea por países y bloques de años produjo intervalos más amplios que incluyeron cero. La selección entre muchas configuraciones y los seis años de evaluación limitan la precisión de esa comparación.")
table(d,"Tabla 3. Extensión temporal con parámetros congelados",["Población y año","País-año","MAE Ridge","MAE persistencia"],[
 ["19 países · 2022","19",f(extension["by_year"]["error"]["2022"]),f(extension["by_year"]["baseline_error"]["2022"])],
 ["19 países · 2023","19",f(extension["by_year"]["error"]["2023"]),f(extension["by_year"]["baseline_error"]["2023"])],
 ["Total principal","38",f(extension["model_MAE"]),f(extension["baseline_MAE"])]
],"MAE en pp. Diferencia total −0,0067 pp; IC95 % por países −0,0399 a 0,0279 pp. El modelo tuvo menor MAE en 13 de 19 países. Perú se excluyó del análisis principal por inspección previa.")
p(d,"La banda agrupada de persistencia cubrió el 60 % de los países en 2020 y el 55 % en 2021. La banda por bloques cubrió el 100 % al abarcar todo el rango 0–100 %, con ancho de 100 pp (Figura 3). Ese resultado fue no informativo. La extensión de 2022–2023 se usó para evaluar predicciones puntuales y no para elegir un nuevo método de calibración.")
figure(d,"figure3_coverage.png","Figura 3. Cobertura y ancho de intervalos retrospectivos para persistencia","La línea discontinua indica el 90 % nominal. El rango por bloques abarca todo el soporte cuando faltan años para el cuantil conformal. El 100 % de cobertura en ese caso no aporta precisión.")
p(d,"Las 7 800 predicciones archivadas se reconstruyeron con diferencia máxima observada cero en el entorno limpio. Pasaron las pruebas de claves, soporte, variables pasadas, recuperación de modelos, repetición entre procesos y reproducción de parámetros. La verificación reconstruyó las predicciones y repitió una búsqueda breve, mientras que el conjunto completo de ensayos de optimización se conserva como registro de ejecución.")
h(d,"Discusión")
p(d,"Los métodos ajustables produjeron ganancias pequeñas e inciertas frente a persistencia. La predicción del cambio anual redujo el error de los árboles respecto a modelar directamente el nivel, pero esa mejora de formulación no estableció una ventaja general sobre la referencia. La extensión temporal mostró errores distintos entre 2022 y 2023 y un intervalo de diferencia que incluyó cero. Los resultados sostienen el uso de persistencia como comparador obligatorio y la evaluación del error antes de recomendar mayor complejidad.")
p(d,"Epidemiológicamente, una serie de estimaciones nacionales combina variación de mortalidad, cambios demográficos y decisiones de estimación y revisión. La estabilidad anual puede favorecer referencias simples. El desenlace compuesto y la agregación de ambos sexos limitan la identificación de desigualdades por causa, sexo o territorio subnacional. La incertidumbre publicada por la OMS tampoco quedó propagada dentro del ajuste, por lo que los intervalos del experimento representan solo una parte de la incertidumbre relevante para vigilancia (1,2).")
p(d,"La caída de cobertura durante 2020–2021 ilustra la fragilidad de calibrar con pocos años bajo dependencia y cambios del proceso. La cobertura trivial de una banda que ocupa todo el soporte debe acompañarse siempre de su ancho. Métodos adaptativos son una línea futura posible, pero su selección exigiría historia suficiente y una evaluación adicional preespecificada (7).")
p(d,"La búsqueda amplia introdujo multiplicidad y el presupuesto de diez ensayos de algunos árboles solo evaluó el muestreo inicial de TPE. Quedan pendientes sus presupuestos de 30 y 60. La comparación armonizada y el reporte de configuraciones completas hacen explícita esta limitación. Los intervalos originales por países condicionan a las predicciones y la sensibilidad temporal, con solo seis años, tiene precisión limitada. La reproducción exacta de predicciones fortalece la trazabilidad del resultado, pero no resuelve esas limitaciones inferenciales (3–5).")
p(d,"La extensión OMS añade años no utilizados para seleccionar el candidato y conserva parámetros congelados. Su independencia se refiere a esa selección, mientras que la edición revisada puede incorporar información posterior al año estimado dentro de la historia. La revisión de fuente, la exclusión de Perú por inspección previa y solo dos años en 19 países limitan esta comprobación retrospectiva. Una evaluación prospectiva con versiones disponibles en la fecha real del pronóstico permitiría valorar mejor la utilidad operativa.")
p(d,"En conclusión, el proyecto alcanzó reproducción técnica de sus predicciones y una evaluación temporal adicional documentada. La diferencia frente a persistencia fue pequeña y compatible con ausencia de ventaja. Los resultados favorecen una vigilancia que informe referencias simples, incertidumbre y versiones de los datos, y delimitan el trabajo necesario antes de recomendar el sistema para decisiones sanitarias.")
h(d,"Declaraciones")
p(d,"Contribuciones, financiación, conflictos de intereses y afiliaciones. Pendientes de confirmación y firma por los autores. Los nombres y correos se conservaron de la plantilla proporcionada.")
p(d,"Disponibilidad. Código y materiales en https://github.com/Alessito123/SP-06/tree/research/rpmesp-audit-20261123. Los resultados históricos, los datos originales, los parámetros por origen y la extensión OMS se conservan en sp06_crisp/science. La aprobación final de esta versión corresponde a los autores.")
h(d,"Referencias")
references=[
"Banco Mundial. Mortality from CVD, cancer, diabetes or CRD between exact ages 30 and 70 (%). World Development Indicators [Internet]. Indicador SH.DYN.NCOM.ZS. https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS",
"World Health Organization. Global Health Estimates [Internet]. Methods and estimates for 2000–2023. https://www.who.int/data/global-health-estimates",
"Roberts DR, Bahn V, Ciuti S, Boyce MS, Elith J, Guillera-Arroita G, et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography. 2017;40:913–929. doi:10.1111/ecog.02881.",
"Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378.",
"Moons KGM, Damen JAA, Kaul T, Hooft L, Andaur Navarro C, Dhiman P, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. BMJ. 2025;388:e082505. doi:10.1136/bmj-2024-082505.",
"Akiba T, Sano S, Yanase T, Ohta T, Koyama M. Optuna: A next-generation hyperparameter optimization framework. Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining. 2019. p. 2623–2631. doi:10.1145/3292500.3330701.",
"Gibbs I, Candès EJ. Adaptive conformal inference under distribution shift. Advances in Neural Information Processing Systems. 2021;34. https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html",
"World Health Organization. Probability of dying between exact ages 30 and 70 from cardiovascular diseases, cancer, diabetes, or chronic respiratory diseases [Internet]. Indicator NCDMORT3070. https://data.who.int/indicators/i/C540135/1F96863",
]
for i,reference in enumerate(references,1):
    paragraph=d.add_paragraph(f"{i}. {reference}")
    paragraph.paragraph_format.space_after=Pt(3)
    paragraph.paragraph_format.line_spacing=1
    for run in paragraph.runs:run.font.size=Pt(10)
d.core_properties.title=d.paragraphs[0].text
d.core_properties.subject="Análisis exploratorio y extensión temporal con parámetros congelados"
assert len(d.tables)==3 and len(d.inline_shapes)==3
d.save(ROOT/"SP06_Manuscrito_RPMESP_Auditoria_Final.docx")

r=document("Informe final de auditoría científica de SP-06")
p(r,"Rama research/rpmesp-audit-20261123 · 23 de noviembre de 2026")
for line in (FOLDER/"INFORME_FINAL.md").read_text(encoding="utf-8-sig").splitlines():
 if line.startswith("# "):continue
 if line.startswith("## "):h(r,line[3:])
 elif line.strip():p(r,line.removeprefix("- "))
h(r,"Evidencia del entorno limpio")
table(r,"Resumen de verificaciones",["Verificación","Resultado"],[
 ["Repositorio nuevo y entorno virtual independiente","Instalación restringida por versiones congeladas"],
 ["Predicciones reproducidas","7 800 en 65 configuraciones"],
 ["Diferencia numérica máxima observada","0; tolerancia de verificación 1 × 10⁻⁸"],
 ["Pruebas iniciales en clon limpio","12 pruebas superadas"],
 ["Pruebas en clon actualizado","13 pruebas superadas, incluida la extensión OMS sin conexión"],
 ["GitHub Actions","Ejecuciones 45210159007 y 45210415452 satisfactorias"],
 ["Búsqueda completa de Optuna","Registro conservado; repetición íntegra pendiente"],
 ["Extensión OMS","38 observaciones principales en 19 países; parámetros congelados"]
],"La reproducción desde parámetros y la repetición de una búsqueda breve tienen alcances distintos.")
p(r,"Evidencia pública de integración continua · https://github.com/Alessito123/SP-06/actions/runs/45210415452")
p(r,"Archivos principales · clean_reproduction.csv, clean_environment.lock.txt, clean_integration.log, selection_temporal_sensitivity.csv, extension_protocol.json y extension_metrics.json.")
h(r,"Preparación editorial")
p(r,"El manuscrito final usa estructura de artículo original, resúmenes bilingües estructurados y seis elementos gráficos combinados. Se adoptaron como referencia las instrucciones RPMESP disponibles y se requiere reconfirmar su versión vigente antes del envío. Se conserva un borrador de revisión que requiere aprobación de los autores.")
p(r,"Instrucciones consultadas · https://rpmesp.ins.gob.pe/index.php/rpmesp/article/viewFile/5025/3447")
r.save(ROOT/"SP06_Informe_Final_Auditoria_RPMESP.docx")
print("Documentos creados")
