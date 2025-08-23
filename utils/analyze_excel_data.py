import pandas as pd
import os
from pathlib import Path

def analyze_excel_files():
    """Analyze Excel files in the data folder and extract requested information."""
    
    data_folder = Path("data")
    
    if not data_folder.exists():
        print(f"Data folder '{data_folder}' not found!")
        return
    
    results = {}
    
    # Define files and columns to analyze
    files_config = {
        "USER_ADDR_IDAD3": ["Usuario", "Departamento", "Función"],
        "TSTCT": ["CódT"],
        "AGR_1251": ["Rol", "Valor de la autorización"],
        "AGR_USERS": ["Rol", "Usuario"]
    }
    
    for file_prefix, columns in files_config.items():
        # Find Excel file with matching prefix
        excel_files = list(data_folder.glob(f"{file_prefix}*.xlsx"))
        
        if not excel_files:
            print(f"No Excel file found for {file_prefix}")
            continue
        
        file_path = excel_files[0]  # Take first matching file
        print(f"\nAnalyzing: {file_path}")
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            file_results = {}
            
            for column in columns:
                if column in df.columns:
                    unique_count = df[column].nunique()
                    unique_values = df[column].unique()
                    
                    file_results[column] = {
                        "unique_count": unique_count,
                        "sample_values": list(unique_values[:10])  # Show first 10 unique values
                    }
                    
                    print(f"  {column}: {unique_count} unique values")
                else:
                    print(f"  Column '{column}' not found in {file_path}")
                    file_results[column] = "Column not found"
            
            # Special handling for AGR_USERS (Users per Rol)
            if file_prefix == "AGR_USERS" and "Rol" in df.columns and "Usuario" in df.columns:
                users_per_rol = df.groupby("Rol")["Usuario"].nunique().to_dict()
                file_results["Users_per_Rol"] = users_per_rol
                
                # Group roles by first part (before first dash) and sum users
                rol_groups = {}
                for rol, user_count in users_per_rol.items():
                    rol_prefix = rol.split('-')[0] if '-' in str(rol) else str(rol)
                    if rol_prefix in rol_groups:
                        rol_groups[rol_prefix] += user_count
                    else:
                        rol_groups[rol_prefix] = user_count
                
                # Save grouped users per rol to CSV
                users_per_rol_df = pd.DataFrame(list(rol_groups.items()), 
                                               columns=['Rol_Group', 'Number_of_Users'])
                csv_path = data_folder / "AGR_USERS_summary.csv"
                users_per_rol_df.to_csv(csv_path, index=False)
                print(f"  Users per Rol Group saved to: {csv_path}")
                print(f"  Total rol groups: {len(rol_groups)}")
            
            results[file_prefix] = file_results
            
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            results[file_prefix] = f"Error: {str(e)}"
    
    return results

def print_summary(results):
    """Print a summary of all results."""
    print("\n" + "="*60)
    print("SUMMARY OF ANALYSIS")
    print("="*60)
    
    for file_name, file_data in results.items():
        print(f"\n{file_name}:")
        if isinstance(file_data, dict):
            for column, data in file_data.items():
                if isinstance(data, dict) and "unique_count" in data:
                    print(f"  - {column}: {data['unique_count']} unique values")
                elif column == "Users_per_Rol":
                    print(f"  - {column}: {len(data)} different roles (original count)")
                else:
                    print(f"  - {column}: {data}")
        else:
            print(f"  {file_data}")

if __name__ == "__main__":
    print("Starting Excel files analysis...")
    results = analyze_excel_files()
    print_summary(results)
    print("\nAnalysis completed!")
