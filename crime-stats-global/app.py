from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import requests
import json
from io import StringIO
from datetime import datetime

app = Flask(__name__)

DISPLAY_LABELS = {
    'corruption_and_economic_crime': 'Corruption and Economic Crime',
    'intentional_homicide': 'Intentional Homicide',
    'violent_and_sexual_crime': 'Violent and Sexual Crime',
    'firearms_trafficking': 'Firearms Trafficking',
    'access_and_functioning_of_justice': 'Access and Functioning of Justice'
}

DATA_PATH = 'static/data/cleaned_global_crime_data.csv'

def fetch_and_clean_csv(url):
    print(f"🔗 Fetching data from {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch CSV file.")
    csv_data = StringIO(response.text)
    df = pd.read_csv(csv_data)
    df.columns = df.columns.str.strip()
    df = df[df['Year'].between(2019, 2024)]
    return df

def get_live_homicide_data(country_code):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/VC.IHR.PSRC.P5?format=json&per_page=100"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {"years": [], "values": []}

    data = response.json()
    if not data or len(data) < 2:
        return {"years": [], "values": []}

    records = data[1]
    years = []
    values = []

    for entry in records:
        year = entry.get("date")
        value = entry.get("value")
        if year and value is not None:
            years.append(int(year))
            values.append(float(value))

    return {"years": years[::-1], "values": values[::-1]}  # Sort oldest to newest

@app.route('/live')
def live_homicide_dashboard():
    selected_country = request.args.get('country', 'IN').upper()
    chart = get_live_homicide_data(selected_country)

    countries = {
        "IN": "India",
        "US": "United States",
        "BR": "Brazil",
        "ZA": "South Africa",
        "FR": "France",
        "JP": "Japan"
    }

    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    return render_template("live_stats.html", chart=chart, countries=countries,
                           selected_country=selected_country, timestamp=timestamp)

@app.route('/')
def index():
    df = pd.read_csv(DATA_PATH)
    df = df[df['Year'].between(2019, 2024)]

    countries = sorted(df['Country'].dropna().unique())
    df['total_crime'] = df[list(DISPLAY_LABELS.keys())].sum(axis=1)
    country_totals = df.groupby('Country')['total_crime'].sum().sort_values(ascending=False).head(10).reset_index()
    top_10 = country_totals.to_dict(orient='records')

    return render_template('index.html', countries=countries, top_10=top_10)

@app.route('/stats')
def stats():
    url = "https://raw.githubusercontent.com/TanisshaDash/flask-projects/main/crime-stats-global/static/data/cleaned_global_crime_data.csv"
    df = fetch_and_clean_csv(url)

    charts = {}
    for crime_type in df['Crime Type'].unique():
        subset = df[df['Crime Type'] == crime_type]
        charts[crime_type] = {
            'years': list(subset['Year']),
            'values': list(subset['Value'])
        }

    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    return render_template("stats.html", charts=charts, charts_json=charts, timestamp=timestamp, country=None)

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