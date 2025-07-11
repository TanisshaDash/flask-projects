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

    # Get the most recent year per country
    latest_year = df['Year'].max()
    recent_df = df[df['Year'] == latest_year]

    # Prepare chart data using internal column names
    chart_data = {}

    for key in DISPLAY_LABELS.keys():
        if key in recent_df.columns:
            subset = recent_df[['Country', key]].dropna()
            subset = subset.sort_values(by=key, ascending=False).head(10)  # Top 10 countries
            chart_data[key] = {
                'countries': subset['Country'].tolist(),
                'values': subset[key].tolist()
            }

    # Map keys to readable chart titles
    charts_display = {}
    for key, data in chart_data.items():
        label = DISPLAY_LABELS.get(key, key)
        charts_display[label] = data

    return render_template('stats.html',
                           charts=charts_display,
                           charts_json=json.dumps(charts_display))

if __name__ == '__main__':
    app.run(debug=True)
