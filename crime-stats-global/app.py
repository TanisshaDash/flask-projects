from flask import Flask, render_template, request
import pandas as pd
from combine_crime_data import generate_merged_crime_data

# 🔁 Generate or update the merged dataset on app start
generate_merged_crime_data()

# 📁 Load the merged CSV
data = pd.read_csv('static/data/global_crime_data.csv')

# 🔧 Preprocess for dropdowns
data.fillna(0, inplace=True)
countries = sorted(data['Country'].unique())
years = sorted(data['Year'].unique())
crime_types = [col for col in data.columns if col not in ['Country', 'Year']]

# 🚀 Flask app setup
app = Flask(__name__)

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
