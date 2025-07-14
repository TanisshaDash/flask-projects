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

DATA_PATH = 'static/data/global_crime_data.csv'

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
    return render_template('stats.html', charts=chart_data, charts_json=(chart_data))

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
