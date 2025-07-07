import pandas as pd
from processLinks import export_to_db

data =  pd.read_excel('./Exports/export-6-7-2025-19-36-53.xlsx')

export_to_db(data, 'Precios historicos')