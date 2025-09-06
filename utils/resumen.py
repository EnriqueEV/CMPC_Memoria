import pandas as pd

# Leer el archivo Excel
df = pd.read_excel('data/Resumen_Relaciones_0509.xlsx')
print("Despues del read_excel")
# Quedarse solo con las columnas necesarias
df = df[['Usuario', 'Rol', 'Fecha']]

# Convertir la columna Fecha a datetime (formato día,mes,año)
# Filtrar solo los valores del año 2025
df_2025 = df[df['Fecha'].dt.year == 2025]
print("Despues del to_datetime")

# Guardar el resultado en un CSV
df_2025.to_csv('data/processed/resumen_2025.csv', index=False)
