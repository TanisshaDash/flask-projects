from flask import Flask, render_template, request, redirect, url_for,jsonify
import pandas as pd
from urllib.parse import unquote 
import json
from io import StringIO
from datetime import datetime
import os , requests 
from combine_crime_data import get_crime_summary
app = Flask(__name__)

DISPLAY_LABELS = {
    'corruption_and_economic_crime': 'Corruption and Economic Crime',
    'intentional_homicide': 'Intentional Homicide',
    'violent_and_sexual_crime': 'Violent and Sexual Crime',
    'firearms_trafficking': 'Firearms Trafficking',
    'access_and_functioning_of_justice': 'Access and Functioning of Justice'
}

# Local path for development
DATA_PATH = 'crime-stats-global/static/data/cleaned_global_crime_data.csv'

# Raw GitHub URL for production (replace with your actual repo URL)
DATA_URL = 'https://raw.githubusercontent.com/TanisshaDash/flask-projects/refs/heads/main/crime-stats-global/static/data/cleaned_global_crime_data.csv'

def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        print(f"📡 Fetching CSV from {DATA_URL}")
        df = pd.read_csv(DATA_URL)
        return df

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

def get_live_homicide(country_code):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/VC.IHR.PSRC.P5?format=json&per_page=100"
    response = requests.get(url)

    if response.status_code != 200:
        return {"years": [], "values": []}

    data = response.json()
    if not data or len(data) < 2:
        return {"years": [], "values": []}

    records = data[1]
    years, values = [], []
    for entry in records:
        year = entry.get("date")
        value = entry.get("value")
        if year and value is not None:
            year_int = int(year)
            if 2000 <= year_int <= 2024:
                years.append(year_int)
                values.append(float(value))

    return {"years": years[::-1], "values": values[::-1]}  # Oldest to newest

@app.route('/live')
def live_stats():
    selected_country = request.args.get('country', 'IN').upper()

    countries = {
        "IN": "India",
        "US": "United States",
        "BR": "Brazil",
        "ZA": "South Africa",
        "FR": "France",
        "JP": "Japan"
    }

    chart = get_live_homicide(selected_country)

    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")

    return render_template(
        "live_stats.html",
        chart=chart,
        countries=countries,
        selected_country=selected_country,
        timestamp=timestamp
    )


@app.route('/')
def index():
    df = load_data()
    df = df[df['Year'].between(2019, 2024)]

    countries = sorted(df['Country'].dropna().unique())
    df['total_crime'] = df[list(DISPLAY_LABELS.keys())].sum(axis=1)
    country_totals = df.groupby('Country')['total_crime'].sum().sort_values(ascending=False).head(20).reset_index()
    top_10 = country_totals.to_dict(orient='records')

    return render_template('index.html', countries=countries, top_10=top_10)

@app.route('/stats')
def stats():
    df = load_data()
    df = df[df['Year'].between(2019, 2024)]

    charts = {}
    for internal_col, display_name in DISPLAY_LABELS.items():
        if internal_col in df.columns:
            grouped = df.groupby("Year")[internal_col].sum().reset_index()

            charts[display_name] = {
                'years': grouped['Year'].tolist(),
                'values': grouped[internal_col].tolist(),
                'id': internal_col  # used for canvas/chart ID
            }

    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    return render_template("stats.html", charts=charts, charts_json=charts,
                           timestamp=timestamp, country=None)

@app.route('/map')
def crime_map():
    df = load_data()
    df = df[df['Year'] == 2023]
    country_values = df.groupby("Country")["intentional_homicide"].sum().to_dict()
    return render_template("map.html", crime_data=json.dumps(country_values))

@app.route('/country')
def country_redirect():
    country = request.args.get("country")
    return redirect(url_for('country_stats', country=country))

@app.route('/country/<country>')
def country_stats(country):
    df = load_data()

    # Decode country name from URL
    country_name = unquote(country)

    # Ensure Year is integer
    df['Year'] = df['Year'].astype(int)

    # Filter for that country and year range
    df = df[(df['Country'] == country_name) & (df['Year'].between(2019, 2024))]

    chart_data = {}
    for internal_col, display_name in DISPLAY_LABELS.items():
        if internal_col in df.columns:
            yearly = df[['Year', internal_col]].dropna().groupby('Year').sum().reset_index()
            values = yearly[internal_col].tolist()

            # Add all categories directly
            chart_data[display_name] = {
                "years": yearly['Year'].tolist(),
                "values": values
            }
    return render_template(
        'stats.html',
        charts=chart_data,
        charts_json=chart_data,
        country=country_name
    )
@app.route("/api/crime-summary", methods=["GET"])
def crime_summary():
    country = request.args.get("country")

    if not country:
        return jsonify({"error": "country parameter is required"}), 400

    summary = get_crime_summary(country)

    if not summary:
        return jsonify({"error": "No data found for this country"}), 404

    return jsonify(summary)


NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise RuntimeError("NEWS_API_KEY environment variable not set")

@app.route('/api/hyderabad-crime-news')
def hyderabad_crime_news():
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": "Hyderabad crime OR Hyderabad murder OR Hyderabad theft OR Hyderabad robbery",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    articles = []

    if data.get("status") == "ok":
        for a in data.get("articles", []):
            articles.append({
                "title": a["title"],
                "source": a["source"]["name"],
                "published_at": a["publishedAt"],
                "url": a["url"],
                "description": a["description"]
            })

    return jsonify({
        "city": "Hyderabad",
        "count": len(articles),
        "articles": articles
    })


if __name__ == '__main__':
    app.run(debug=True)
