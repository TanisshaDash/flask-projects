import pandas as pd

def clean_csv(filepath, new_value_column_name):
    print(f"\n📄 Reading: {filepath}")
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    print("🧩 Columns:", list(df.columns))

    required_cols = ['Country', 'Year', 'VALUE']
    if not all(col in df.columns for col in required_cols):
        print(f"❌ Required columns missing in {filepath}")
        return pd.DataFrame()

    # Clean and reduce
    df = df[['Country', 'Year', 'VALUE']].copy()
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
    df.dropna(subset=['Country', 'Year', 'VALUE'], inplace=True)

    # Group and reduce duplicates by taking average
    df = df.groupby(['Country', 'Year'], as_index=False).agg({ 'VALUE': 'mean' })
    df.columns = ['Country', 'Year', new_value_column_name]

    return df

def generate_merged_crime_data():
    corruption_df = clean_csv("data_cts_corruption_and_economic_crime 6.csv", "corruption_and_economic_crime")
    homicide_df = clean_csv("data_cts_intentional_homicide.csv", "intentional_homicide")
    firearms_df = clean_csv("data_iafq_firearms_trafficking.csv", "firearms_trafficking")
    justice_df = clean_csv("data_cts_access_and_functioning_of_justice 1.csv", "access_and_functioning_of_justice")
    sexualcrime_df = clean_csv("data_cts_violent_and_sexual_crime.csv", "violent_and_sexual_crime")

    merged_df = corruption_df \
        .merge(homicide_df, on=["Country", "Year"], how="outer") \
        .merge(firearms_df, on=["Country", "Year"], how="outer") \
        .merge(justice_df, on=["Country", "Year"], how="outer") \
        .merge(sexualcrime_df, on=["Country", "Year"], how="outer")

    merged_df.fillna(0, inplace=True)

    merged_df.to_csv("static/data/global_crime_data.csv", index=False)
    print("✅ Merged data saved to static/data/global_crime_data.csv")

# Make sure to run this script again after making the change to generate the new CSV.
if __name__ == "__main__":
    generate_merged_crime_data()
