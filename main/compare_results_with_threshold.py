
import pandas as pd
import numpy as np

if __name__ == "__main__":
	# Cambia la ruta si tu archivo tiene otro nombre
	csv_path = 'data/result/result_0.1_0.5_0.1_2_-1_thresh.csv'
	df = pd.read_csv(csv_path)

	# Selecciona solo columnas numéricas (excluye Usuario si es string)
	numeric_cols = df.select_dtypes(include=[np.number]).columns


	for col in numeric_cols:
		avg = df[col].mean()
		max_val = df[col].max()
		min_val = df[col].min()
		print(f"Columna: {col}")
		print(f"  Promedio: {avg}")
		print(f"  Máximo: {max_val}")
		print(f"  Mínimo: {min_val}\n")

	# Calcular diferencia porcentual de la media entre thresholds para R_S_ y R_E_
	import re
	def get_sorted_cols(prefix):
		# Extrae el número del nombre de columna y ordena
		cols = [col for col in df.columns if col.startswith(prefix)]
		cols_sorted = sorted(cols, key=lambda x: float(re.findall(r"[\d.]+", x)[0]))
		return cols_sorted

	for prefix in ["R_S_", "R_E_"]:
		cols_sorted = get_sorted_cols(prefix)
		print(f"\nDiferencia porcentual de la media entre thresholds para columnas {prefix}:")
		prev_mean = None
		prev_thresh = None
		for col in cols_sorted:
			mean = df[col].mean()
			thresh = float(re.findall(r"[\d.]+", col)[0])
			if prev_mean is not None:
				diff_pct = 100 * (mean - prev_mean) / prev_mean if prev_mean != 0 else float('inf')
				print(f"  {prev_thresh:.2f} ({prev_mean:.2f}) -> {thresh:.2f} ({mean:.2f}): {diff_pct:.2f}%")
			prev_mean = mean
			prev_thresh = thresh
