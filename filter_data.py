import pandas as pd
from datetime import datetime

# Load the data
data = pd.read_csv('License.csv')

# Convert the FIRST_ISSUEDATE column to datetime, coerce errors
data['FIRST_ISSUEDATE'] = pd.to_datetime(data['FIRST_ISSUEDATE'], errors='coerce', format='%Y-%m-%d')

# Define the date range
start_date = datetime(2020, 1, 1)
end_date = datetime(2024, 12, 31)

# Filter the data
filtered_data = data[(data['FIRST_ISSUEDATE'] >= start_date) & (data['FIRST_ISSUEDATE'] <= end_date)]

# Output the filtered data
filtered_data.to_csv('liz.csv', index=False)

