
import pandas as pd
from user_vector import createUsersVector
import utils.utils as ut
from sklearn.metrics.pairwise import cosine_similarity
import concurrent.futures

def evaluate_combination(args):
    # Desempaqueta los argumentos
    (params, base_uv_df, department_cols, function_cols, roleloc_cols, roles_cols, resumen_df, split_df) = args
    import pandas as pd
    from sklearn.metrics.pairwise import cosine_similarity
    import utils.utils as ut
    department_weight, role_weight, area_weight, subarea_weight, neighbors = params
    uv_df = base_uv_df.copy()
    uv_df[department_cols] = uv_df[department_cols] * department_weight
    uv_df[function_cols] = uv_df[function_cols] * role_weight
    uv_df[roleloc_cols] = uv_df[roleloc_cols] * area_weight
    uv_df[roles_cols] = uv_df[roles_cols] * subarea_weight

    sim_matrix = cosine_similarity(uv_df.values)
    sim_df = pd.DataFrame(sim_matrix, index=uv_df.index, columns=uv_df.index)
    result = ut.roles_found(sim_df, resumen_df, split_df, k=neighbors, threshold=0.7)
    if result:
        print(f"total_roles {result[0]}, found_roles {result[1]}, score {result[2]} | params: {params}")
        return {
            "department_weight": department_weight,
            "role_weight": role_weight,
            "area_weight": area_weight,
            "subarea_weight": subarea_weight,
            "neighbors": neighbors,
            "total_roles": result[0],
            "found_roles": result[1],
            "score": result[2]
        }
    else:
        return None

def grid_search():
    best_params = None
    best_score = float("-inf")
    resumen_path = 'data/processed/resumen_2025.csv'
    resumen_df = pd.read_csv(resumen_path)

    user_addr_df, agr_users_df, agr_1251_df = ut.load_data(".csv")
    if user_addr_df is None or agr_users_df is None or agr_1251_df is None:
        print("Error loading data.")
        return

    merged_df = ut.merge_df(user_addr_df, agr_users_df, agr_1251_df)
    split_df = ut.split_merge_df(merged_df)

    # Calcula una sola vez el vector multi-hot base (todos los pesos en 1)
    base_uv_df = ut.create_user_multihot_vectors(split_df, 1, 1, 1, 1)

    # Identifica las columnas de cada tipo
    department_cols = [col for col in base_uv_df.columns if col.startswith('Departamento')]
    function_cols = [col for col in base_uv_df.columns if col.startswith('Función')]
    roleloc_cols = [col for col in base_uv_df.columns if col.startswith('pair_')]
    roles_cols = [col for col in base_uv_df.columns if col.startswith('role_')]

    weight_combinations = [0, 0.1, 0.5, 1, 2, 5]
    neighbor_options = [10, 50, 100, -1]

    # Prepara todas las combinaciones de hiperparámetros
    from itertools import product
    param_grid = list(product(weight_combinations, weight_combinations, weight_combinations, weight_combinations, neighbor_options))

    results = []

    # Prepara los argumentos para cada proceso
    args_list = [
        (params, base_uv_df, department_cols, function_cols, roleloc_cols, roles_cols, resumen_df, split_df)
        for params in param_grid
    ]

    # Paraleliza la evaluación de combinaciones
    import os
    max_workers = min(8, os.cpu_count() or 1)  # Puedes ajustar este valor
    import concurrent.futures
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        for res in executor.map(evaluate_combination, args_list):
            if res:
                results.append(res)

    # Encuentra el mejor resultado
    for res in results:
        if res["score"] > best_score:
            best_score = res["score"]
            best_params = (res["department_weight"], res["role_weight"], res["area_weight"], res["subarea_weight"], res["neighbors"])

    # Guarda los resultados en un CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv('data/processed/grid_search_results.csv', index=False)

    print(f"Best parameters: {best_params} with score: {best_score}")

if __name__ == "__main__":
    grid_search()