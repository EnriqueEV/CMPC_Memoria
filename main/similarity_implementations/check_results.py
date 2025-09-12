import pandas as pd
import argparse
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import utils.utils as ut
import ast

K_MODES = True
COSINE_SIMILARITY = True
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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



def roles_found_kmodes(user_vectors_with_clusters, resumen_df, split_roles, fecha_min='2025-06-01'):
    """
    Evalúa cuántos roles asignados a usuarios pueden ser encontrados entre los usuarios de su mismo cluster (K-modes).
    user_vectors_with_clusters: DataFrame con columnas ['Usuario', ..., 'cluster']
    resumen_df: DataFrame con columnas ['Usuario', 'Rol', 'Fecha']
    split_roles: DataFrame con columnas ['Usuario', 'Rol'] (Rol debe ser lista)
    """
    # Asegura que la columna 'Rol' de split_roles es lista
    split_roles['Rol'] = split_roles['Rol']
    # Filtra resumen_df por fecha
    resumen_df = resumen_df[resumen_df['Fecha'] >= fecha_min]
    # Usuarios válidos: que estén en ambos
    usuarios_validos = set(split_roles['Usuario']) & set(resumen_df['Usuario'])
    # Prepara un dict: usuario -> set(roles posibles)
    roles_usuario = dict(zip(split_roles['Usuario'], split_roles['Rol']))
    # Prepara dict usuario -> cluster
    cluster_usuario = dict(zip(user_vectors_with_clusters['Usuario'], user_vectors_with_clusters['cluster']))
    # Prepara cluster -> usuarios
    cluster_to_users = user_vectors_with_clusters.groupby('cluster')['Usuario'].apply(list).to_dict()

    total_roles = 0
    roles_encontrados = 0
    user_stats = {}

    # Agrupa roles asignados por usuario
    roles_asignados_por_usuario = resumen_df.groupby('Usuario')['Rol'].apply(list).to_dict()

    for usuario in usuarios_validos:
        roles_asignados = roles_asignados_por_usuario.get(usuario, [])
        roles_asignados = [r.split('-')[0] for r in roles_asignados if isinstance(r, str)]
        if not roles_asignados:
            continue
        # Usuarios en el mismo cluster (excepto el propio)
        cluster = cluster_usuario.get(usuario, None)
        if cluster is None:
            continue
        usuarios_cluster = cluster_to_users.get(cluster, [])
        usuarios_cluster = [u for u in usuarios_cluster if u != usuario]
        # Junta todos los roles de los usuarios del cluster
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
    return total_roles, roles_encontrados, porcentaje, df_stats, total_potenciales, promedio_potenciales
def roles_found_cosine_stats(user_results_df):
    total_potenciales = user_results_df['Roles_similares'].sum()
    promedio_potenciales = user_results_df['Roles_similares'].mean() if not user_results_df.empty else 0
    return total_potenciales, promedio_potenciales



if __name__ == "__main__":
    split_roles = pd.read_csv('data/processed/split_roles.csv')

    split_roles['Rol'] = split_roles['Rol'].apply(ast.literal_eval)
    split_roles['Location'] = split_roles['Location'].apply(ast.literal_eval)
    if K_MODES:
        # Cargar los datos necesarios   
        resumen_df = pd.read_csv('data/processed/resumen_2025.csv')
        for i in range(3,11):

            print(f"--- Evaluando K-modes con {i} clusters ---")
            user_vectors_with_clusters = pd.read_csv(f'data/processed/user_vectors_with_clusters_{i}.csv')
            total, encontrados, porcentaje, df_stats, total_potenciales, promedio_potenciales = roles_found_kmodes(user_vectors_with_clusters, resumen_df, split_roles)
            print(f"Total de roles asignados después de 2025-06-01: {total}")
            print(f"Roles encontrados en el cluster (K-modes): {encontrados}")
            print(f"Porcentaje de roles encontrados (K-modes): {porcentaje:.2f}%")
            print(f"Total de roles potenciales (K-modes): {total_potenciales}")
            print(f"Promedio de roles potenciales por usuario (K-modes): {promedio_potenciales:.2f}")
            # Guardar el DataFrame de estadísticas por usuario
            df_stats.to_csv(f'data/result/roles_found_kmodes_stats_{i}.csv', index=False)
            print(f"Se guardó el detalle por usuario en data/result/roles_found_kmodes_stats_{i}.csv")

    if COSINE_SIMILARITY:
        # Cargar los datos necesarios
        user_vectors = pd.read_csv('data/processed/user_vectors.csv')
        resumen_df = pd.read_csv('data/processed/resumen_2025.csv')

        dep_weight = 1
        fun_weight = 1   
        rolLoc_weight = 1
        role_weight = 1
        base_uv_df = ut.create_user_multihot_vectors(split_roles, dep_weight, fun_weight, rolLoc_weight, role_weight)
        results = evaluate_combination(base_uv_df, resumen_df, split_roles, k=-1, threshold=0.7,fecha_min='2025-06-01')
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
        print(f"Total de roles potenciales (cosine similarity): {total_potenciales_cos}")
        print(f"Promedio de roles potenciales por usuario (cosine similarity): {promedio_potenciales_cos:.2f}")
        df_result.to_csv(f'data/result/result_F_{dep_weight}_{fun_weight}_{rolLoc_weight}_{role_weight}_{-1}_thresh.csv', index=False)