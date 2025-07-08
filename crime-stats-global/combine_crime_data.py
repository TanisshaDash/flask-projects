import pandas as pd


def clean_excel(filepath, new_value_column_name):
    df = pd.read_excel(filepath, header=1)
    print(f"🔍 FILE: {filepath}")
    print("🔑 Columns:", df.columns.tolist())

    # Adjust these column names if needed based on print output
    df = df[['Country or Area', 'Year', 'Value']].copy()
    df.columns = ['Country', 'Year', new_value_column_name]

    df.dropna(subset=['Country', 'Year'], inplace=True)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df[new_value_column_name] = pd.to_numeric(df[new_value_column_name], errors='coerce')
    return df.dropna()

# 👇 Main function to combine all datasets
def generate_merged_crime_data():
    # ✅ Clean each dataset
    corruption_df = clean_excel('data_cts_corruption_and_economic_crime.xlsx', 'Corruption_Econ_Crime')
    homicide_df = clean_excel('data_cts_intentional_homicide.xlsx', 'Homicide')
    prisoners_df = clean_excel('data_cts_prisons_and_prisoners.xlsx', 'Prisoner_Count')
    criminals_df = clean_excel('data_cts_violent_and_sexual_crime.xlsx', 'Violent_Sexual_Crime')
    firearms_df = clean_excel('data_iafq_firearms_trafficking.xlsx', 'Firearms_Trafficking')
    charthomicide_df = clean_excel('data_portal_m49_regions- homicide.xlsx', 'Regional_Homicide_Rate')
    access_df = clean_excel('data_cts_access_and_functioning_of_justice.xlsx', 'Access_Justice')  

    # 🔁 Merge all on 'Country' and 'Year'
    merged_df = corruption_df \
        .merge(homicide_df, on=['Country', 'Year'], how='outer') \
        .merge(prisoners_df, on=['Country', 'Year'], how='outer') \
        .merge(criminals_df, on=['Country', 'Year'], how='outer') \
        .merge(firearms_df, on=['Country', 'Year'], how='outer') \
        .merge(charthomicide_df, on=['Country', 'Year'], how='outer') \
        .merge(access_df, on=['Country', 'Year'], how='outer')  # 🆕

    # 🧼 Fill blanks with 0
    merged_df.fillna(0, inplace=True)

    # 💾 Save
    merged_df.to_excel('static/data/merged_global_crime_data.xlsx', index=False)
    print("✅ Merged data saved to static/data/global_crime_data.csv")

    return merged_df
