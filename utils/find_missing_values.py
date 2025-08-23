import pandas as pd
from pathlib import Path

def find_missing_values():
    """Find missing values between TSTCT CódT and AGR_1251 Valor de la autorización."""
    
    data_folder = Path("data")
    
    if not data_folder.exists():
        print(f"Data folder '{data_folder}' not found!")
        return
    
    # Find TSTCT file
    tstct_files = list(data_folder.glob("TSTCT*.xlsx"))
    if not tstct_files:
        print("No TSTCT Excel file found!")
        return
    
    # Find AGR_1251 file
    agr_files = list(data_folder.glob("AGR_1251*.xlsx"))
    if not agr_files:
        print("No AGR_1251 Excel file found!")
        return
    
    try:
        # Read TSTCT file
        print(f"Reading {tstct_files[0]}...")
        tstct_df = pd.read_excel(tstct_files[0])
        
        # Read AGR_1251 file
        print(f"Reading {agr_files[0]}...")
        agr_df = pd.read_excel(agr_files[0])
        
        # Check if columns exist
        if "CódT" not in tstct_df.columns:
            print("Column 'CódT' not found in TSTCT file!")
            return
        
        if "Valor de la autorización" not in agr_df.columns:
            print("Column 'Valor de la autorización' not found in AGR_1251 file!")
            return
        
        # Get unique values from each column (remove NaN values)
        codt_values = set(tstct_df["CódT"].dropna().unique())
        valor_auth_values = set(agr_df["Valor de la autorización"].dropna().unique())
        
        print(f"\nTotal unique CódT values: {len(codt_values)}")
        print(f"Total unique Valor de la autorización values: {len(valor_auth_values)}")
        
        # Find missing values
        missing_in_agr = codt_values - valor_auth_values  # In TSTCT but not in AGR_1251
        missing_in_tstct = valor_auth_values - codt_values  # In AGR_1251 but not in TSTCT
        common_values = codt_values & valor_auth_values  # Common values
        
        print(f"\nCommon values: {len(common_values)}")
        print(f"Values in TSTCT (CódT) but missing in AGR_1251: {len(missing_in_agr)}")
        print(f"Values in AGR_1251 (Valor de la autorización) but missing in TSTCT: {len(missing_in_tstct)}")
        
        # Save results to CSV files
        results_folder = data_folder / "missing_values_analysis"
        results_folder.mkdir(exist_ok=True)
        
        # Save missing in AGR_1251
        if missing_in_agr:
            missing_agr_df = pd.DataFrame(list(missing_in_agr), columns=["Missing_in_AGR_1251"])
            missing_agr_path = results_folder / "missing_in_AGR_1251.csv"
            missing_agr_df.to_csv(missing_agr_path, index=False)
            print(f"\nSaved values missing in AGR_1251 to: {missing_agr_path}")
        
        # Save missing in TSTCT
        if missing_in_tstct:
            missing_tstct_df = pd.DataFrame(list(missing_in_tstct), columns=["Missing_in_TSTCT"])
            missing_tstct_path = results_folder / "missing_in_TSTCT.csv"
            missing_tstct_df.to_csv(missing_tstct_path, index=False)
            print(f"Saved values missing in TSTCT to: {missing_tstct_path}")
        
        # Save common values
        if common_values:
            common_df = pd.DataFrame(list(common_values), columns=["Common_Values"])
            common_path = results_folder / "common_values.csv"
            common_df.to_csv(common_path, index=False)
            print(f"Saved common values to: {common_path}")
        
        # Create summary report
        summary_data = {
            "Metric": [
                "Total CódT values (TSTCT)",
                "Total Valor de la autorización values (AGR_1251)",
                "Common values",
                "Missing in AGR_1251",
                "Missing in TSTCT"
            ],
            "Count": [
                len(codt_values),
                len(valor_auth_values),
                len(common_values),
                len(missing_in_agr),
                len(missing_in_tstct)
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_path = results_folder / "missing_values_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"Saved summary report to: {summary_path}")
        
        return {
            "codt_values": codt_values,
            "valor_auth_values": valor_auth_values,
            "missing_in_agr": missing_in_agr,
            "missing_in_tstct": missing_in_tstct,
            "common_values": common_values
        }
        
    except Exception as e:
        print(f"Error processing files: {str(e)}")
        return None

if __name__ == "__main__":
    print("Starting missing values analysis...")
    results = find_missing_values()
    if results:
        print("\nAnalysis completed successfully!")
    else:
        print("\nAnalysis failed!")
