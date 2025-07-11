from flask import Flask, render_template
import pandas as pd
import json

app = Flask(__name__)

# Label mapping for display purposes
DISPLAY_LABELS = {
    'corruption_and_economic_crime': 'Corruption and Economic Crime',
    'intentional_homicide': 'Intentional Homicide',
    'violent_and_sexual_crime': 'Violent and Sexual Crime',
    'firearms_trafficking': 'Firearms Trafficking',
    'access_and_functioning_of_justice': 'Access and Functioning of Justice'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats():
    df = pd.read_csv('static/data/global_crime_data.csv')

    # ✅ Filter for years between 2019 and 2024
    df = df[(df['Year'] >= 2019) & (df['Year'] <= 2024)]

    # Get the most recent year from the filtered data
    latest_year = df['Year'].max()
    recent_df = df[df['Year'] == latest_year]

    chart_data = {}
    charts_display = {}

    for internal, label in DISPLAY_LABELS.items():
        if internal in recent_df.columns:
            filtered = recent_df[['Country', internal]].dropna()
            top_countries = filtered.sort_values(by=internal, ascending=False).head(10)

            values = top_countries[internal].tolist()
            countries = top_countries['Country'].tolist()

            if any(v > 0 for v in values):
                charts_display[label] = {
                    'countries': countries,
                    'values': values
                }

    print("📊 Charts JSON Preview:\n", json.dumps(charts_display, indent=2))
    return render_template('stats.html', charts=charts_display, charts_json=json.dumps(charts_display))



if __name__ == '__main__':
    app.run(debug=True)
