
import pandas as pd
from kmodes.kmodes import KModes
VISUALIZE = False  


if __name__ == "__main__":

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
