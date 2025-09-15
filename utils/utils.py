# --- MÉTRICAS DE EVALUACIÓN: PRECISION, RECALL, F1 ---

import pandas as pd
import numpy as np
from pathlib import Path

from sklearn import neighbors
from config.constants import USER_ADDR_COLUMNS, AGR_USERS_COLUMNS, AGR_1251_COLUMNS
from sklearn.preprocessing import MultiLabelBinarizer
from ast import literal_eval

def load_data(file_type = ".csv"):
    data_folder = Path("data")
    
    if not data_folder.exists():
        print(f"Data folder '{data_folder}' not found!")
        return None, None, None
    
    user_files = list(data_folder.glob("USER_ADDR_IDAD3*"+file_type))
    
    if not user_files:
        print("No USER_ADDR_IDAD3 Excel file found!")
        return None, None, None

    agr_users_files = list(data_folder.glob("AGR_USERS*"+file_type))
    if not agr_users_files:
        print("No AGR_USERS Excel file found!")
        return None, None, None
    
    agr_1251_files = list(data_folder.glob("AGR_1251*"+file_type))
    if not agr_1251_files:
        print("No AGR_1251 Excel file found!")
        return None, None, None

    try:
        # Read the Excel files
        file_path = user_files[0]
        print(f"Reading file: {file_path}")
        if file_type == ".csv":

            user_addr_df = pd.read_csv(file_path)
            
            agr_users_df = pd.read_csv(agr_users_files[0])
            agr_1251_df = pd.read_csv(agr_1251_files[0])
        else:
            user_addr_df = pd.read_excel(file_path)
            agr_users_df = pd.read_excel(agr_users_files[0])
            agr_1251_df = pd.read_excel(agr_1251_files[0])  

        #Check if the required columns are present and delete the not necessary columns
        
        missing_columns = [col for col in USER_ADDR_COLUMNS if col not in user_addr_df.columns]
        if missing_columns:
            print(f"Missing columns in USER_ADDR file: {missing_columns}")
            return None, None, None
        else:
            user_addr_df = user_addr_df[USER_ADDR_COLUMNS]

        missing_columns = [col for col in AGR_USERS_COLUMNS if col not in agr_users_df.columns]
        if missing_columns:
            print(f"Missing columns in AGR_USERS file: {missing_columns}")
            return None, None, None
        else:
            agr_users_df = agr_users_df[AGR_USERS_COLUMNS]

        missing_columns = [col for col in AGR_1251_COLUMNS if col not in agr_1251_df.columns]
        if missing_columns:
            print(f"Missing columns in AGR_1251 file: {missing_columns}")
            return None, None, None
        else:
            agr_1251_df = agr_1251_df[AGR_1251_COLUMNS]

        return user_addr_df, agr_users_df, agr_1251_df


    except Exception as e:
        print(f"Error processing file: {str(e)}")


def merge_df(user_addr_df, agr_users_df):
    """Merge the three DataFrames on the USER_ID column."""
    role_column = 'Rol'
    if role_column in agr_users_df.columns:
        roles_grouped = agr_users_df.groupby('Usuario')[role_column].apply(list).reset_index()
        roles_grouped.rename(columns={role_column: 'Roles'}, inplace=True)   
        merged_df = pd.merge(user_addr_df, roles_grouped, on='Usuario', how='left')

        return merged_df
    else:

        return None
    return merged_df


def split_merge_df(merged_df):
    """
    Split the 'Roles' column into 'Rol' and 'Location' columns.
    Example: 'ROL_NAME-XYZ' -> Rol: 'ROL_NAME', Location: 'XYZ'
    """
    rol_list = []
    location_list = []
    for idx, row in merged_df.iterrows():
        roles = row['Roles']
        temp_rol = []
        temp_location = []
        for rol in roles:
            rol_name = rol.split('-')[0] if '_' in rol else None
            location = rol.split('-')[-1] if '_' in rol else None
            if location == None or rol_name == None:
                continue
            elif "514" in location or "504" in location:
                temp_rol.append(rol_name)
                if ":" in location:
                    location = location.split(":")[-1]
                temp_location.append(location)
        rol_list.append(temp_rol)
        location_list.append(temp_location)
    merged_df['Rol'] = rol_list
    merged_df['Location'] = location_list
    merged_df = merged_df.drop(columns=['Roles'])
    return merged_df

def create_user_multihot_vectors(df, department_weight=1, function_weight=1, roleloc_weight=1, roles_weight=1):
    # Asegura que Usuario sea el índice para todos los DataFrames
    df = df.set_index('Usuario')

    # One-hot encoding para Departamento y Función
    department_df = pd.get_dummies(df[['Departamento']])
    function_df = pd.get_dummies(df[['Función']])

    # 1. Generar los pares (rol, location) por índice
    def build_roleloc_pairs(row):
        return [f"{r}_{l}" for r, l in zip(row['Rol'], row['Location']) if pd.notnull(r) and pd.notnull(l)]
    df['RoleLocPairs'] = df.apply(build_roleloc_pairs, axis=1)

    # 2. Multi-hot para los pares (rol, location)
    mlb_roleloc = MultiLabelBinarizer()
    roleloc_multihot = mlb_roleloc.fit_transform(df['RoleLocPairs'])
    roleloc_df = pd.DataFrame(roleloc_multihot, columns=[f"pair_{c}" for c in mlb_roleloc.classes_], index=df.index)

    # 3. Multi-hot solo para los roles
    mlb_roles = MultiLabelBinarizer()
    roles_multihot = mlb_roles.fit_transform(df['Rol'])
    roles_df = pd.DataFrame(roles_multihot, columns=[f"role_{c}" for c in mlb_roles.classes_], index=df.index)


    # Concatenar usando el mismo índice (Usuario)
    final_multihot = pd.concat([
        department_weight * department_df,
        function_weight * function_df,
        roleloc_weight * roleloc_df,
        roles_weight * roles_df
    ], axis=1)

    return final_multihot


def roles_found(sim_df, resumen_df, split_roles, fecha_min='2025-06-01', k=5, threshold=None):
    # Asegura que la columna 'Rol' de split_roles es lista
    split_roles['Rol'] = split_roles['Rol']
    
    # Filtra resumen_df por fecha
    resumen_df = resumen_df[resumen_df['Fecha'] >= fecha_min]
    
    # Usuarios válidos: que estén en ambos
    usuarios_validos = set(split_roles['Usuario']) & set(resumen_df['Usuario'])
    
    # Prepara un dict: usuario -> set(roles posibles)
    roles_usuario = dict(zip(split_roles['Usuario'], split_roles['Rol']))
    
    total_roles = 0
    roles_encontrados = 0
    roles_per_user = []
    
    for idx, row in sim_df.iterrows():
        if idx not in usuarios_validos:
            continue

        # Roles asignados a este usuario (en resumen_df, desde fecha_min)
        roles_asignados = set(resumen_df[resumen_df['Usuario'] == idx]['Rol'])
        roles_asignados = {r.split("-")[0] for r in roles_asignados}
        if not roles_asignados:
            continue

        # Usuarios similares (asume fila de sim_df es vector de similitud)
        sim_scores = sim_df.loc[idx].drop(idx)
        # Filtra por threshold si se especifica
        if threshold is not None:
            sim_scores = sim_scores[sim_scores >= threshold]
        # Selecciona hasta k más similares (si hay suficientes)
        if k != -1:
            top_similar = sim_scores.sort_values(ascending=False).head(k)
        else:
            top_similar = sim_scores.sort_values(ascending=False)
        # Junta todos los roles de los similares
        roles_similares = set()
        for sim_user in top_similar.index:
            top_list = roles_usuario.get(sim_user, [])
            roles_similares.update(top_list)

        # Para cada rol asignado, verifica si está en los roles de los similares
        roles_encontrados_user = 0
        for rol in roles_asignados:
            total_roles += 1
            if rol in roles_similares:
                roles_encontrados += 1
                roles_encontrados_user += 1
        roles_per_user.append((idx, len(roles_asignados), len(roles_similares), roles_encontrados_user))

    porcentaje = (roles_encontrados / total_roles) * 100 if total_roles > 0 else 0
    return total_roles, roles_encontrados, porcentaje, roles_per_user


