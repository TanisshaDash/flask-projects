from flask import Flask, render_template, request
import pandas as pd
import json

app = Flask(__name__)

DISPLAY_LABELS = {
    'corruption_and_economic_crime': 'Corruption and Economic Crime',
    'intentional_homicide': 'Intentional Homicide',
    'violent_and_sexual_crime': 'Violent and Sexual Crime',
    'firearms_trafficking': 'Firearms Trafficking',
    'access_and_functioning_of_justice': 'Access and Functioning of Justice'
}

DATA_PATH = 'static/data/cleaned_global_crime_data.csv'

@app.route('/')
def index():
    df = pd.read_csv(DATA_PATH)
    df = df[df['Year'].between(2019, 2024)]
    countries = sorted(df['Country'].dropna().unique())
    return render_template('index.html', countries=countries)

@app.route('/stats')
def stats():
    df = pd.read_csv(DATA_PATH)
    df = df[df['Year'].between(2019, 2024)]

    chart_data = {}

    for internal, label in DISPLAY_LABELS.items():
        if internal in df.columns:
            grouped = df.groupby('Year')[internal].sum().reset_index()
            years = grouped['Year'].tolist()
            values = grouped[internal].tolist()

            if any(v > 0 for v in values):
                chart_data[label] = {
                    'years': years,
                    'values': values
                }

    print("📊 Charts JSON Preview:\n", json.dumps(chart_data, indent=2))
    return render_template('stats.html', charts=chart_data, charts_json=json.dumps(chart_data))

@app.route('/country/<country>')
def country_stats(country):
    df = pd.read_csv(DATA_PATH)
    df = df[(df['Country'] == country) & (df['Year'].between(2019, 2024))]

    chart_data = {}

    for internal_col, display_name in DISPLAY_LABELS.items():
        if internal_col in df.columns:
            yearly = df[['Year', internal_col]].dropna().groupby('Year').sum().reset_index()
            values = yearly[internal_col].tolist()
            if any(v > 0 for v in values):
                chart_data[display_name] = {
                    "years": yearly['Year'].tolist(),
                    "values": values
                }

    print("📊 Charts JSON Preview:\n", json.dumps(chart_data, indent=2))
    return render_template('stats.html', charts=chart_data, charts_json=chart_data)


if __name__ == '__main__':
    app.run(debug=True)

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