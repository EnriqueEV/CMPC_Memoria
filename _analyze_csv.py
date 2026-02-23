import pandas as pd

df = pd.read_csv('recomendaciones_ahora si_.csv')
print('=== SHAPE ===')
print(f'Filas: {df.shape[0]}, Columnas: {df.shape[1]}')
print()
print('=== COLUMNAS ===')
print(df.columns.tolist())
print()
print('=== PRIMERAS 10 FILAS ===')
print(df.head(10).to_string())
print()
print('=== ESTADÍSTICAS GENERALES ===')
print(f'Usuarios únicos: {df["user_id"].nunique() if "user_id" in df.columns else "N/A"}')

# Detectar columna de usuario
user_col = next((c for c in df.columns if 'user' in c.lower()), df.columns[0])
role_col = next((c for c in df.columns if 'role' in c.lower() or 'rol' in c.lower()), None)
conf_col = next((c for c in df.columns if 'conf' in c.lower() or 'prob' in c.lower() or 'score' in c.lower()), None)

print(f'Columna usuario detectada: {user_col}')
print(f'Columna rol detectada: {role_col}')
print(f'Columna confianza detectada: {conf_col}')
print()
print(f'Usuarios únicos: {df[user_col].nunique()}')
if role_col:
    print(f'Roles únicos recomendados: {df[role_col].nunique()}')
print()
print('=== RECS POR USUARIO (top 15 usuarios con más recs) ===')
recs_por_usuario = df[user_col].value_counts()
print(recs_por_usuario.head(15).to_string())
print()
print(f'Promedio recs por usuario: {recs_por_usuario.mean():.2f}')
print(f'Mediana recs por usuario: {recs_por_usuario.median():.1f}')
print(f'Mínimo recs por usuario: {recs_por_usuario.min()}')
print(f'Máximo recs por usuario: {recs_por_usuario.max()}')
print()
if conf_col:
    print('=== DISTRIBUCIÓN DE CONFIANZA ===')
    print(df[conf_col].describe())
    print()
    bins = [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    labels = ['0.0-0.5', '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
    df['conf_bin'] = pd.cut(df[conf_col], bins=bins, labels=labels)
    print(df['conf_bin'].value_counts().sort_index().to_string())
