import pandas as pd
import ast



if __name__ == "__main__":
    multihot_df = create_user_multihot_vectors('data/processed/split_roles.csv')
    print(multihot_df.head())
    # Si quieres guardar el resultado:
    multihot_df.to_csv('data/processed/user_multihot_vectors.csv')