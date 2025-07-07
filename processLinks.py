import pandas as pd
import re
import subprocess
import os
import datetime

def scrap_links(path: str) -> dict:
    if not os.path.isdir(path):
        return {
            "Éxito": False,
            "Salida": "",
            "Error": f"La ruta '{path}' no existe."
        }

    command = ["npm.cmd", "run", "gl"]  # usar npm.cmd en Windows

    try:
        response = subprocess.run(
            command,
            cwd=path,
            check=True,
            capture_output=True,
            text=True
        )
        return {
            "Éxito": True,
            "Salida": response.stdout,
            "Error": response.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "Éxito": False,
            "Salida": e.stdout,
            "Error": e.stderr
        }
    except FileNotFoundError as e:
        return {
            "Éxito": False,
            "Salida": "",
            "Error": f"Comando no encontrado: {e}"
        }

def extract_tranform_links(path: str) -> pd.DataFrame:

    def getLinks(path):
        try:
            df = pd.read_json(path)
            df = df.rename(columns={0: 'URL'})
            return df
        except FileNotFoundError:
            print("File not found. Please ensure the file path is correct.")
            return pd.DataFrame(columns=['url'])

    links = getLinks(path)

    def extraer_fechas(url):
        # Busca el patrón de fechas tipo 3may-9may-2025
        match = re.search(r'(\d{1,2})([a-z]{3})-(\d{1,2})([a-z]{3})-(\d{4})', url, re.IGNORECASE)
        if match:
            dia_ini, mes_ini, dia_fin, mes_fin, anio = match.groups()
            meses = {'ene':'01','feb':'02','mar':'03','abr':'04','may':'05','jun':'06',
                    'jul':'07','ago':'08','sep':'09','oct':'10','nov':'11','dic':'12'}
            mes_ini_num = meses[mes_ini.lower()]
            mes_fin_num = meses[mes_fin.lower()]
            fecha_ini = f"{int(dia_ini):02d}-{mes_ini_num}-{anio}"
            fecha_fin = f"{int(dia_fin):02d}-{mes_fin_num}-{anio}"
            return fecha_ini, fecha_fin
        return None, None

    links[['Fecha inicial', 'Fecha final']] = links['URL'].apply(
        lambda url: pd.Series(extraer_fechas(url))
    )

    # Convertir las fechas a formato datetime
    links['Fecha inicial'] = pd.to_datetime(links['Fecha inicial'], format='%d-%m-%Y', errors='coerce')
    links['Fecha final'] = pd.to_datetime(links['Fecha final'], format='%d-%m-%Y', errors='coerce')

    # Calcular la distancia entre días
    links['distancia entre días'] = (links['Fecha final'] - links['Fecha inicial']).dt.days

    # Corregir el año de la fecha inicial si la distancia es menor a -300 (caso de cambio de año)
    mask = links['distancia entre días'] < -300
    links.loc[mask, 'Fecha inicial'] = links.loc[mask, 'Fecha inicial'] - pd.DateOffset(years=1) # type: ignore

    # Recalcular la distancia
    links['distancia entre días'] = (links['Fecha final'] - links['Fecha inicial']).dt.days

    return links[['URL', 'Fecha inicial', 'Fecha final', 'distancia entre días']]

def fileProcessor(path: str, date_start: str, date_end: str) -> pd.DataFrame:

    # Leer hojas de cálculo de Excel, desde la 1.1 (Verduras y hortalizas) hasta la 1.9 (Pescado)
    sheets = ['1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9']

    df_temp = []

    for sheet in sheets:
        try:
            print(f"Analizando sheet: {sheet}")
            data_temp = pd.read_excel(path, sheet_name=sheet, skipfooter=10)
        except:
            continue
        # Identificar categoría
        categoria = data_temp.iloc[4:5, 0].to_string()[10:]
        # Saltar primeras 10 filas
        data_temp = data_temp.iloc[10:]
        # Tomar solo las primeras 5 columnas
        data_temp = data_temp.iloc[:, :5]
        data_temp.columns = ['Producto', 'Mercado mayorista', 'Precio mínimo', 'Precio máximo', 'Precio medio']
        
        # convertir tipos de datos a float
        try:
            data_temp['Precio mínimo'] = data_temp['Precio mínimo'].astype(float)
            data_temp['Precio máximo'] = data_temp['Precio máximo'].astype(float)
            data_temp['Precio medio'] = data_temp['Precio medio'].astype(float)
        except:
            continue
        # agregar columnas de fecha
        data_temp['Fecha inicial'] = pd.to_datetime(date_start, format='%d-%m-%Y', errors='coerce')
        data_temp['Fecha final'] = pd.to_datetime(date_end, format='%d-%m-%Y', errors='coerce')

        # Añadir categoría
        data_temp['Categoría'] = categoria

        # Añadir df de esta hoja a el array para después ser convertido en un solo df.
        df_temp.append(data_temp)

    data = pd.concat(df_temp)
    data = data.dropna()
    return data

def exportName():
    now = datetime.datetime.now()
    return f"export-{now.day}-{now.month}-{now.year}-{now.hour}-{now.minute}-{now.second}.xlsx"

# Crear funcion que envíe el archivo a la base de datos
def export_to_db(df: pd.DataFrame, table_name: str):
    from sqlalchemy import create_engine

    # Crear conexión a la base de datos
    pgpass = os.getenv('PGADMINPASSWORD')
    engine = create_engine(f'postgresql://user:{pgpass}@localhost:5432/sipsa')

    # Exportar DataFrame a la base de datos
    df.to_sql(table_name, engine, if_exists='replace', index=False)

    print(f"Datos exportados a la tabla {table_name} en la base de datos.")