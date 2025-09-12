VISUALIZE = True  # Cambia a False para desactivar la visualización
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
# K-modes clustering para datos categóricos/multihot
# --------------------------------------------------
# La librería kmodes permite agrupar datos categóricos (o multihot) en clusters.
# A diferencia de K-means (que usa medias y distancias euclidianas), K-modes usa:
# - Modos (categoría más frecuente) para definir el centroide de cada cluster.
# - Distancia de coincidencia simple (Hamming) para asignar puntos a clusters.
# Es ideal para datos donde las variables son binarias o categóricas (como tu matriz multihot).
#
# Pasos básicos:
# 1. Cargar los datos multihot (sin la columna de usuario).
# 2. Ajustar el modelo K-modes.
# 3. Analizar los clusters resultantes.

import pandas as pd
from kmodes.kmodes import KModes
VISUALIZE = False  # Cambia a False para desactivar la visualización

if __name__ == "__main__":
	# Cargar los vectores de usuario (ajusta la ruta si es necesario)

	df = pd.read_csv('data/processed/user_vectors.csv')
	user_ids = df.iloc[:, 0]
	X = df.iloc[:, 1:].values

	for n_clusters in range(3, 11):
		print(f"\n--- K-modes con {n_clusters} clusters ---")
		km = KModes(n_clusters=n_clusters, init='Huang', n_init=5, verbose=1)
		clusters = km.fit_predict(X)
		# Guardar solo usuario y cluster
		result_df = pd.DataFrame({
			'Usuario': user_ids,
			'cluster': clusters
		})
		out_path = f'data/processed/user_vectors_with_clusters_{n_clusters}.csv'
		result_df.to_csv(out_path, index=False)
		print(f"Guardado: {out_path}")
		print(result_df['cluster'].value_counts())

		if VISUALIZE:
			pca = PCA(n_components=2)
			X_pca = pca.fit_transform(X)
			plt.figure(figsize=(8,6))
			scatter = plt.scatter(X_pca[:,0], X_pca[:,1], c=clusters, cmap='tab10', alpha=0.7)
			plt.title(f'Visualización de clusters K-modes (PCA) - {n_clusters} clusters')
			plt.xlabel('Componente principal 1')
			plt.ylabel('Componente principal 2')
			plt.legend(*scatter.legend_elements(), title="Cluster")
			plt.tight_layout()
			plt.show()

	# Función para encontrar usuarios similares (mismo cluster)
	def find_similar_users(user_id, df):
		if user_id not in df.iloc[:,0].values:
			print(f"Usuario {user_id} no encontrado.")
			return []
		user_cluster = df.loc[df.iloc[:,0] == user_id, 'cluster'].values[0]
		similares = df[df['cluster'] == user_cluster].iloc[:,0].tolist()
		similares = [u for u in similares if u != user_id]
		print(f"Usuarios similares a {user_id} (mismo cluster {user_cluster}):")
		print(similares)
		return similares

	# Ejemplo de uso:
	# find_similar_users('USUARIO_EJEMPLO', df)

# Nota:
# - Puedes experimentar con distintos valores de n_clusters.
# - El método 'Huang' es el inicializador estándar para K-modes.
# - La salida 'verbose=1' te muestra el progreso del algoritmo.
# - El resultado es un cluster para cada usuario, útil para análisis de perfiles o segmentación.
