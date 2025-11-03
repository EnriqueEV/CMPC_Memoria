from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd




def _read_csv_robust(csv_path: Path | str) -> pd.DataFrame:
	csv_path = Path(csv_path)
	for enc in ("utf-8", "utf-8-sig", "latin-1"):
		try:
			return pd.read_csv(csv_path, encoding=enc)
		except Exception:
			continue
	# last try with default
	return pd.read_csv(csv_path)


def _parse_roles_cell(cell) -> List[str]:
	if isinstance(cell, list):
		return [str(x).strip() for x in cell]
	if not isinstance(cell, str) or not cell.strip():
		return []
	try:
		value = ast.literal_eval(cell)
		if isinstance(value, list):
			return [str(x).strip() for x in value]
		# fallback split
		return [part.strip().strip("'\"") for part in cell.split(",") if part.strip()]
	except Exception:
		return [part.strip().strip("'\"") for part in cell.split(",") if part.strip()]


@dataclass
class NegativeSamplingConfig:
	negative_ratio: int = 3  
	random_state: int = 42
	include_usuario_col: bool = False  

def build_positive_pairs(df_split: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Set[str]], Set[str]]:
	"""
	Returns:
		positives_df with columns [USUARIO, DEPARTAMETNO, FUNCION, ROL, ASIGNADO=1]
		user_roles_map: dict usuario -> set(roles)
		all_roles: set of all roles
	"""
	usuario_col = "Usuario"
	dept_col = "Departamento"
	func_col = "Función"
	role_col = "Rol"

	rows = []
	user_roles_map: Dict[str, Set[str]] = {}
	all_roles: Set[str] = set()
	for _, r in df_split[[usuario_col, dept_col, func_col, role_col]].iterrows():
		usuario = str(r[usuario_col]).strip()
		dept = str(r[dept_col]).strip()
		func = str(r[func_col]).strip()
		roles = _parse_roles_cell(r[role_col])
		for rol in roles:
			if not rol:
				continue
			rows.append({
				"USUARIO": usuario,
				"DEPARTAMETNO": dept,
				"FUNCION": func,
				"ROL": rol,
				"ASIGNADO": 1,
			})
			user_roles_map.setdefault(usuario, set()).add(rol)
			all_roles.add(rol)

    
	positives_df = pd.DataFrame(
		rows, columns=["USUARIO", "DEPARTAMETNO", "FUNCION", "ROL", "ASIGNADO"]
	)

	base = Path(__file__).parents[2]
	default_out_1 = base / "data" / "modulo_recomendacion_roles" / "positives_with_duplicates.csv"
	default_out_2 = base / "data" / "modulo_recomendacion_roles" / "positives_without_duplicates.csv"


	positives_df.to_csv(default_out_1, index=False, encoding="utf-8")
	positives_df = positives_df.drop_duplicates(subset=["USUARIO", "ROL"], keep="first")
	positives_df.to_csv(default_out_2, index=False, encoding="utf-8")

	return positives_df, user_roles_map, all_roles


def sample_uniform_negatives(
	user_roles_map: Dict[str, Set[str]],
	all_roles: Set[str],
	df_user_attrs: pd.DataFrame,
	cfg: NegativeSamplingConfig,
) -> pd.DataFrame:
	"""
	Uniformly sample negatives per user with ratio cfg.negative_ratio relative to user positives.
	Output columns: [USUARIO, DEPARTAMETNO, FUNCION, ROL, ASIGNADO=0]
	"""
	rnd = random.Random(cfg.random_state)

	usuario_col = "Usuario"
	dept_col = "Departamento"
	func_col = "Función"
	user_info = df_user_attrs[[usuario_col, dept_col, func_col]].drop_duplicates().set_index(usuario_col)

	records: List[Dict[str, object]] = []
	all_roles_list = list(all_roles)
	for user, pos_roles in user_roles_map.items():
		pos_count = len(pos_roles)
		if pos_count == 0:
			continue
		candid = [r for r in all_roles_list if r not in pos_roles]
		if not candid:
			continue
		n_neg = min(len(candid), pos_count * cfg.negative_ratio)
		negs = rnd.sample(candid, k=n_neg)

		if user in user_info.index:
			dept = str(user_info.loc[user, dept_col])
			func = str(user_info.loc[user, func_col])
		else:
			dept, func = "", ""

		for rol in negs:
			records.append({
				"USUARIO": user,
				"DEPARTAMETNO": dept,
				"FUNCION": func,
				"ROL": rol,
				"ASIGNADO": 0,
			})

	negatives_df = pd.DataFrame.from_records(
		records, columns=["USUARIO", "DEPARTAMETNO", "FUNCION", "ROL", "ASIGNADO"]
	)
	return negatives_df


def generate_training_dataset_uniform(
	input_csv_path: str | Path,
	output_csv_path: str | Path,
	negative_ratio: int = 3,
	random_state: int = 42,
	include_usuario_col: bool = False,
) -> Tuple[int, int]:
	"""
	Construye el dataset de entrenamiento con negativos UNIFORMES.
	- Lee split_roles.csv
	- Genera positivos (ASIGNADO=1) y muestrea negativos uniformes (ASIGNADO=0)
	- Guarda un CSV con columnas [DEPARTAMETNO, FUNCION, ROL, ASIGNADO] y opcional USUARIO

	Retorna: (num_positivos, num_negativos)
	"""
	df_split = _read_csv_robust(input_csv_path)
	positives_df, user_roles_map, all_roles = build_positive_pairs(df_split)

	cfg = NegativeSamplingConfig(
		negative_ratio=negative_ratio,
		random_state=random_state,
		include_usuario_col=include_usuario_col,
	)
	negatives_df = sample_uniform_negatives(user_roles_map, all_roles, df_split, cfg)

	combined = pd.concat([positives_df, negatives_df], ignore_index=True)
	if not include_usuario_col:
		combined = combined[["DEPARTAMETNO", "FUNCION", "ROL", "ASIGNADO"]]

	output_csv_path = Path(output_csv_path)
	output_csv_path.parent.mkdir(parents=True, exist_ok=True)
	combined.to_csv(output_csv_path, index=False, encoding="utf-8")
	return int((combined["ASIGNADO"] == 1).sum()), int((combined["ASIGNADO"] == 0).sum())


if __name__ == "__main__": 
	base = Path(__file__).parents[2]
	default_in = base / "data" / "processed" / "split_roles.csv"
	default_out = base / "data" / "modulo_recomendacion_roles" / "training_pairs_uniform_with_negatives.csv"
	pos, neg = generate_training_dataset_uniform(
		input_csv_path=default_in,
		output_csv_path=default_out,
		negative_ratio=3,
		random_state=42,
		include_usuario_col=False,
	)
	print(f"Generado: {pos} positivos y {neg} negativos -> {default_out}")

