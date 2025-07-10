import pandas as pd

def clean_csv(filepath, new_value_column_name):
    print(f"📄 Reading: {filepath}")
    df = pd.read_csv(filepath)
    print(f"🧩 Columns: {df.columns.tolist()}")

    required_cols = ['Country', 'Year', 'VALUE']
    if not all(col in df.columns for col in required_cols):
        print(f"❌ Required columns not found in {filepath}")
        return pd.DataFrame()

    df = df[['Country', 'Year', 'VALUE']].copy()
    df.columns = ['Country', 'Year', new_value_column_name]

    df.dropna(subset=['Country', 'Year'], inplace=True)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df[new_value_column_name] = pd.to_numeric(df[new_value_column_name], errors='coerce')

    return df.dropna()

def generate_merged_crime_data():
    corruption_df = clean_csv('data_cts_corruption_and_economic_crime.csv', 'Corruption_Econ_Crime')
    homicide_df = clean_csv('data_cts_intentional_homicide.csv', 'Homicide')
    prisoners_df = clean_csv('data_cts_access_and_functioning_of_justice.csv', 'Justice_Access')
    criminals_df = clean_csv('data_cts_violent_and_sexual_crime.csv', 'Violent_Sexual_Crime')
    firearms_df = clean_csv('data_iafq_firearms_trafficking.csv', 'Firearms_Trafficking')

    merged_df = corruption_df \
        .merge(homicide_df, on=['Country', 'Year'], how='outer') \
        .merge(prisoners_df, on=['Country', 'Year'], how='outer') \
        .merge(criminals_df, on=['Country', 'Year'], how='outer') \
        .merge(firearms_df, on=['Country', 'Year'], how='outer')

    merged_df.fillna(0, inplace=True)
    merged_df.to_csv('static/data/global_crime_data.csv', index=False)
    print("✅ Merged data saved to static/data/global_crime_data.csv")

if __name__ == "__main__":
    generate_merged_crime_data()
