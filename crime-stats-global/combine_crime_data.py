import pandas as pd

def clean_csv(filepath, new_value_column_name):
    print(f"📄 Reading: {filepath}")
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()  # ✅ Strips whitespace from column names
    print("🧩 Columns:", df.columns.tolist())

    expected = ['Country', 'Year', 'VALUE']
    if not all(col in df.columns for col in expected):
        print(f"❌ Required columns not found in {filepath}")
        return pd.DataFrame()

    df = df[expected].copy()
    df.columns = ['Country', 'Year', new_value_column_name]
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df[new_value_column_name] = pd.to_numeric(df[new_value_column_name], errors='coerce')
    return df.dropna()


def generate_merged_crime_data():
    corruption_df = clean_csv("data_cts_corruption_and_economic_crime 6.csv", "Corruption_Economic_Crime")
    homicide_df = clean_csv("data_cts_intentional_homicide.csv", "Intentional_Homicide")
    firearms_df = clean_csv("data_iafq_firearms_trafficking.csv", "Firearms_Trafficking")
    justice_df = clean_csv("data_cts_access_and_functioning_of_justice 1.csv", "Access_Justice")
    sexualcrime_df = clean_csv("data_cts_violent_and_sexual_crime.csv", "Violent_Sexual_Crime")

    merged_df = corruption_df \
        .merge(homicide_df, on=["Country", "Year"], how="outer") \
        .merge(firearms_df, on=["Country", "Year"], how="outer") \
        .merge(justice_df, on=["Country", "Year"], how="outer") \
        .merge(sexualcrime_df, on=["Country", "Year"], how="outer")

    merged_df.fillna(0, inplace=True)

    merged_df.to_csv("static/data/global_crime_data.csv", index=False)
    print("✅ Merged data saved to static/data/global_crime_data.csv")

if __name__ == "__main__":
    generate_merged_crime_data()
