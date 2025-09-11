import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime
from ast import literal_eval

def safe_list(val):
	if isinstance(val, list):
		return val
	if pd.isna(val):
		return []
	if isinstance(val, str):
		s = val.strip()
		# Intenta parsear listas en formato string
		if s.startswith('[') and s.endswith(']'):
			try:
				parsed = literal_eval(s)
				if isinstance(parsed, list):
					return parsed
			except Exception:
				pass
		# Si viene como string simple, devuelve lista con el string
		return [s] if s else []
	return []


def build_roles_to_remove(resumen_df: pd.DataFrame, cutoff: str) -> dict:
	# Asegura datetime y filtra asignaciones posteriores a cutoff
	resumen_df = resumen_df.copy()
	resumen_df['Fecha'] = pd.to_datetime(resumen_df['Fecha'], errors='coerce')
	cutoff_dt = pd.to_datetime(cutoff)
	mask = resumen_df['Fecha'] > cutoff_dt
	posteriores = resumen_df.loc[mask, ['Usuario', 'Rol']]

	# Extrae nombre base del rol (antes del primer '-')
	posteriores['RolBase'] = posteriores['Rol'].astype(str).str.split('-').str[0]

	# Mapa: usuario -> set(roles a remover)
	roles_remove = posteriores.groupby('Usuario')['RolBase'].apply(lambda s: set(s.dropna().tolist())).to_dict()
	return roles_remove


def filter_split_roles(split_roles_df: pd.DataFrame, roles_to_remove: dict) -> pd.DataFrame:
	df = split_roles_df.copy()
	# Asegura que 'Rol' y 'Location' sean listas
	df['Rol'] = df['Rol'].apply(safe_list)
	df['Location'] = df['Location'].apply(safe_list)

	new_rol = []
	new_loc = []
	removed_counts = []

	for _, row in df.iterrows():
		usuario = row['Usuario']
		roles = row['Rol']
		locs = row['Location']

		remove_set = roles_to_remove.get(usuario, set())

		# Mantén alineación rol-location
		filtered_roles = []
		filtered_locs = []
		removed = 0
		for r, l in zip(roles, locs):
			if r in remove_set:
				removed += 1
				continue
			filtered_roles.append(r)
			filtered_locs.append(l)

		# Si listas tienen tamaños distintos por datos corruptos, recorta al mínimo
		if len(filtered_roles) != len(filtered_locs):
			m = min(len(filtered_roles), len(filtered_locs))
			filtered_roles = filtered_roles[:m]
			filtered_locs = filtered_locs[:m]

		new_rol.append(filtered_roles)
		new_loc.append(filtered_locs)
		removed_counts.append(removed)

	df['Rol'] = new_rol
	df['Location'] = new_loc
	df['RemovedAfterCutoff'] = removed_counts
	return df


def main():
	# Cambiar cutoff por la fecha minima deseada
	cutoff = "2025-01-01"
	# Rutas
	base = Path('data/processed')
	split_roles_path = base / 'split_roles.csv'
	resumen_path = base / 'resumen_2025.csv'

	if not split_roles_path.exists():
		print(f'No existe {split_roles_path}')
		return
	if not resumen_path.exists():
		print(f'No existe {resumen_path}')
		return

	# Carga
	split_roles_df = pd.read_csv(split_roles_path)
	split_roles_df['Rol'] = split_roles_df['Rol'].apply(literal_eval)
	split_roles_df['Location'] = split_roles_df['Location'].apply(literal_eval)
	resumen_df = pd.read_csv(resumen_path)

	# Validación de columnas mínimas
	for col in ['Usuario', 'Rol']:
		if col not in resumen_df.columns:
			print(f'Falta columna {col} en {resumen_path}')
			return
	for col in ['Usuario', 'Rol', 'Location']:
		if col not in split_roles_df.columns:
			print(f'Falta columna {col} en {split_roles_path}')
			return

	roles_to_remove = build_roles_to_remove(resumen_df, cutoff)

	filtered_df = filter_split_roles(split_roles_df, roles_to_remove)

	# Elimina usuarios sin roles
	filtered_df = filtered_df[filtered_df['Rol'].apply(lambda x: len(x) > 0)]

	# Guarda resultado
	out_path = base / f'split_roles_asof_{cutoff}.csv'
	filtered_df.to_csv(out_path, index=False)

	afectados = sum(1 for v in roles_to_remove.values() if v)
	total_removed = filtered_df['RemovedAfterCutoff'].sum()
	print(f'Generado: {out_path}')
	print(f'Usuarios afectados: {afectados} | Roles eliminados: {total_removed}')


if __name__ == '__main__':
	main()
