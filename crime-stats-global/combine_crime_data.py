import pandas as pd

def clean_csv(filepath, new_value_column_name):
    print(f"📄 Reading file: {filepath}")
    df = pd.read_csv(filepath)

    print("🧩 Columns found:", df.columns.tolist())
    
    df = df[['Country or Area', 'Year', 'Value']].copy()
    df.columns = ['Country', 'Year', new_value_column_name]
    df.dropna(subset=['Country', 'Year'], inplace=True)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df[new_value_column_name] = pd.to_numeric(df[new_value_column_name], errors='coerce')
    return df.dropna()

def generate_merged_crime_data():
    corruption_df = clean_csv('data_cts_corruption_and_economic_crime.csv', 'Corruption_Econ_Crime')
    homicide_df = clean_csv('data_cts_intentional_homicide.csv', 'Homicide')
    prisoners_df = clean_csv('data_cts_prisons_and_prisoners.csv', 'Prisoner_Count')
    criminals_df = clean_csv('data_cts_violent_and_sexual_crime.csv', 'Violent_Sexual_Crime')
    firearms_df = clean_csv('data_iafq_firearms_trafficking.csv', 'Firearms_Trafficking')
    charthomicide_df = clean_csv('data_portal_m49_regions_homicide.csv', 'Regional_Homicide_Rate')

    merged_df = corruption_df \
        .merge(homicide_df, on=['Country', 'Year'], how='outer') \
        .merge(prisoners_df, on=['Country', 'Year'], how='outer') \
        .merge(criminals_df, on=['Country', 'Year'], how='outer') \
        .merge(firearms_df, on=['Country', 'Year'], how='outer') \
        .merge(charthomicide_df, on=['Country', 'Year'], how='outer')

    merged_df.fillna(0, inplace=True)
    merged_df.to_csv('static/data/global_crime_data.csv', index=False)
    print("✅ Merged data saved to static/data/global_crime_data.csv")
    return merged_df

# Run it once if needed
if __name__ == '__main__':
    generate_merged_crime_data()
