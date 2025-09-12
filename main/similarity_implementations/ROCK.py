from pyclustering.cluster.rock import rock
from pyclustering.utils import distance_metric, type_metric
# NOTA: Existen implementaciones de ROCK en pyclustering (https://pyclustering.github.io/docs/0.10.1/html/d0/d3a/classpyclustering_1_1cluster_1_1rock_1_1rock.html),
# pero aquí se implementa desde cero para mayor control y personalización.
import pandas as pd
import numpy as np
from collections import defaultdict


# Parámetros
THETA = 0.7  # Umbral de similitud para considerar vecinos
N_CLUSTERS_RANGE = range(3, 11)  # Probar de 3 a 10 clusters

def build_neighbors(sim_df, theta):
	"""Construye matriz binaria de vecinos y diccionario de vecinos por usuario."""
	neighbors_matrix = (sim_df.values >= theta).astype(int)
	np.fill_diagonal(neighbors_matrix, 0)
	user_ids = sim_df.index.tolist()
	neighbors_dict = {
		user: [user_ids[j] for j, is_neighbor in enumerate(neighbors_matrix[i]) if is_neighbor]
		for i, user in enumerate(user_ids)
	}
	return neighbors_matrix, neighbors_dict, user_ids

def count_links(cluster_a, cluster_b, neighbors_dict):
	"""Cuenta los links entre dos clusters (conjuntos de usuarios)."""
	links = 0
	for u in cluster_a:
		for v in cluster_b:
			if v in neighbors_dict[u]:
				links += 1
	return links

def rock_clustering(sim_df, theta, n_clusters):
	neighbors_matrix, neighbors_dict, user_ids = build_neighbors(sim_df, theta)
	# Inicialmente, cada usuario es su propio cluster
	clusters = [{u} for u in user_ids]

	# Precalcular número de vecinos para cada usuario
	num_neighbors = {u: len(neighbors_dict[u]) for u in user_ids}

	def goodness(ci, cj):
		# Fórmula de ROCK: links(ci, cj) / ((|ci|+|cj|)^(1+2*f(theta)))
		# f(theta) = (1-theta)/(1+theta)
		links = count_links(ci, cj, neighbors_dict)
		denom = (len(ci) + len(cj)) ** (1 + 2 * ((1-theta)/(1+theta)))
		return links / denom if denom > 0 else 0

	while len(clusters) > n_clusters:
		best_score = -1
		best_pair = None
		# Buscar el par de clusters con mayor "goodness"
		for i in range(len(clusters)):
			for j in range(i+1, len(clusters)):
				score = goodness(clusters[i], clusters[j])
				if score > best_score:
					best_score = score
					best_pair = (i, j)
		if best_pair is None or best_score == 0:
			break  # No se pueden fusionar más clusters
		# Fusionar los dos clusters con mayor goodness
		i, j = best_pair
		clusters[i] = clusters[i].union(clusters[j])
		del clusters[j]
		print(f"Clusters restantes: {len(clusters)} (última fusión score={best_score:.4f})")
	# Asignar cluster a cada usuario
	user_to_cluster = {}
	for idx, cluster in enumerate(clusters):
		for u in cluster:
			user_to_cluster[u] = idx
	return user_to_cluster

if __name__ == "__main__":
	# 1. Cargar los vectores multihot de usuario
	df = pd.read_csv('data/processed/user_vectors.csv')
	user_ids = df.iloc[:, 0].tolist()
	X = df.iloc[:, 1:].values.tolist()

	for n_clusters in N_CLUSTERS_RANGE:
		print(f"\n--- ROCK (pyclustering) con {n_clusters} clusters ---")
		# Crear instancia de ROCK
		rock_instance = rock(X, n_clusters, THETA)
		rock_instance.process()
		clusters = rock_instance.get_clusters()
		# Mapear usuario a cluster
		user_to_cluster = {}
		for idx, cluster in enumerate(clusters):
			for i in cluster:
				user_to_cluster[user_ids[i]] = idx
		result_df = pd.DataFrame({
			'Usuario': list(user_to_cluster.keys()),
			'cluster': list(user_to_cluster.values())
		})
		out_path = f'data/processed/user_vectors_with_clusters_ROCK_{n_clusters}.csv'
		result_df.to_csv(out_path, index=False)
		print(f"Guardado: {out_path}")
	print("Clustering ROCK (pyclustering) terminado para todos los valores de clusters.")
