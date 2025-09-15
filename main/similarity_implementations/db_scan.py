import pandas as pd
from sklearn.cluster import DBSCAN


EPS = 0.3 
MIN_SAMPLES = 5  
METRIC = 'cosine' 

if __name__ == "__main__":
	df = pd.read_csv('data/processed/user_vectors.csv')
	user_ids = df.iloc[:, 0].tolist()
	X = df.iloc[:, 1:].values

	for min_samples in range(3, 11):
		print(f"\n--- DBSCAN con min_samples={min_samples} ---")
		db = DBSCAN(eps=EPS, min_samples=min_samples, metric=METRIC, n_jobs=-1)
		clusters = db.fit_predict(X)
		n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
		print(f"Clusters encontrados: {n_clusters}")
		result_df = pd.DataFrame({
			'Usuario': user_ids,
			'cluster': clusters
		})
		out_path = f'data/processed/user_vectors_with_clusters_DBSCAN_{min_samples}.csv'
		result_df.to_csv(out_path, index=False)
		print(f"Guardado: {out_path}")
	print("Clustering DBSCAN terminado para todos los valores de min_samples (3 a 10).")
