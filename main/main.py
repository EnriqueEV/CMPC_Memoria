import pandas as pd
from pathlib import Path
import numpy as np
import sys
from sklearn.preprocessing import OneHotEncoder
sys.path.append(str(Path(__file__).parent.parent))

import utils.utils as ut

#Antes de empezar a ejecutar el codigo, es mejor pasar los archivos a formato CSV dado a que es mucho mas rapido la carga de este formato

def print_diretoria_industrial_users(departamento="DIRETORIA INDUSTRIAL"):
    """Print all users from DIRETORIA INDUSTRIAL department with their usernames and functions."""

    user_addr_df, agr_users_df, agr_1251_df = ut.load_data(".csv")
    
    if user_addr_df is None or agr_users_df is None or agr_1251_df is None:
        print("Error loading data.")
        return

    print(user_addr_df.head())
    print(agr_users_df.head())
    print(agr_1251_df.head())

    merged_df = ut.merge_df(user_addr_df, agr_users_df, agr_1251_df)
    if merged_df is not None:
        print(merged_df.head())


if __name__ == "__main__":
    departamento = "CN_MANUTMECA"
    print_diretoria_industrial_users(departamento)
