import pandas as pd
from pathlib import Path
from config.constants import USER_ADDR_COLUMNS, AGR_USERS_COLUMNS, AGR_1251_COLUMNS
from sklearn.preprocessing import MultiLabelBinarizer

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
            
            print(f"Reading AGR_USERS file: {agr_users_files[0]}")
            agr_users_df = pd.read_csv(agr_users_files[0])
            print(f"Reading AGR_1251 file: {agr_1251_files[0]}")
            agr_1251_df = pd.read_csv(agr_1251_files[0])
        else:
            user_addr_df = pd.read_excel(file_path)
            print(f"Reading AGR_USERS file: {agr_users_files[0]}")
            agr_users_df = pd.read_excel(agr_users_files[0])
            print(f"Reading AGR_1251 file: {agr_1251_files[0]}")
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


def merge_df(user_addr_df, agr_users_df, agr_1251_df):
    """Merge the three DataFrames on the USER_ID column."""
    role_column = 'Rol'
    if role_column in agr_users_df.columns:
        roles_grouped = agr_users_df.groupby('Usuario')[role_column].apply(list).reset_index()
        roles_grouped.rename(columns={role_column: 'Roles'}, inplace=True)   
        merged_df = pd.merge(user_addr_df, roles_grouped, on='Usuario', how='left')
        users_with_multiple_roles = merged_df[merged_df['Roles'].apply(lambda x: len(x) > 1 if isinstance(x, list) else False)]
        if not users_with_multiple_roles.empty:
            print(f"\nUsers with multiple roles ({len(users_with_multiple_roles)}):")
            for idx, row in users_with_multiple_roles.head().iterrows():
                print(f"User: {row['Usuario']}, Roles: {row['Roles']}")
        return merged_df
    else:
        print(f"Role column '{role_column}' not found in agr_users_df")
        print(f"Available columns: {list(agr_users_df.columns)}")
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

def create_user_multihot_vectors(df, department_weight=1,function_weight=1, roleloc_weight=1, roles_weight=1):
    # Cargar el DataFrame
    # Convertir las columnas de string a lista
    department_df = pd.get_dummies(df[['Departamento']])
    function_df = pd.get_dummies(df[['Función']])

    # 1. Generar los pares (rol, location) por índice
    def build_roleloc_pairs(row):
        return [f"{r}_{l}" for r, l in zip(row['Rol'], row['Location']) if pd.notnull(r) and pd.notnull(l)]
    df['RoleLocPairs'] = df.apply(build_roleloc_pairs, axis=1)

    # 2. Multi-hot para los pares (rol, location)
    mlb_roleloc = MultiLabelBinarizer()
    roleloc_multihot = mlb_roleloc.fit_transform(df['RoleLocPairs'])
    roleloc_df = pd.DataFrame(roleloc_multihot, columns=[f"pair_{c}" for c in mlb_roleloc.classes_], index=df['Usuario'])

    # 3. Multi-hot solo para los roles
    mlb_roles = MultiLabelBinarizer()
    roles_multihot = mlb_roles.fit_transform(df['Rol'])
    roles_df = pd.DataFrame(roles_multihot, columns=[f"role_{c}" for c in mlb_roles.classes_], index=df['Usuario'])

    print(f"Bits Departamento: {department_df.shape[1]}")
    print(f"Bits Función: {function_df.shape[1]}")
    print(f"Bits (Rol, Location): {roleloc_df.shape[1]}")
    print(f"Bits Roles: {roles_df.shape[1]}")
    print(f"Bits totales (sin Usuario): {department_df.shape[1] + function_df.shape[1] + roleloc_df.shape[1] + roles_df.shape[1]}")

    # 4. Concatenar ambos multi-hot
    final_multihot = pd.concat([df[['Usuario']],department_weight*department_df,function_weight*function_df, roleloc_weight*roleloc_df, roles_weight*roles_df], axis=1)

    return final_multihot