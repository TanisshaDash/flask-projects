from flask import Flask, render_template, request, redirect, url_for
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

    # Calculate total crime per country
    df['total_crime'] = df[list(DISPLAY_LABELS.keys())].sum(axis=1)
    country_totals = df.groupby('Country')['total_crime'].sum().sort_values(ascending=False).reset_index()


    top_20 = country_totals.head(20).to_dict(orient='records')

    return render_template('index.html', countries=countries, top_10=top_20)

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

    return render_template('stats.html', charts=chart_data, charts_json=chart_data, country=None)

@app.route('/map')
def crime_map():
    df = pd.read_csv(DATA_PATH)
    df = df[df['Year'] == 2023]
    country_values = df.groupby("Country")["intentional_homicide"].sum().to_dict()
    return render_template("map.html", crime_data=json.dumps(country_values))

@app.route('/country')
def country_redirect():
    country = request.args.get("country")
    return redirect(url_for('country_stats', country=country))

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

    return render_template('stats.html', charts=chart_data, charts_json=chart_data, country=country)
if __name__ == '__main__':
    app.run(debug=True)
