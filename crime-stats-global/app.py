from flask import Flask, render_template, request
import pandas as pd
import json

app = Flask(__name__)

# ✅ Load merged Excel file directly
data = pd.read_excel('static/data/merged_global_crime_data.xlsx')

# 🧹 Preprocess
data.fillna(0, inplace=True)
countries = sorted(data['Country'].unique())
years = sorted(data['Year'].unique())
crime_types = [col for col in data.columns if col not in ['Country', 'Year']]

@app.route('/')
def index():
    return render_template('index.html', countries=countries, years=years, crime_types=crime_types)

@app.route('/stats', methods=['POST'])
def stats():
    country = request.form['country']
    year = int(request.form['year'])
    selected_crimes = request.form.getlist('crime_types')

    filtered = data[(data['Country'] == country) & (data['Year'] == year)]
    crime_data = filtered[selected_crimes].to_dict(orient='records')[0] if not filtered.empty else {}

    return render_template('stats.html', country=country, year=year, crime_data=crime_data)

if __name__ == '__main__':
    app.run(debug=True)
