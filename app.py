import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Initialize the app
app = dash.Dash(__name__)
server = app.server  # needed for Render deployment

# Read and prepare data
df = pd.read_csv('data/facc.csv', skipinitialspace=True)

# Clean zone data
df['ZONE'] = df['ZONE'].astype(str).str.strip()
df['ZONE'] = df['ZONE'].apply(lambda x: str(int(float(x))) if x.replace('.', '').isdigit() else 'Unknown')

# Clean severity data
df['ACCIDENT_SEVERITY'] = df['ACCIDENT_SEVERITY'].astype(str).str.strip()

# Clean nationality data
df['NATIONALITY_GROUP_OF_ACCIDENT_'] = df['NATIONALITY_GROUP_OF_ACCIDENT_'].astype(str).str.strip()
df.loc[df['NATIONALITY_GROUP_OF_ACCIDENT_'].isin(['nan', 'NaN', 'None', '']), 'NATIONALITY_GROUP_OF_ACCIDENT_'] = 'Unknown'

# Get unique values for dropdowns
severity_options = [{'label': sev, 'value': sev} 
                   for sev in sorted(df['ACCIDENT_SEVERITY'].unique()) if sev not in ['nan', 'NaN', 'None', '']]
nationality_options = [{'label': nat, 'value': nat} 
                      for nat in sorted(df['NATIONALITY_GROUP_OF_ACCIDENT_'].unique()) if nat not in ['nan', 'NaN', 'None', '']]

# Color scheme
colors = {
    'background': '#111111',
    'card_bg': 'rgba(255, 255, 255, 0.05)',
    'text': '#FFFFFF',
    'neon_blue': '#00ffff',
    'grey': '#808080',
    'dark_grey': '#333333',
}

# Custom CSS with glassmorphism
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {
                background-color: #111111;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(0, 255, 255, 0.1) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(128, 128, 128, 0.1) 0%, transparent 40%);
                margin: 0;
                font-family: 'Space Grotesk', sans-serif;
            }
            .glass-card {
                background: rgba(0, 0, 0, 0.7);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                border: 1px solid rgba(0, 255, 255, 0.2);
                box-shadow: 0 8px 32px 0 rgba(0, 255, 255, 0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .glass-card:hover {
                border: 1px solid rgba(0, 255, 255, 0.3);
                box-shadow: 0 8px 32px 0 rgba(0, 255, 255, 0.2);
            }
            .dash-dropdown .Select-control {
                background-color: rgba(0, 0, 0, 0.8) !important;
                border: 1px solid rgba(0, 255, 255, 0.2) !important;
                border-radius: 10px;
            }
            .dash-dropdown .Select-menu-outer {
                background-color: rgba(0, 0, 0, 0.95) !important;
                border: 1px solid rgba(0, 255, 255, 0.2) !important;
                border-radius: 10px;
                z-index: 1000 !important;
            }
            .dash-dropdown .Select-value-label {
                color: #FFFFFF !important;
            }
            .dash-dropdown .Select-menu-outer .Select-option {
                background-color: rgba(0, 0, 0, 0.95) !important;
                color: #FFFFFF !important;
            }
            .dash-dropdown .Select-menu-outer .Select-option:hover {
                background-color: rgba(0, 255, 255, 0.2) !important;
            }
            .filter-container {
                position: relative;
                z-index: 100;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    html.H1("Qatar Traffic Accidents Analysis",
            style={
                'textAlign': 'center',
                'color': colors['neon_blue'],
                'marginBottom': '30px',
                'fontFamily': 'Space Grotesk',
                'textShadow': '0 0 10px rgba(0, 255, 255, 0.5)'
            }),
    
    # Filters
    html.Div([
        html.Div([
            html.Label("Accident Severity", style={'color': colors['neon_blue']}),
            dcc.Dropdown(
                id='severity-filter',
                options=severity_options,
                multi=True,
                className='dash-dropdown'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        html.Div([
            html.Label("Nationality", style={'color': colors['neon_blue']}),
            dcc.Dropdown(
                id='nationality-filter',
                options=nationality_options,
                multi=True,
                className='dash-dropdown'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'top'}),
        
    ], className='glass-card filter-container'),
    
    # Yearly Trend Chart
    html.Div([
        dcc.Graph(id='yearly-trend')
    ], className='glass-card'),
    
    # Top 10 Zones Chart
    html.Div([
        dcc.Graph(id='top-zones')
    ], className='glass-card'),
    
], style={'padding': '20px'})

# Callbacks
@app.callback(
    [Output('yearly-trend', 'figure'),
     Output('top-zones', 'figure')],
    [Input('severity-filter', 'value'),
     Input('nationality-filter', 'value')]
)
def update_charts(selected_severity, selected_nationality):
    # Filter data based on selections
    filtered_df = df.copy()
    
    if selected_severity:
        filtered_df = filtered_df[filtered_df['ACCIDENT_SEVERITY'].isin(selected_severity)]
    if selected_nationality:
        filtered_df = filtered_df[filtered_df['NATIONALITY_GROUP_OF_ACCIDENT_'].isin(selected_nationality)]
    
    # Yearly trend
    yearly_counts = filtered_df.groupby('ACCIDENT_YEAR').size().reset_index(name='count')
    yearly_fig = go.Figure()
    yearly_fig.add_trace(go.Scatter(
        x=yearly_counts['ACCIDENT_YEAR'],
        y=yearly_counts['count'],
        mode='lines+markers',
        line=dict(color=colors['neon_blue'], width=3),
        marker=dict(size=8, color=colors['grey'])
    ))
    yearly_fig.update_layout(
        title='Yearly Accident Trend',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], family='Space Grotesk'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    )
    
    # Top 10 zones by year
    zone_year_counts = filtered_df.groupby(['ACCIDENT_YEAR', 'ZONE']).size().reset_index(name='count')
    top_zones = zone_year_counts.groupby('ZONE')['count'].sum().nlargest(10).index
    zone_year_filtered = zone_year_counts[zone_year_counts['ZONE'].isin(top_zones)]
    
    zones_fig = px.line(zone_year_filtered, 
                       x='ACCIDENT_YEAR', 
                       y='count', 
                       color='ZONE',
                       title='Yearly Accidents in Top 10 Zones')
    zones_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], family='Space Grotesk'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        showlegend=True,
        legend_title_text='Zone'
    )
    
    return yearly_fig, zones_fig

if __name__ == '__main__':
    app.run_server(debug=True)