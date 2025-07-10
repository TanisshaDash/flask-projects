from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Load the merged CSV
def load_data():
    try:
        df = pd.read_csv('static/data/global_crime_data.csv')
        return df
    except FileNotFoundError:
        print("❌ Merged data file not found.")
        return pd.DataFrame()

@app.route('/')
def index():
    data = load_data()
    countries = sorted(data['Country'].unique()) if not data.empty else []
    return render_template('index.html', countries=countries)

@app.route('/stats/<country>')
def country_stats(country):
    data = load_data()
    if data.empty:
        return f"<h2>No data found for {country}</h2>"

    country_data = data[data['Country'] == country]
    if country_data.empty:
        return f"<h2>No statistics available for {country}</h2>"

    return render_template('stats.html', country=country, data=country_data)

if __name__ == '__main__':
    app.run(debug=True)
