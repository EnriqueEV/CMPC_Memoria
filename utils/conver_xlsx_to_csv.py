import pandas as pd
from pathlib import Path
def convert_xlsx_to_csv():
    """Convert all xlsx files in the data folder to csv format"""
    data_folder = Path("data")
    
    if not data_folder.exists():
        print(f"Data folder '{data_folder}' not found!")
        return
    
    # Find all xlsx files
    xlsx_files = list(data_folder.glob("*.xlsx"))
    
    if not xlsx_files:
        print("No xlsx files found in data folder!")
        return
    
    print(f"Found {len(xlsx_files)} xlsx files to convert")
    
    for xlsx_file in xlsx_files:
        try:
            # Read the xlsx file
            df = pd.read_excel(xlsx_file)
            
            # Create csv filename (same name but with .csv extension)
            csv_filename = xlsx_file.with_suffix('.csv')
            
            # Save as csv
            df.to_csv(csv_filename, index=False)
            
            print(f"Converted: {xlsx_file.name} -> {csv_filename.name}")
            
        except Exception as e:
            print(f"Error converting {xlsx_file.name}: {str(e)}")
    
    print("Conversion completed!")


if __name__ == "__main__":
    convert_xlsx_to_csv()