import pandas as pd
from processLinks import export_to_db

data =  pd.read_excel('./Exports/export-9-7-2025-19-59-45.xlsx')

export_to_db(data, 'Precios historicos')