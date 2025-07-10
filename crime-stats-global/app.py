from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load the cleaned and merged crime data
df = pd.read_csv("static/data/global_crime_data.csv")

# Mapping readable labels to CSV column names
headers_map = {
    "Corruption and Economic Crime": "corruption_economic_crime",
    "Homicide": "homicide",
    "Violent and Sexual Crime": "violent_sexual_crime",
    "Firearms Trafficking": "firearms_trafficking",
    "Access and Functioning of Justice": "access_functioning_justice"
}

# Home route – shows dropdown of countries
@app.route("/")
def index():
    countries = sorted(df["Country"].dropna().unique())
    return render_template("index.html", countries=countries)

# Stats route – shows crime data for selected country
@app.route('/stats')
def stats():
    df = pd.read_csv('static/data/global_crime_data.csv')
    latest_year = df['Year'].max()
    filtered_df = df[df['Year'] == latest_year]

    crime_columns = ['Corruption and Economic Crime', 'Intentional Homicide', 'Violent and Sexual Crime', 'Firearms Trafficking', 'Access and Functioning of Justice']
    values = [filtered_df[col].sum() for col in crime_columns]

    return render_template('stats.html', headers=crime_columns, values=values)


if __name__ == "__main__":
    app.run(debug=True)
