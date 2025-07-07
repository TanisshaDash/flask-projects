import pandas as pd

# Load your individual Excel files
homicide_df = pd.read_excel('crime-stats-global/data_cts_corruption_and_economic_crime.xlsx')
assault_df = pd.read_excel('data/assault.xlsx')
robbery_df = pd.read_excel('data/robbery.xlsx')

# Make sure they have 'Country' and 'Year' columns
# Rename the crime value column in each to reflect the type of crime
homicide_df.rename(columns={'Value': 'Homicide'}, inplace=True)
assault_df.rename(columns={'Value': 'Assault'}, inplace=True)
robbery_df.rename(columns={'Value': 'Robbery'}, inplace=True)

# Merge all dataframes on 'Country' and 'Year'
merged_df = homicide_df.merge(assault_df, on=['Country', 'Year'], how='outer')
merged_df = merged_df.merge(robbery_df, on=['Country', 'Year'], how='outer')

# Fill missing values with 0 (optional)
merged_df.fillna(0, inplace=True)

# Save to CSV
merged_df.to_csv('static/data/global_crime_data.csv', index=False)
print(\"Combined data saved to static/data/global_crime_data.csv\")
