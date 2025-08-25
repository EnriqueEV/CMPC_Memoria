import pandas as pd
from pathlib import Path
from config.constants import USER_ADDR_COLUMNS, AGR_USERS_COLUMNS, AGR_1251_COLUMNS

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
        # Group by Usuario and aggregate roles into a list
        roles_grouped = agr_users_df.groupby('Usuario')[role_column].apply(list).reset_index()
        roles_grouped.rename(columns={role_column: 'Roles'}, inplace=True)
        
        print(f"\nRoles grouped by user:")
        print(roles_grouped.head())
        print(f"Shape: {roles_grouped.shape}")
        
        # Merge user_addr_df with the grouped roles
        merged_df = pd.merge(user_addr_df, roles_grouped, on='Usuario', how='left')
        
        print(f"\nFinal merged DataFrame:")
        print(merged_df.head())
        print(f"Shape: {merged_df.shape}")
        
        # Show example of users with multiple roles
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