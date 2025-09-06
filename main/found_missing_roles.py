
import pandas as pd
import numpy as np
import ast

def main():
	# Cargar la matriz de similitud de usuarios
	sim_path = 'data/processed/user_similarity.csv'
	sim_df = pd.read_csv(sim_path, index_col=0)
	users = sim_df.index.tolist()

	# Cargar los roles de cada usuario
	roles_path = 'data/processed/split_roles.csv'
	roles_df = pd.read_csv(roles_path)
	# Convertir la columna de roles de string a lista
	roles_df['Rol'] = roles_df['Rol'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])

	# Pedir usuario y N
	user = input('Ingrese el nombre de usuario: ').strip().upper()
	if user not in users:
		print(f'Usuario {user} no encontrado.')
		return
	try:
		N = int(input('¿Cuántos usuarios similares comparar? (N): '))
	except ValueError:
		print('N debe ser un número entero.')
		return

	# Obtener los N usuarios más similares (excluyendo el propio usuario)
	sim_scores = sim_df.loc[user].drop(user)
	top_similar = sim_scores.sort_values(ascending=False).head(N)
	print(f'Usuarios más similares a {user}:')
	for i, (u, score) in enumerate(top_similar.items(), 1):
		print(f'{i}. {u} (similitud: {score:.3f})')

	# Obtener roles del usuario
	user_roles = set()
	user_roles_rows = roles_df[roles_df['Usuario'] == user]
	for row in user_roles_rows['Rol']:
		user_roles.update(row)

	# Obtener roles de los N usuarios más similares
	neighbors_roles = set()
	for neighbor in top_similar.index:
		neighbor_rows = roles_df[roles_df['Usuario'] == neighbor]
		for row in neighbor_rows['Rol']:
			neighbors_roles.update(row)


	# Roles que tienen los vecinos y le faltan al usuario
	missing_roles = neighbors_roles - user_roles
	if missing_roles:
		print(f'Roles que le faltan a {user} respecto a sus {N} vecinos más similares:')
		for r in sorted(missing_roles):
			print(f'- {r}')
	else:
		print(f'No se encontraron roles faltantes para {user} respecto a sus vecinos.')

	# --- Verificar si esos roles faltantes ya están en resumen_2025.csv ---
	resumen_path = 'data/processed/resumen_2025.csv'
	resumen_df = pd.read_csv(resumen_path)
	resumen_user = resumen_df[resumen_df['Usuario'] == user]
	if resumen_user.empty:
		print(f'El usuario {user} no tiene registros en resumen_2025.csv.')
		return
	# Extraer el primer elemento antes del '-' en la columna Rol
	resumen_user['Rol_base'] = resumen_user['Rol'].astype(str).apply(lambda x: x.split('-')[0])
	resumen_roles_set = set(resumen_user['Rol_base'])

	print(f'\nVerificación de roles faltantes en resumen_2025.csv para {user}:')
	for r in sorted(missing_roles):
		r_base = str(r).split('-')[0]
		if r_base in resumen_roles_set:
			print(f'✔ {r} (ya está en resumen_2025)')
		else:
			print(f'✘ {r} (NO está en resumen_2025)')

if __name__ == '__main__':
	main()
