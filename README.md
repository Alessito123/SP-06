# SP-06

El [protocolo](PROTOCOLO.md) contiene el plan científico, el cálculo muestral, las arquitecturas, la armonización y el diccionario del CSV. El proyecto comienza con un panel armonizado o con datos simulados.

## Despliegue CRISP-DM y protocolo de siete fases

```powershell
.\.venv\Scripts\python -m pip install -r sp06_crisp/requirements.txt
.\.venv\Scripts\python -m streamlit run sp06_crisp/app.py --server.address 127.0.0.1 --server.port 8502
```

La opción **Protocolo de siete fases** abre datos y EDA, entrenamiento, evaluación, SHAP, reportes, motor y Optuna. **CRISP-DM histórico** conserva el diseño previo de la aplicación del puerto 8502. La aplicación del puerto 8501 tiene un punto de entrada independiente.

En el protocolo nuevo, el panel público se divide por años completos mediante el método de mayores restos. Para 2000–2021 resultan 16 años de desarrollo (2000–2015), tres de validación (2016–2018) y tres de prueba (2019–2021). Las primeras filas de cada país quedan fuera del ajuste cuando faltan rezagos. La selección usa cinco folds externos por país con corte temporal y tres folds internos por país con Optuna. El modelo ajustado se calibra con validación y se compara con persistencia sobre la prueba reservada, a un paso y con los valores previos disponibles.

Configura la búsqueda en **7. Optuna** y ejecuta **Entrenar y guardar corrida**. Los artefactos locales se escriben en `sp06_crisp/runs/`. Cada corrida incluye el manifiesto, las particiones, las puntuaciones, los trials y el modelo serializado en formato Skops o JSON nativo de XGBoost. La fase **6. Motor** muestra el comando equivalente para volver a generar un pronóstico sin entrenar:

```powershell
.\.venv\Scripts\python sp06_crisp/engine.py <id-de-corrida> PER 2022
```

Para un panel importado, conserva el CSV original y pásalo con `--csv`. El motor verifica que la huella del archivo y las versiones instaladas correspondan al manifiesto. **Sustentación** enlaza las siete vistas. La integración de DeepSeek Harness requiere una especificación externa del docente y no interviene en este flujo de entrenamiento.

## Entrega docente en el despliegue original

| Fase | Entrega | Estado |
| --- | --- | --- |
| 1. Datos públicos | Panel anual y ficha de procedencia | Disponible en la web y como CSV. |
| 2. Entrenamiento | Persistencia, Ridge y XGBoost con datos públicos | Ejecutado en la web. El guardado registra resultados y configuración. |
| 3. Motor | Inferencia independiente con modelos guardados | Pendiente. |
| 4. Validación | Prueba temporal bloqueada y selección de modelo | El backtest disponible es exploratorio. |
| 5. Explicabilidad | SHAP, intervalos y escenarios | Disponibles para exploración. |
| 6. Aplicación web | Procedencia, cobertura, gráficos y descargas | Incorporados para el panel público. |
| 7. Despliegue | Streamlit y PostgreSQL | Verificado localmente. |

## Dataset público incluido

[wdi_mortality.csv](wdi_mortality.csv) contiene 440 estimaciones anuales para 20 países de América Latina, de 2000 a 2021. El indicador SH.DYN.NCOM.ZS mide la probabilidad porcentual de morir entre los 30 y los 70 años por las cuatro ENT combinadas. La serie corresponde a ambos sexos y proviene de la OMS, a través de World Development Indicators del Banco Mundial. Copia descargada el 9 de noviembre de 2026, licencia CC BY 4.0.

[Indicador y descarga](https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS) · [Metadatos](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SH.DYN.NCOM.ZS) · [Consulta usada para la copia](https://api.worldbank.org/v2/country/ARG;BOL;BRA;CHL;COL;CRI;CUB;DOM;ECU;SLV;GTM;HTI;HND;MEX;NIC;PAN;PRY;PER;URY;VEN/indicator/SH.DYN.NCOM.ZS?format=json&source=2&date=2000:2025&per_page=1000)

El entrenamiento público inicial utiliza el historial del indicador y la identidad de cada serie. Los modos sintético y CSV propio utilizan la tasa estandarizada por 100 000 habitantes.

## Ejecutar en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --server.maxUploadSize 20
```

Abra la URL local que indica Streamlit. La fuente pública es la opción inicial. Para utilizar otro panel, seleccione **CSV propio** y cargue un CSV UTF-8 con las columnas exactas:

```text
iso3,sex,year,age,population,coverage,cvd,cancer,diabetes,resp,gdp,urban
```

La app espera conteos ya asignados a las cuatro causas, con una fila por estrato de edad. No use archivos brutos de mortalidad como entrada directa. Las celdas gdp y urban pueden quedar vacías. Para exportar una plantilla sintética ejecutable:

```powershell
.\.venv\Scripts\python -c "from pathlib import Path; from data import demo; Path('demo.csv').write_bytes(demo())"
python sample_size.py
```

## PostgreSQL

Cree una base vacía en una instancia accesible. Use el propietario para aplicar el esquema con psql. Para operar, configure un rol de aplicación con USAGE del esquema e INSERT en p06_runs y p06_predictions. Aplique la política de red y TLS de su institución. La app está pensada para ejecución local por un analista.

```powershell
psql -d p06 -v ON_ERROR_STOP=1 -f schema.sql
# Configure DATABASE_URL en la sesión mediante su mecanismo de secretos
.\.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --server.maxUploadSize 20
```

DATABASE_URL acepta un URI PostgreSQL o parámetros libpq. Tras completar un análisis pulse **Guardar ejecución en PostgreSQL**. Cada guardado registra una corrida nueva. La transacción guarda métricas y predicciones en conjunto. Los datos de entrada permanecen fuera de PostgreSQL. Conserve el CSV y su manifiesto de fuentes junto con el hash de la ejecución para permitir la réplica.

## Reiniciar el despliegue local

El despliegue de este equipo escucha en 127.0.0.1:8501. Los datos y los archivos privados de conexión están en `%LOCALAPPDATA%\P06`. Tras reiniciar Windows, ejecute desde la raíz del proyecto:

```powershell
$p06Root = Join-Path $env:LOCALAPPDATA 'P06'
$p06Data = Join-Path $p06Root 'postgres'
$p06Ctl = 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe'
& $p06Ctl -D $p06Data status
if ($LASTEXITCODE -ne 0) {
    & $p06Ctl -D $p06Data -l (Join-Path $p06Root 'postgres.log') -o '-h 127.0.0.1 -p 56507' -w start
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar PostgreSQL para P06.' }
}
$env:PGPASSFILE = Join-Path $p06Root 'pgpass.conf'
$env:DATABASE_URL = 'host=127.0.0.1 port=56507 dbname=p06 user=p06_app'
.\.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.maxUploadSize 20 --browser.gatherUsageStats false
```
