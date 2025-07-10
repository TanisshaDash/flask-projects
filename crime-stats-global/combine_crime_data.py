import pandas as pd
import os

def clean_csv(filepath, new_value_column_name):
    df = pd.read_csv(filepath)
    print(f"📄 Reading: {filepath}")
    print(f"🧩 Columns: {df.columns.tolist()}")

    # Standard column detection
    if not all(col in df.columns for col in ['Country or Area', 'Year', 'Value']):
        print(f"❌ Required columns not found in {filepath}")
        return pd.DataFrame()

    df = df[['Country or Area', 'Year', 'VALUE']].copy()
    df.columns = ['Country', 'Year', new_value_column_name]
    df.dropna(subset=['Country', 'Year'], inplace=True)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df[new_value_column_name] = pd.to_numeric(df[new_value_column_name], errors='coerce')
    return df.dropna()

def generate_merged_crime_data():
    # Load and clean each CSV dataset
    corruption_df = clean_csv('data_cts_corruption_and_economic_crime.csv', 'Corruption_Econ_Crime')
    homicide_df = clean_csv('data_cts_intentional_homicide.csv', 'Homicide')
    firearms_df = clean_csv('data_iafq_firearms_trafficking.csv', 'Firearms_Trafficking')
    justice_df = clean_csv('data_cts_access_and_functioning_of_justice.csv', 'Justice_Function')
    violence_df = clean_csv('data_cts_violent_and_sexual_crime.csv', 'Violent_Sexual_Crime')

    # Merge all available datasets
    merged_df = corruption_df
    for df in [homicide_df, firearms_df, justice_df, violence_df]:
        if not df.empty:
            merged_df = merged_df.merge(df, on=['Country', 'Year'], how='outer')

    # Final cleaning
    merged_df.fillna(0, inplace=True)

    # Save merged CSV
    output_path = os.path.join("static", "data", "global_crime_data.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    print(f"✅ Merged data saved to {output_path}")

    return merged_df

# Only run if this script is executed directly
if __name__ == "__main__":
    generate_merged_crime_data()
