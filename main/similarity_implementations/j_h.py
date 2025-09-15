

# Jaccard coefficient and Hamming distance implementation for user multihot vectors
import numpy as np
import pandas as pd
import os

def jaccard_coefficient(u, v):
	"""
	Calcula el coeficiente de Jaccard entre dos vectores binarios (multihot).
	"""
	intersection = np.logical_and(u, v).sum()
	union = np.logical_or(u, v).sum()
	if union == 0:
		return 0.0
	return intersection / union

def hamming_distance(u, v):
	"""
	Calcula la distancia de Hamming entre dos vectores binarios (multihot).
	"""
	return np.sum(u != v)

def user_similarity_jaccard_hamming(user_vectors: pd.DataFrame):
	"""
	Calcula la matriz de similitud entre usuarios usando (Jaccard / Hamming).
	user_vectors: DataFrame con columna 'Usuario' y columnas multihot (solo numéricas).
	Retorna: DataFrame de similitud (usuarios x usuarios), índices y columnas con nombres de usuario.
	"""
	usuarios = user_vectors['Usuario'].tolist() if 'Usuario' in user_vectors.columns else list(user_vectors.index)
	# Excluir la columna 'Usuario' para el cálculo
	X = user_vectors.drop(columns=['Usuario'], errors='ignore').select_dtypes(include=[np.number]).values
	n = X.shape[0]
	sim_matrix = np.zeros((n, n))
	for i in range(n):
		for j in range(n):
			jac = jaccard_coefficient(X[i], X[j])
			ham = hamming_distance(X[i], X[j])
			sim_matrix[i, j] = jac / ham if ham != 0 else 0.0
	return pd.DataFrame(sim_matrix, index=usuarios, columns=usuarios)


if __name__ == "__main__":
	user_vectors = pd.read_csv('data/processed/user_vectors.csv')
	print("Calculando matriz de similitud (Jaccard/Hamming)...")
	sim_df = user_similarity_jaccard_hamming(user_vectors)
	sim_df_reset = sim_df.reset_index().rename(columns={'index': 'Usuario'})
	sim_df_reset.to_csv('data/processed/user_similarity_jaccard_hamming.csv', index=False)
	print("Matriz de similitud guardada en data/processed/user_similarity_jaccard_hamming.csv")