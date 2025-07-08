import pandas as pd
import os

def clean_excel(filepath, new_value_column_name):
    print(f"📄 Reading file: {filepath}")
    df = pd.read_excel(filepath, header=2)

    # Check available columns for debugging
    print("🧩 Columns found:", df.columns.tolist())

    # Use standard expected columns
    try:
        df = df[['Country or Area', 'Year', 'Value']].copy()
        df.columns = ['Country', 'Year', new_value_column_name]
        df.dropna(subset=['Country', 'Year'], inplace=True)
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df[new_value_column_name] = pd.to_numeric(df[new_value_column_name], errors='coerce')
        return df.dropna()
    except KeyError as e:
        print(f"❌ Column missing in {filepath}: {e}")
        return pd.DataFrame(columns=['Country', 'Year', new_value_column_name])

def generate_merged_crime_data():
    # 📚 Clean each Excel file
    corruption_df = clean_excel('data_cts_corruption_and_economic_crime.xlsx', 'Corruption_Econ_Crime')
    homicide_df = clean_excel('data_cts_intentional_homicide.xlsx', 'Homicide')
    criminals_df = clean_excel('data_cts_violent_and_sexual_crime.xlsx', 'Violent_Sexual_Crime')
    firearms_df = clean_excel('data_iafq_firearms_trafficking.xlsx', 'Firearms_Trafficking')
    justice_df = clean_excel('data_cts_access_and_functioning_of_justice.xlsx', 'Justice_Accessibility')

    # 🔗 Merge all on ['Country', 'Year']
    merged_df = corruption_df \
        .merge(homicide_df, on=['Country', 'Year'], how='outer') \
        .merge(criminals_df, on=['Country', 'Year'], how='outer') \
        .merge(firearms_df, on=['Country', 'Year'], how='outer') \
        .merge(justice_df, on=['Country', 'Year'], how='outer')

    # 🧼 Fill any missing values with 0
    merged_df.fillna(0, inplace=True)

    # 💾 Save as Excel
    output_path = 'static/data/merged_global_crime_data.xlsx'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_excel(output_path, index=False)

    print(f"✅ Merged dataset saved to {output_path}")
    return merged_df

# Optional: Run directly
if __name__ == '__main__':
    generate_merged_crime_data()
