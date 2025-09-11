import pandas as pd
from user_vector import createUsersVector
import utils.utils as ut
from sklearn.metrics.pairwise import cosine_similarity
import concurrent.futures



if __name__ == "__main__":
    best_params = None
    best_score = float("-inf")
    resumen_path = 'data/processed/resumen_2025.csv'
    resumen_df = pd.read_csv(resumen_path)

    user_addr_df, agr_users_df, agr_1251_df = ut.load_data(".csv")
    if user_addr_df is None or agr_users_df is None or agr_1251_df is None:
        print("Error loading data.")
        exit()  
    merged_df = ut.merge_df(user_addr_df, agr_users_df, agr_1251_df)
    split_df = ut.split_merge_df(merged_df)
    dep_weight = 0.1
    fun_weight = 0.5   
    rolLoc_weight = 0.1
    role_weight = 2
    k = -1


    # Calcula una sola vez el vector multi-hot base (todos los pesos en 1)
    base_uv_df = ut.create_user_multihot_vectors(split_df, dep_weight, fun_weight, rolLoc_weight, role_weight)
    sim_matrix = cosine_similarity(base_uv_df.values)
    sim_df = pd.DataFrame(sim_matrix, index=base_uv_df.index, columns=base_uv_df.index)
    result = ut.roles_found(sim_df, resumen_df, split_df, k=k, threshold=0.8)
    print(f"Base case (all weights 1): total_roles {result[0]}, found_roles {result[1]}, score {result[2]}")

    # Prueba múltiples thresholds y guarda resultados en columnas separadas
    import numpy as np
    thresholds = np.arange(0.5, 0.95 + 0.001, 0.05)

    # Diccionario para almacenar resultados por usuario
    user_results = {}
    for threshold in thresholds:
        result = ut.roles_found(sim_df, resumen_df, split_df, k=k, threshold=round(threshold, 2))
        for i in result[3]:
            usuario = i[0]
            if usuario not in user_results:
                user_results[usuario] = {
                    'Usuario': usuario,
                    'Roles_Asignados': i[1]
                }
            user_results[usuario][f'R_S_{threshold:.2f}'] = i[2]
            user_results[usuario][f'R_E_{threshold:.2f}'] = i[3]

    # Convierte a DataFrame
    df_result = pd.DataFrame(list(user_results.values()))
    # Ordena columnas: Usuario, Roles_Asignados, luego por threshold
    cols = ['Usuario', 'Roles_Asignados']
    for threshold in thresholds:
        cols.append(f'R_S_{threshold:.2f}')
        cols.append(f'R_E_{threshold:.2f}')
    df_result = df_result[cols]
    df_result.to_csv(f'data/result/result_{dep_weight}_{fun_weight}_{rolLoc_weight}_{role_weight}_{k}_simple_run.csv', index=False)