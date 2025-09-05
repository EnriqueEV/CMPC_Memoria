import pandas as pd
import ast

df = pd.read_csv('data/processed/merged_data.csv')
df['Roles'] = df['Roles'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) else [])

rol_list = []
location_list = []

for idx, row in df.iterrows():
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

df['Rol'] = rol_list
df['Location'] = location_list
df = df.drop(columns=['Roles'])

df.to_csv("data/processed/split_roles.csv", index=False)