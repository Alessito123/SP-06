"""Interactive chart downloads and report generation for the CRISP-DM app."""
from html import escape
from io import BytesIO

import altair as alt
import pandas as pd
import streamlit as st

INTERPRETATION = (
    "La prueba reservada cubre 2018–2021. Un MAE menor indica menos error promedio. "
    "Persistencia repite el último valor observado. La banda de incertidumbre es exploratoria."
)

READING = {
    "portada": "Compara las líneas de observado, modelo y persistencia para el mismo año.",
    "mapa": "Consulta la leyenda de color y pasa el cursor sobre un país para ver su valor.",
    "ranking-paises": "Compara la longitud de las barras en la escala horizontal de probabilidad.",
    "histograma": "Lee los intervalos en el eje horizontal y la frecuencia en el vertical.",
    "cajas": "Compara la posición y el ancho de las cajas entre países.",
    "series": "Sigue cada color de izquierda a derecha para comparar la evolución por país.",
    "correlaciones": "Cruza dos variables y lee el coeficiente de Pearson en la celda.",
    "faltantes": "Un cero indica que la columna está completa en las filas analizadas.",
    "descriptivos": "Compara la mediana con la media y revisa los cuartiles.",
    "cobertura": "Compara el conteo con los años que abarca cada serie.",
    "cronograma": "Lee las fechas de inicio y fin de cada barra.",
    "rezagos": "Lee lag1, lag2 y lag3 como uno, dos y tres años anteriores.",
    "ranking-modelos": "La barra más corta corresponde al menor error medio.",
    "error-fold": "Compara modelos dentro del mismo fold antes de revisar la variación entre folds.",
    "folds": "Revisa qué países quedaron separados para evaluar cada fold.",
    "hiperparametros": "Compara el error entre modelos evaluados en el mismo fold.",
    "shap-global": "Ordena los rezagos por longitud de barra para identificar su peso relativo.",
    "mae-externo": "Ordena los valores de menor a mayor para comparar el rendimiento externo.",
    "pruebas-estadisticas": "Para Wilcoxon, lee la columna con corrección de Holm.",
    "prueba-grafico": "Compara la separación vertical entre las líneas durante 2018–2021.",
    "residuos": "Usa el cero del eje vertical como referencia para distinguir subestimación y sobreestimación.",
    "prueba-tabla": "Contrasta el observado con ambos pronósticos y revisa si cae dentro de los límites.",
    "pronostico": "Lee el último año y los extremos de su barra vertical.",
    "shap-local": "Lee el signo y la magnitud de cada barra en relación con cero.",
    "particion": "Compara los periodos cronológicos y el número de filas elegibles en cada bloque.",
    "optuna-avance": "Sigue cada búsqueda de izquierda a derecha. Una caída indica que se encontró un menor error.",
    "optuna-distribucion": "Compara las medianas y los cuartiles del error por modelo.",
    "optuna-trials": "Filtra por fold y modelo para revisar los parámetros y el estado de cada trial.",
    "optuna-importancia": "Compara la magnitud de la asociación entre el parámetro y el error dentro de una búsqueda.",
}


def show_notes(slug, note):
    st.markdown(f"**Interpretabilidad:** {READING[slug]}")
    st.markdown(f"**Explicación:** {note}")


def show_chart(slug, note, chart, **kwargs):
    st.altair_chart(chart, **kwargs)
    show_notes(slug, note)
    description = (f"<p><strong>Interpretabilidad:</strong> {escape(READING[slug])}</p>"
                   f"<p><strong>Explicación:</strong> {escape(note)}</p>")
    html = chart.to_html().replace("</body>", f"{description}</body>")
    with st.popover("Descargar gráfico"):
        st.download_button("HTML interactivo", html, f"sp06-{slug}.html", "text/html",
                           key=f"download-{slug}", on_click="ignore")
        if st.button("Preparar PNG", key=f"png-{slug}"):
            from io import BytesIO

            import vl_convert as vlc
            from PIL import Image

            spec = chart.to_dict()
            sample = Image.open(BytesIO(vlc.vegalite_to_png(spec)))
            rendered = Image.open(BytesIO(vlc.vegalite_to_png(spec, scale=3600 / sample.width)))
            image = rendered.resize((3600, round(rendered.height * 3600 / rendered.width)), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="PNG", dpi=(600, 600))
            st.download_button("Descargar PNG · 600 DPI", output.getvalue(), f"sp06-{slug}.png", "image/png",
                               key=f"download-png-{slug}", on_click="ignore")


def show_table(slug, note, table, **kwargs):
    st.dataframe(table, **kwargs)
    show_notes(slug, note)
    include_index = not isinstance(table.index, pd.RangeIndex)
    st.download_button("Descargar tabla · CSV", table.to_csv(index=include_index).encode("utf-8-sig"),
                       f"sp06-{slug}.csv", "text/csv", key=f"download-{slug}", on_click="ignore")


def show_line(slug, note, rows, *, x, y, color, x_label):
    chart = alt.Chart(rows).mark_line(point=True).encode(
        x=alt.X(f"{x}:O", title=x_label), y=f"{y}:Q", color=f"{color}:N",
        tooltip=[f"{x}:O", f"{y}:Q", f"{color}:N"],
    )
    show_chart(slug, note, chart, width="stretch")


def show_bar(slug, note, rows, *, x, y, color, horizontal=False):
    axes = {"x": f"{y}:Q", "y": f"{x}:N"} if horizontal else {"x": f"{x}:N", "y": f"{y}:Q"}
    chart = alt.Chart(rows).mark_bar(color=color).encode(**axes, tooltip=[f"{x}:N", f"{y}:Q"])
    show_chart(slug, note, chart, width="stretch")


def build_report(kind, country, metadata, metrics, folds, scores, predictions, chart):
    import vl_convert as vlc

    png = vlc.vegalite_to_png(chart.properties(width=650).to_dict(), scale=1.4)
    output = BytesIO()
    title = f"Informe de mortalidad prematura en {country}"
    period = metadata.get("prueba_reservada", {}).get("años", [2018, 2021])
    interpretation = INTERPRETATION.replace("2018–2021", f"{period[0]}–{period[-1]}")
    reading = "Interpretabilidad: compara los errores del modelo y de persistencia. En el gráfico, revisa si el observado cae dentro de la banda."
    explanation = f"Explicación: {interpretation}"
    summary = [
        f"Fuente OMS / Banco Mundial · SH.DYN.NCOM.ZS · {metadata['fuente']}",
        f"Modelo ajustado {metadata['modelo_ajustado']}",
        f"Hiperparámetros {metadata['hiperparámetros']}",
        f"SHA-256 del dataset {metadata['dataset_sha256']}",
    ]
    external = scores.groupby("modelo")["MAE log"].mean().sort_values()
    summary.append("MAE log medio de cinco folds externos · " +
                   " · ".join(f"{name} {value:.4f}" for name, value in external.items()))
    formatted = [(name, f"{value:.4f}") for name, value in metrics.items()]
    if kind == "PDF":
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        styles = getSampleStyleSheet()
        metrics_table = Table([["Métrica", "Valor"], *formatted], colWidths=[260, 120])
        metrics_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102a43")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf7f8")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story = [Paragraph(escape(title), styles["Title"])]
        story.extend(Paragraph(escape(line), styles["BodyText"]) for line in summary)
        story.extend([Spacer(1, 14), Paragraph("Prueba reservada", styles["Heading2"]), metrics_table,
                      Spacer(1, 12), Image(BytesIO(png), width=440, height=250, kind="proportional"),
                      Paragraph(reading, styles["BodyText"]),
                      Paragraph(explanation, styles["BodyText"])])
        SimpleDocTemplate(output).build(story)
        return output.getvalue(), "pdf", "application/pdf"

    if kind == "Word":
        from docx import Document
        from docx.shared import Inches

        document = Document()
        document.add_heading(title, 0)
        for line in summary:
            document.add_paragraph(line)
        document.add_heading("Prueba reservada", level=1)
        table = document.add_table(rows=1, cols=2)
        table.style = "Light Shading Accent 1"
        table.rows[0].cells[0].text = "Métrica"
        table.rows[0].cells[1].text = "Valor"
        for name, value in formatted:
            left, right = table.add_row().cells
            left.text, right.text = name, value
        document.add_picture(BytesIO(png), width=Inches(6))
        document.add_paragraph(reading)
        document.add_paragraph(explanation)
        document.save(output)
        return output.getvalue(), "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    from openpyxl import Workbook
    from openpyxl.drawing.image import Image
    from openpyxl.styles import Font, PatternFill

    book = Workbook()
    overview = book.active
    overview.title = "Resumen"
    overview.append(["Métrica", "Valor"])
    for name, value in metrics.items():
        overview.append([name, float(value)])
    overview.append([])
    overview.append(["Informe", title])
    for line in summary:
        overview.append([line])
    overview.append([reading])
    overview.append([explanation])
    image = Image(BytesIO(png))
    image.width, image.height = 660, 350
    overview.add_image(image, f"A{overview.max_row + 2}")
    overview.column_dimensions["A"].width = 34
    overview.column_dimensions["B"].width = 22
    for name, frame in [("Folds", folds), ("Validación", scores), ("Predicciones", predictions)]:
        sheet = book.create_sheet(name)
        sheet.append(list(frame.columns))
        for row in frame.itertuples(index=False, name=None):
            sheet.append(row)
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            width = max(len(str(cell.value)) for cell in column) + 2
            sheet.column_dimensions[column[0].column_letter].width = min(65, width)
    for sheet in book:
        sheet.freeze_panes = "A2"
        for cell in sheet[1]:
            cell.fill = PatternFill("solid", fgColor="102A43")
            cell.font = Font(color="FFFFFF", bold=True)
    book.save(output)
    return output.getvalue(), "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
