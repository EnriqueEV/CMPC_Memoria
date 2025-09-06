import pandas as pd
from pathlib import Path
import numpy as np
import sys
from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer
sys.path.append(str(Path(__file__).parent.parent))

import utils.utils as ut

#Antes de empezar a ejecutar el codigo, es mejor pasar los archivos a formato CSV dado a que es mucho mas rapido la carga de este formato

# En caso de que se quiera guardar los dataframes generados en el proceso (recordar crear carpeta processed en data)

def createUsersVector(save,department_weight=1, role_weight=1, area_weight=1, subarea_weight=1):
    user_addr_df, agr_users_df, agr_1251_df = ut.load_data(".csv")
    
    if user_addr_df is None or agr_users_df is None or agr_1251_df is None:
        print("Error loading data.")
        return



    merged_df = ut.merge_df(user_addr_df, agr_users_df, agr_1251_df)
    #print(merged_df.head())
    split_df = ut.split_merge_df(merged_df)
    #print(split_df.head())
    user_vector_df = ut.create_user_multihot_vectors(split_df, department_weight, role_weight, area_weight, subarea_weight)
    #print(user_vector_df.head())

    if merged_df is not None and save:
        merged_df.to_csv("data/processed/merged_data.csv", index=False)
    if split_df is not None and save:
        split_df.to_csv("data/processed/split_roles.csv", index=False)

    if user_vector_df is not None and save:
        user_vector_df.to_csv("data/processed/user_vectors.csv")

    return user_vector_df
    


if __name__ == "__main__":
    createUsersVector()
