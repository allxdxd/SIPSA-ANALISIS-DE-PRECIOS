import pandas as pd
import os
from processLinks import fileProcessor, extract_tranform_links, scrap_links, exportName

# Buscar los link de los archivos y traerlos
scrap_links("./agronet_scraper")

path = "./agronet_scraper/dataLinks.json"

links = extract_tranform_links(path)

df_array = []

for link in links.iterrows():
    path = link[1]['URL']
    date_start = link[1]['Fecha inicial']
    date_end = link[1]['Fecha final']
    print(f"\n\nProcesando reporte: {date_start} - {date_end}\nPath: {path}")
    df = fileProcessor(path, date_start, date_end)
    df_array.append(df)

df_final = pd.concat(df_array)  

export_file = f'./Exports/{exportName()}'
df_final.to_excel(export_file)

print(df_final)
