import ast
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import utils.utils as ut
from sklearn.metrics.pairwise import cosine_similarity

def evaluate_combination(uv_df, resumen_df, split_df, k=5, threshold=0.7,fecha_min='2025-01-01'):
    """
    Calcula la matriz de similitud y verifica usuarios encontrados usando roles_found.
    """
    sim_matrix = cosine_similarity(uv_df.values)
    sim_df = pd.DataFrame(sim_matrix, index=uv_df.index, columns=uv_df.index)
    result = ut.roles_found(sim_df, resumen_df, split_df, k=k, threshold=threshold, fecha_min=fecha_min)
    if result:
        print(f"total_roles {result[0]}, found_roles {result[1]}, score {result[2]}")
        return {
            "total_roles": result[0],
            "found_roles": result[1],
            "score": result[2],
            "detalle": result[3]
        }
    else:
        return None

def main():
    split_df_path = 'data/processed/split_roles.csv'
    resumen_df_path = 'data/processed/resumen_2025.csv'
    split_df = pd.read_csv(split_df_path)
    split_df['Rol'] = split_df['Rol'].apply(ast.literal_eval)
    split_df['Location'] = split_df['Location'].apply(ast.literal_eval)

    resumen_df = pd.read_csv(resumen_df_path)
    dep_weight = 1
    fun_weight = 1   
    rolLoc_weight = 1
    role_weight = 1

    base_uv_df = ut.create_user_multihot_vectors(split_df, dep_weight, fun_weight, rolLoc_weight, role_weight)
    results = evaluate_combination(base_uv_df, resumen_df, split_df, k=-1, threshold=0.7,fecha_min='2025-06-01')
    user_results = {}
    for i in results["detalle"]:
        usuario = i[0]
        if usuario not in user_results:
            user_results[usuario] = {
                'Usuario': usuario,
                'Roles_Asignados': i[1]
            }
        user_results[usuario][f'Roles_similares'] = i[2]
        user_results[usuario][f'Roles_encontrados'] = i[3]

    df_result = pd.DataFrame(list(user_results.values()))
    # Ordena columnas: Usuario, Roles_Asignados, luego por threshold
    cols = ['Usuario', 'Roles_Asignados']
    cols.append(f'Roles_similares')
    cols.append(f'Roles_encontrados')
    df_result = df_result[cols]
    df_result.to_csv(f'data/result/result_V2_{dep_weight}_{fun_weight}_{rolLoc_weight}_{role_weight}_{-1}_thresh.csv', index=False)
if __name__ == "__main__":
    main()

