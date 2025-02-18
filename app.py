import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Read and prepare data
df = pd.read_csv('facc.csv', skipinitialspace=True)

# Clean zone data
df['ZONE'] = df['ZONE'].astype(str).str.strip()
df['ZONE'] = df['ZONE'].apply(lambda x: str(int(float(x))) if x.replace('.', '').isdigit() else 'Unknown')

# Extract hour from time
df['HOUR'] = df['ACCIDENT_TIME'].str.extract('(\d+)').astype(float)

# Color scheme
colors = {
    'background': '#111111',
    'card_bg': 'rgba(255, 255, 255, 0.05)',
    'text': '#FFFFFF',
    'vibrant_red': '#FF3B3B',
    'maroon': '#800000',
    'yellow': '#FFD700',
    'border': 'rgba(255, 255, 255, 0.1)'
}

# Initialize the app
app = dash.Dash(__name__)

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
                    radial-gradient(circle at 10% 20%, rgba(128, 0, 0, 0.2) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(255, 59, 59, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 60%);
                margin: 0;
                font-family: 'Space Grotesk', sans-serif;
            }
            .glass-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                padding: 20px;
                margin-bottom: 20px;
            }
            .glass-card:hover {
                background: rgba(255, 255, 255, 0.08);
                transition: background 0.3s ease;
            }
            .dash-dropdown .Select-control {
                background-color: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 10px;
            }
            .dash-dropdown .Select-menu-outer {
                background-color: #1a1a1a !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 10px;
            }
            .dash-dropdown .Select-value-label {
                color: #FFFFFF !important;
            }
            .dash-dropdown .Select-menu-outer .Select-option {
                background-color: #1a1a1a !important;
                color: #FFFFFF !important;
            }
            .dash-dropdown .Select-menu-outer .Select-option:hover {
                background-color: rgba(255, 59, 59, 0.2) !important;
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
    html.H1("Qatar Traffic Accidents Dashboard",
            style={
                'textAlign': 'center',
                'marginBottom': '30px',
                'color': colors['vibrant_red'],
                'fontSize': '2.5em',
                'textShadow': '2px 2px 4px rgba(0, 0, 0, 0.5)'
            }),
    
    # Filters row
    html.Div([
        html.Div([
            html.Label("Select Year", style={'color': colors['text']}),
            dcc.Dropdown(
                id='year-filter',
                options=[{'label': str(int(year)), 'value': year} 
                        for year in sorted(df['ACCIDENT_YEAR'].unique())],
                value=df['ACCIDENT_YEAR'].max(),
                className='dash-dropdown'
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        html.Div([
            html.Label("Select Zone", style={'color': colors['text']}),
            dcc.Dropdown(
                id='zone-filter',
                options=[{'label': f'Zone {zone}', 'value': zone} 
                        for zone in sorted(df['ZONE'].unique())],
                value='all',
                multi=True,
                className='dash-dropdown'
            )
        ], style={'width': '60%', 'display': 'inline-block', 'marginLeft': '40px'})
    ], className='glass-card'),

    # Charts row 1
    html.Div([
        html.Div([
            dcc.Graph(id='yearly-trend')
        ], className='glass-card', style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='hourly-distribution')
        ], className='glass-card', style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
    ]),

    # Charts row 2
    html.Div([
        html.Div([
            dcc.Graph(id='zone-bar')
        ], className='glass-card', style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='weather-pie')
        ], className='glass-card', style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
    ]),

    # Summary statistics
    html.Div([
        html.H3("Summary Statistics", 
                style={
                    'textAlign': 'center',
                    'color': colors['yellow'],
                    'marginBottom': '20px'
                }),
        html.Div(id='summary-stats', 
                 style={
                     'textAlign': 'center',
                     'color': colors['text']
                 })
    ], className='glass-card', style={'marginTop': '30px'})
], style={'padding': '20px'})

# Callbacks
@app.callback(
    [Output('yearly-trend', 'figure'),
     Output('hourly-distribution', 'figure'),
     Output('zone-bar', 'figure'),
     Output('weather-pie', 'figure'),
     Output('summary-stats', 'children')],
    [Input('year-filter', 'value'),
     Input('zone-filter', 'value')]
)
def update_graphs(selected_year, selected_zones):
    # Filter data
    if selected_zones == 'all' or not selected_zones:
        filtered_df = df[df['ACCIDENT_YEAR'] == selected_year]
    else:
        filtered_df = df[(df['ACCIDENT_YEAR'] == selected_year) & 
                        (df['ZONE'].isin(selected_zones))]

    # Common figure layout
    layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], family='Space Grotesk'),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Yearly trend
    yearly_df = df.groupby('ACCIDENT_YEAR').size().reset_index(name='count')
    yearly_fig = go.Figure()
    yearly_fig.add_trace(go.Scatter(
        x=yearly_df['ACCIDENT_YEAR'],
        y=yearly_df['count'],
        mode='lines+markers',
        line=dict(color=colors['vibrant_red'], width=3),
        marker=dict(size=8, color=colors['yellow'])
    ))
    yearly_fig.update_layout(
        title='Yearly Accident Trend',
        **layout
    )

    # Hourly distribution
    hourly_fig = go.Figure()
    hourly_fig.add_trace(go.Histogram(
        x=filtered_df['HOUR'],
        nbinsx=24,
        marker_color=colors['maroon']
    ))
    hourly_fig.update_layout(
        title='Hourly Distribution of Accidents',
        **layout
    )

    # Zone distribution
    zone_counts = filtered_df['ZONE'].value_counts().head(10)
    zone_fig = go.Figure()
    zone_fig.add_trace(go.Bar(
        x=zone_counts.index,
        y=zone_counts.values,
        marker_color=colors['vibrant_red']
    ))
    zone_fig.update_layout(
        title='Top 10 Zones by Accident Count',
        **layout
    )

    # Weather distribution
    if 'WEATHER' in filtered_df.columns:
        weather_counts = filtered_df['WEATHER'].value_counts()
        weather_fig = go.Figure()
        weather_fig.add_trace(go.Pie(
            labels=weather_counts.index,
            values=weather_counts.values,
            marker=dict(colors=[colors['vibrant_red'], colors['maroon'], colors['yellow']])
        ))
        weather_fig.update_layout(
            title='Weather Conditions Distribution',
            **layout
        )
    else:
        weather_fig = go.Figure()
        weather_fig.update_layout(
            title='Weather Data Not Available',
            **layout
        )

    # Summary statistics
    stats = html.Div([
        html.Div([
            html.Strong("Total Accidents: ", style={'color': colors['yellow']}),
            html.Span(f"{len(filtered_df)}")
        ], style={'marginBottom': '10px'}),
        html.Div([
            html.Strong("Zones Affected: ", style={'color': colors['yellow']}),
            html.Span(f"{filtered_df['ZONE'].nunique()}")
        ], style={'marginBottom': '10px'}),
        html.Div([
            html.Strong("Most Common Hour: ", style={'color': colors['yellow']}),
            html.Span(f"{filtered_df['HOUR'].mode().iloc[0]}")
        ])
    ])

    return yearly_fig, hourly_fig, zone_fig, weather_fig, stats

if __name__ == '__main__':
    app.run_server(debug=True)