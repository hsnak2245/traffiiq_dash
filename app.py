import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd

# Initialize the Dash app
app = dash.Dash(__name__)

# Create some sample data
df = pd.DataFrame({
    'Year': [2019, 2020, 2021, 2022],
    'Sales': [100, 120, 140, 180]
})

# Create a simple line plot
fig = px.line(df, x='Year', y='Sales', title='Annual Sales')

# Define the app layout
app.layout = html.Div([
    html.H1('My First Dash App'),
    
    html.Div([
        dcc.Graph(
            id='example-graph',
            figure=fig
        )
    ])
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)