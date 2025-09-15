import pandas as pd
import argparse
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import utils.utils as ut
import ast

K_MODES = True
COSINE_SIMILARITY = True
DBSCAN = True
JACCARD = True
DICE = True
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


from scipy.spatial.distance import pdist, squareform

THRESHOLD = [0.7,0.8,0.9]

def compute_f1_from_roles_found(roles_per_user):
    """
    Calcula precision, recall y F1-score global a partir de la salida de roles_found (o roles_found_cluster).
    roles_per_user: lista de tuplas (usuario, n_roles_asignados, n_roles_potenciales, n_roles_encontrados)
    """
    TP = sum([x[3] for x in roles_per_user])  # roles encontrados correctamente
    FN = sum([x[1] - x[3] for x in roles_per_user])  # roles reales no encontrados
    FP = sum([x[2] - x[3] for x in roles_per_user])  # roles potenciales que no eran reales
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

def evaluate_combination(uv_df, resumen_df, split_df, metric='cosine', k=5, threshold=THRESHOLD, fecha_min='2025-01-01'):
    """
    Calcula la matriz de similitud entre usuarios según la métrica y verifica usuarios encontrados usando roles_found.
    metric: 'cosine', 'jaccard', 'dice'
    """
    X = uv_df.values
    if metric == 'cosine':
        sim_matrix = cosine_similarity(X)
    # Jaccard y DICE en scipy es distancia, así que 1 - distancia
    elif metric == 'jaccard':
        sim_matrix = 1 - squareform(pdist(X, metric='jaccard'))
    elif metric == 'dice':
        sim_matrix = 1 - squareform(pdist(X, metric='dice'))
    else:
        raise ValueError(f"Métrica no soportada: {metric}")
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


def evaluate_combination_jk(sim_df, resumen_df, split_df, k=5, threshold=0.7,fecha_min='2025-01-01'):
    """
    Calcula la matriz de similitud y verifica usuarios encontrados usando roles_found.
    """
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


def roles_found_cluster(user_clusters_df, resumen_df, split_roles, fecha_min='2025-06-01'):
    """
    Evalúa cuántos roles asignados a usuarios pueden ser encontrados entre los usuarios de su mismo cluster.
    user_clusters_df: DataFrame con columnas ['Usuario', 'cluster']
    resumen_df: DataFrame con columnas ['Usuario', 'Rol', 'Fecha']
    split_roles: DataFrame con columnas ['Usuario', 'Rol'] (Rol debe ser lista)
    """
    split_roles['Rol'] = split_roles['Rol']
    resumen_df = resumen_df[resumen_df['Fecha'] >= fecha_min]
    usuarios_validos = set(split_roles['Usuario']) & set(resumen_df['Usuario'])
    roles_usuario = dict(zip(split_roles['Usuario'], split_roles['Rol']))
    cluster_usuario = dict(zip(user_clusters_df['Usuario'], user_clusters_df['cluster']))
    cluster_to_users = user_clusters_df.groupby('cluster')['Usuario'].apply(list).to_dict()

    total_roles = 0
    roles_encontrados = 0
    user_stats = {}
    roles_asignados_por_usuario = resumen_df.groupby('Usuario')['Rol'].apply(list).to_dict()

    for usuario in usuarios_validos:
        roles_asignados = roles_asignados_por_usuario.get(usuario, [])
        roles_asignados = [r.split('-')[0] for r in roles_asignados if isinstance(r, str)]
        if not roles_asignados:
            continue
        cluster = cluster_usuario.get(usuario, None)
        if cluster is None:
            continue
        usuarios_cluster = cluster_to_users.get(cluster, [])
        usuarios_cluster = [u for u in usuarios_cluster if u != usuario]
        roles_similares = set()
        for sim_user in usuarios_cluster:
            top_list = roles_usuario.get(sim_user, [])
            roles_similares.update(top_list)
        encontrados = 0
        for rol in set(roles_asignados):
            total_roles += 1
            if rol in roles_similares:
                roles_encontrados += 1
                encontrados += 1
        user_stats[usuario] = {
            'usuario': usuario,
            'roles_asignados': len(set(roles_asignados)),
            'roles_potenciales_cluster': len(roles_similares),
            'roles_asignados_encontrados': encontrados
        }

    porcentaje = (roles_encontrados / total_roles) * 100 if total_roles > 0 else 0
    df_stats = pd.DataFrame(list(user_stats.values()))
    total_potenciales = df_stats['roles_potenciales_cluster'].sum()
    promedio_potenciales = df_stats['roles_potenciales_cluster'].mean() if not df_stats.empty else 0
    all_data = []
    for data in user_stats.values():
        all_data.append((data['usuario'], data['roles_asignados'], data['roles_potenciales_cluster'], data['roles_asignados_encontrados']))
    precision, recall, f1 = compute_f1_from_roles_found(all_data)
    return total_roles, roles_encontrados, porcentaje, df_stats, total_potenciales, promedio_potenciales, precision, recall, f1

def roles_found_cosine_stats(user_results_df):
    total_potenciales = user_results_df['Roles_similares'].sum()
    promedio_potenciales = user_results_df['Roles_similares'].mean() if not user_results_df.empty else 0
    return total_potenciales, promedio_potenciales



if __name__ == "__main__":
    split_roles = pd.read_csv('data/processed/split_roles.csv')

    split_roles['Rol'] = split_roles['Rol'].apply(ast.literal_eval)
    split_roles['Location'] = split_roles['Location'].apply(ast.literal_eval)

        # --- Acumulador de resultados finales ---
    resultados_finales = []

    if K_MODES:
        resumen_df = pd.read_csv('data/processed/resumen_2025.csv')
        for i in range(3,11):
            print(f"--- Evaluando K-modes con {i} clusters ---")
            user_vectors_with_clusters = pd.read_csv(f'data/processed/user_vectors_with_clusters_{i}.csv')
            total, encontrados, porcentaje, df_stats, total_potenciales, promedio_potenciales, precision, recall, f1 = roles_found_cluster(user_vectors_with_clusters, resumen_df, split_roles)
            print(f"Total de roles asignados después de 2025-06-01: {total}")
            print(f"Roles encontrados en el cluster (K-modes): {encontrados}")
            print(f"Porcentaje de roles encontrados (K-modes): {porcentaje:.2f}%")
            print(f"Total de roles potenciales (K-modes): {total_potenciales}")
            print(f"Promedio de roles potenciales por usuario (K-modes): {promedio_potenciales:.2f}")
            df_stats.to_csv(f'data/result/roles_found_kmodes_stats_{i}.csv', index=False)
            print(f"Se guardó el detalle por usuario en data/result/roles_found_kmodes_stats_{i}.csv")
            relacion = encontrados / promedio_potenciales if promedio_potenciales != 0 else 0
            resultados_finales.append({
                        'algoritmo': f'K-modes_{i}',
                        'roles_encontrados': encontrados,
                        'porcentaje_roles_encontrados': porcentaje,
                        'promedio_roles_potenciales_por_usuario': promedio_potenciales,
                        'relacion_roles_encontrados_promedio_potenciales': relacion,
                        'precision': precision,
                        'recall': recall,
                        'f1_score': f1,
                        'promedio_roles_encontrados_por_usuario': df_stats['roles_asignados_encontrados'].mean() if not df_stats.empty else 0,
                        'std_roles_potenciales_por_usuario': df_stats['roles_potenciales_cluster'].std() if not df_stats.empty else 0,
                        'std_roles_encontrados_por_usuario': df_stats['roles_asignados_encontrados'].std() if not df_stats.empty else 0
                    })

    # --- DBSCAN evaluation and visualization ---
    if DBSCAN:
        resumen_df = pd.read_csv('data/processed/resumen_2025.csv')
        for min_samples in range(3, 11):
            print(f"--- Evaluando DBSCAN con min_samples={min_samples} ---")
            dbscan_clusters = pd.read_csv(f'data/processed/user_vectors_with_clusters_DBSCAN_{min_samples}.csv')
            # Evaluación de roles encontrados en clusters DBSCAN
            total, encontrados, porcentaje, df_stats, total_potenciales, promedio_potenciales, precision, recall, f1 = roles_found_cluster(dbscan_clusters, resumen_df, split_roles)
            print(f"Total de roles asignados después de 2025-06-01: {total}")
            print(f"Roles encontrados en el cluster (DBSCAN): {encontrados}")
            print(f"Porcentaje de roles encontrados (DBSCAN): {porcentaje:.2f}%")
            print(f"Total de roles potenciales (DBSCAN): {total_potenciales}")
            print(f"Promedio de roles potenciales por usuario (DBSCAN): {promedio_potenciales:.2f}")
            df_stats.to_csv(f'data/result/roles_found_dbscan_stats_{min_samples}.csv', index=False)
            print(f"Se guardó el detalle por usuario en data/result/roles_found_dbscan_stats_{min_samples}.csv")
            relacion = encontrados / promedio_potenciales if promedio_potenciales != 0 else 0
            
            resultados_finales.append({
                        'algoritmo': f'DBSCAN_{min_samples}',
                        'roles_encontrados': encontrados,
                        'porcentaje_roles_encontrados': porcentaje,
                        'promedio_roles_potenciales_por_usuario': promedio_potenciales,
                        'relacion_roles_encontrados_promedio_potenciales': relacion,
                        'precision': precision,
                        'recall': recall,
                        'f1_score': f1,
                        'promedio_roles_encontrados_por_usuario': df_stats['roles_asignados_encontrados'].mean() if not df_stats.empty else 0,
                        'std_roles_potenciales_por_usuario': df_stats['roles_potenciales_cluster'].std() if not df_stats.empty else 0,
                        'std_roles_encontrados_por_usuario': df_stats['roles_asignados_encontrados'].std() if not df_stats.empty else 0
                    })
            

    for threshold in THRESHOLD:

        if COSINE_SIMILARITY:
            print(f"--- Evaluando Cosine Similarity {threshold} ---")
            # Cargar los datos necesarios
            resumen_df = pd.read_csv('data/processed/resumen_2025.csv')

            dep_weight = 1
            fun_weight = 1   
            rolLoc_weight = 1
            role_weight = 1
            base_uv_df = ut.create_user_multihot_vectors(split_roles, dep_weight, fun_weight, rolLoc_weight, role_weight)
            results = evaluate_combination(base_uv_df, resumen_df, split_roles, metric='cosine', k=-1, threshold=threshold, fecha_min='2025-06-01')
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
            total_potenciales_cos, promedio_potenciales_cos = roles_found_cosine_stats(df_result)
            print(f"Total de roles potenciales (cosine jk): {total_potenciales_cos}")
            print(f"Promedio de roles potenciales por usuario (cosine jk): {promedio_potenciales_cos:.2f}")
            df_result.to_csv(f'data/result/result_F_{dep_weight}_{fun_weight}_{rolLoc_weight}_{role_weight}_{-1}_thresh.csv', index=False)
            relacion = results["found_roles"] / promedio_potenciales_cos if promedio_potenciales_cos != 0 else 0
            precision, recall, f1 = compute_f1_from_roles_found(results["detalle"])
            resultados_finales.append({
                            'algoritmo': f'cosine_similarity_{threshold}',
                            'roles_encontrados': results["found_roles"],
                            'porcentaje_roles_encontrados': results["score"],
                            'promedio_roles_potenciales_por_usuario': promedio_potenciales_cos,
                            'relacion_roles_encontrados_promedio_potenciales': relacion,
                            'precision': precision,
                            'recall': recall,
                            'f1_score': f1,
                            'promedio_roles_encontrados_por_usuario': df_result['Roles_encontrados'].mean() if not df_result.empty else 0,
                            'std_roles_potenciales_por_usuario': df_result['Roles_similares'].std() if not df_result.empty else 0,
                            'std_roles_encontrados_por_usuario': df_result['Roles_encontrados'].std() if not df_result.empty else 0
                        })
            
        if JACCARD:
            print(f"--- Evaluando Jaccard {threshold} ---")
            # Cargar los datos necesarios
            resumen_df = pd.read_csv('data/processed/resumen_2025.csv')

            dep_weight = 1
            fun_weight = 1   
            rolLoc_weight = 1
            role_weight = 1
            base_uv_df = ut.create_user_multihot_vectors(split_roles, dep_weight, fun_weight, rolLoc_weight, role_weight)
            results = evaluate_combination(base_uv_df, resumen_df, split_roles, metric='jaccard', k=-1, threshold=threshold, fecha_min='2025-06-01')
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
            total_potenciales_jac, promedio_potenciales_jac = roles_found_cosine_stats(df_result)
            print(f"Total de roles potenciales (jaccard): {total_potenciales_jac}")
            print(f"Promedio de roles potenciales por usuario (jaccard): {promedio_potenciales_jac:.2f}")
            df_result.to_csv(f'data/result/result_F_{dep_weight}_{fun_weight}_{rolLoc_weight}_{role_weight}_{-1}_thresh.csv', index=False)
            relacion = results["found_roles"] / promedio_potenciales_jac if promedio_potenciales_jac != 0 else 0
            precision, recall, f1 = compute_f1_from_roles_found(results["detalle"])

            resultados_finales.append({
                            'algoritmo': f'jaccard_{threshold}',
                            'roles_encontrados': results["found_roles"],
                            'porcentaje_roles_encontrados': results["score"],
                            'promedio_roles_potenciales_por_usuario': promedio_potenciales_jac,
                            'relacion_roles_encontrados_promedio_potenciales': relacion,
                            'precision': precision,
                            'recall': recall,
                            'f1_score': f1,
                            'promedio_roles_encontrados_por_usuario': df_result['Roles_encontrados'].mean() if not df_result.empty else 0,
                            'std_roles_potenciales_por_usuario': df_result['Roles_similares'].std() if not df_result.empty else 0,
                            'std_roles_encontrados_por_usuario': df_result['Roles_encontrados'].std() if not df_result.empty else 0
                        })
            
        if DICE:
            print(f"--- Evaluando DICE {threshold} ---")
            # Cargar los datos necesarios
            resumen_df = pd.read_csv('data/processed/resumen_2025.csv')

            dep_weight = 1
            fun_weight = 1   
            rolLoc_weight = 1
            role_weight = 1
            base_uv_df = ut.create_user_multihot_vectors(split_roles, dep_weight, fun_weight, rolLoc_weight, role_weight)
            results = evaluate_combination(base_uv_df, resumen_df, split_roles, metric='dice', k=-1, threshold=threshold, fecha_min='2025-06-01')
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
            total_potenciales_jac, promedio_potenciales_DICE = roles_found_cosine_stats(df_result)
            print(f"Total de roles potenciales (dice): {total_potenciales_jac}")
            print(f"Promedio de roles potenciales por usuario (dice): {promedio_potenciales_DICE:.2f}")
            df_result.to_csv(f'data/result/result_F_{dep_weight}_{fun_weight}_{rolLoc_weight}_{role_weight}_{-1}_thresh.csv', index=False)
            relacion = results["found_roles"] / promedio_potenciales_DICE if promedio_potenciales_DICE != 0 else 0
            precision, recall, f1 = compute_f1_from_roles_found(results["detalle"])

            resultados_finales.append({
                            'algoritmo': f'dice_{threshold}',
                            'roles_encontrados': results["found_roles"],
                            'porcentaje_roles_encontrados': results["score"],
                            'promedio_roles_potenciales_por_usuario': promedio_potenciales_DICE,
                            'relacion_roles_encontrados_promedio_potenciales': relacion,
                            'precision': precision,
                            'recall': recall,
                            'f1_score': f1,
                            'promedio_roles_encontrados_por_usuario': df_result['Roles_encontrados'].mean() if not df_result.empty else 0,
                            'std_roles_potenciales_por_usuario': df_result['Roles_similares'].std() if not df_result.empty else 0,
                            'std_roles_encontrados_por_usuario': df_result['Roles_encontrados'].std() if not df_result.empty else 0
                        })
        
        
    # --- Guardar resultados finales ---
    if 'resultados_finales' in locals() and resultados_finales:
        df_final = pd.DataFrame(resultados_finales)
        df_final.to_csv(f'data/result/resultados_finales_{THRESHOLD}.csv', index=False)
        print(f'Se guardó el resumen de resultados finales en data/result/resultados_finales_{THRESHOLD}.csv')