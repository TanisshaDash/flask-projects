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

@app.route('/')
def index():
    df = pd.read_csv('static/data/global_crime_data.csv')
    df = df[(df['Year'] >= 2019) & (df['Year'] <= 2024)]
    
    countries = sorted(df['Country'].dropna().unique().tolist())
    return render_template('index.html', countries=countries)

@app.route('/stats')
def stats():
    df = pd.read_csv('static/data/global_crime_data.csv')

    # Filter to 2019–2024
    filtered_df = df[df['Year'].between(2019, 2024)]

    chart_data = {}

    for internal, label in DISPLAY_LABELS.items():
        if internal in filtered_df.columns:
            # Group by Year and sum values
            grouped = filtered_df.groupby('Year')[internal].sum().reset_index()
            years = grouped['Year'].tolist()
            values = grouped[internal].tolist()

            # Filter: only include if at least 2 meaningful (non-zero) values
            non_zero_values = [v for v in values if v > 0]
            if len(non_zero_values) >= 2:
                chart_data[label] = {
                    'years': years,
                    'values': values
                }

    print("📊 Charts JSON Preview:\n", json.dumps(chart_data, indent=2))
    return render_template('stats.html', charts=chart_data, charts_json=json.dumps(chart_data))


@app.route('/country/<country_name>')
def country_stats(country_name):
    df = pd.read_csv('static/data/global_crime_data.csv')
    df = df[(df['Year'] >= 2019) & (df['Year'] <= 2024)]
    df = df[df['Country'] == country_name]

    chart_data = {}

    for internal, label in DISPLAY_LABELS.items():
        if internal in df.columns:
            year_group = df[['Year', internal]].dropna().groupby('Year').sum()
            chart_data[label] = {
                'years': year_group.index.tolist(),
                'values': year_group[internal].tolist()
            }
            print("📊 Charts JSON Preview:\n", json.dumps(chart_data, indent=2))

    return render_template('stats.html', country=country_name, charts=chart_data, charts_json=json.dumps(chart_data))


if __name__ == '__main__':
    app.run(debug=True) 

