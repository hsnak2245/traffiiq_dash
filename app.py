import pandas as pd
import json
import folium
from folium import plugins
import branca.colormap as cm
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
from datetime import datetime
import calendar
from pathlib import Path
import branca.element as be

class QatarAccidentsDashboard:
    def __init__(self, accidents_file='facc.csv', polygons_file='qatar_zones_polygons.json'):
        self.accidents_file = accidents_file
        self.polygons_file = polygons_file
        self.df = None
        self.zones_data = None
        self.zone_names = self.initialize_zone_names()
        self.current_year = None
        
        # Color scheme
        self.colors = {
            'background': '#F5F5DC',  # Beige
            'text': '#4D4D4D',  # Grey
            'title_background': '#800000',  # Maroon
            'title_text': '#F5F5DC',  # Beige
            'neon_pink': '#800000',  # Maroon
            'neon_cyan': '#B03060',  # Shade of Maroon
            'neon_green': '#8B0000',  # Dark Maroon
            'maroon': '#800000'
        }
        
        # Load and process data
        self.load_data()
        
    def initialize_zone_names(self):
        try:
            with open('zone_names.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load zone names: {e}")
            return {}

        
    def load_data(self):
        # Load accidents data
        self.df = pd.read_csv(self.accidents_file, skipinitialspace=True)
        
        # Clean data
        self.df['ZONE'] = self.df['ZONE'].astype(str).str.strip()
        self.df['ZONE'] = self.df['ZONE'].apply(lambda x: 
            str(int(float(x))) if x.replace('.', '').isdigit() else 'Unknown')
        
        # Convert time to hour
        self.df['HOUR'] = self.df['ACCIDENT_TIME'].str.extract('(\d+)').astype(float)
        
        # Set current year to the most recent year
        self.current_year = self.df['ACCIDENT_YEAR'].max()
        
        # Load polygon data
        try:
            with open(self.polygons_file, 'r') as f:
                self.zones_data = json.load(f)
        except:
            print("Warning: Could not load polygon data")

    def create_map(self, year):
        # Create base map
        m = folium.Map(
            location=[25.2867, 51.5333],
            zoom_start=11,
            tiles='CartoDB positron',
            prefer_canvas=True
        )
        
        # Get accident counts for the selected year
        year_data = self.df[self.df['ACCIDENT_YEAR'] == year]
        zone_counts = year_data['ZONE'].value_counts().to_dict()
        max_count = max(zone_counts.values()) if zone_counts else 1
        
        # Create color scale
        colormap = cm.LinearColormap(
            colors=['#F5F5DC', '#B03060', '#8B0000'],  # Beige to shades of maroon
            vmin=0,
            vmax=max_count
        )
        
        # Add zones to map
        for zone, count in zone_counts.items():
            try:
                if zone.lower() == 'unknown':
                    continue
                    
                zone_int = str(int(float(zone)))
                zone_data = self.zones_data.get(zone_int)
                zone_name = self.zone_names.get(zone_int, f'Zone {zone_int}')
                
                if zone_data:
                    coordinates = [[p['lat'], p['lng']] for p in zone_data['coordinates']]
                    opacity = 0.2 + (count / max_count * 0.8)
                    
                    folium.Polygon(
                        locations=coordinates,
                        weight=0,
                        fill=True,
                        fill_color=colormap(count),
                        fill_opacity=opacity,
                        popup=f'{zone_name}<br>Accidents: {count}',
                        tooltip=zone_name
                    ).add_to(m)
                    
            except Exception as e:
                print(f"Error processing zone {zone}: {str(e)}")
                
        # Add the color scale
        colormap.add_to(m)
        
        # Save the map to HTML
        map_path = 'assets/map.html'
        m.save(map_path)
        return map_path

    def create_dashboard(self):
        app = dash.Dash(__name__)
        
        # Calculate metrics before creating layout
        metrics = self.calculate_metrics()
        
        # Add custom font
        app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                <title>Qatar Traffic Accidents Analysis</title>
                <link href="https://api.fontshare.com/v2/css?f[]=space-grotesk@400,700&display=swap" rel="stylesheet">
                {%metas%}
                {%favicon%}
                {%css%}
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
        
        # Create initial map
        initial_map_path = self.create_map(self.current_year)
        
        app.layout = html.Div(style={
            'backgroundColor': self.colors['background'], 
            'padding': '20px',
            'minHeight': '100vh',
            'fontFamily': 'Space Grotesk, sans-serif'
        }, children=[
            html.Div(style={
                'backgroundColor': self.colors['title_background'],
                'padding': '10px',
                'borderRadius': '5px'
            }, children=[
                html.H1('Qatar Traffic Accidents Analysis',
                       style={'color': self.colors['title_text'], 
                              'textAlign': 'center'})
            ]),
            
            # Metrics Row
            html.Div(style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'gap': '20px',
                'margin': '20px 0',
                'flexWrap': 'wrap'
            }, children=[
                # Calculate metrics
                *[html.Div(style={
                    'flex': '1',
                    'minWidth': '200px',
                    'padding': '20px',
                    'textAlign': 'center',
                    'position': 'relative'
                }, children=[
                    html.Div(style={
                        'fontSize': '3em',
                        'color': self.colors['neon_cyan'],
                        'fontWeight': 'bold'
                    }, children=[
                        html.I(className='fas fa-car-crash', style={
                            'position': 'absolute',
                            'top': '10px',
                            'left': '10px',
                            'fontSize': '1.5em',
                            'color': self.colors['neon_pink']
                        }),
                        html.Span(id=f'{title.lower().replace(" ", "-")}-value', children=str(value))
                    ]),
                    html.H4(title, style={
                        'color': self.colors['neon_pink'],
                        'marginTop': '10px',
                        'fontSize': '1em'
                    })
                ]) for title, value in [
                    ('Annual Avg. Accidents (2020+)', self.format_number(metrics['annual_avg'])),
                    ('Total Deaths', self.format_number(metrics['total_deaths'])),
                    ('Pedestrian Collision Deaths', self.format_number(metrics['pedestrian_deaths'])),
                    ('Total Accidents', self.format_number(metrics['total_accidents']))
                ]]
            ]),
            
            # Main content container
            html.Div(style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'gap': '20px',
                'margin': '20px 0'
            }, children=[
                # Left section - Map
                html.Div(style={
                    'flex': '2',
                    'minWidth': '600px'
                }, children=[
                    # Year selector above map
                    html.Div(style={
                        'marginBottom': '20px',
                        'padding': '20px',
                    }, children=[
                        html.Label('Select Year:', 
                                 style={'color': self.colors['text'],
                                       'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='year-selector',
                            options=[{'label': str(int(year)), 'value': year} 
                                    for year in sorted(self.df['ACCIDENT_YEAR'].unique())],
                            value=self.current_year,
                            style={
                                'width': '200px',
                                'backgroundColor': self.colors['background'],
                                'color': 'black'
                            }
                        )
                    ]),
                    # Map
                    html.Div(style={
                        'height': '600px',
                        'overflow': 'hidden'
                    }, children=[
                        html.Iframe(
                            id='map-iframe',
                            srcDoc=open(initial_map_path, 'r').read(),
                            style={'width': '100%', 'height': '100%', 'border': 'none'}
                        )
                    ])
                ]),
                
                # Right section - Stats
                html.Div(style={
                    'flex': '1',
                    'minWidth': '300px',
                    'padding': '20px',
                    'color': self.colors['text'],
                    'height': '680px',  # Add this line
                    'overflowY': 'auto'  # Add this line for scrolling
                }, children=[
                    html.H3('Zone Statistics', 
                           style={'color': self.colors['neon_pink']}),
                    html.Div(id='zone-stats-content')
                ])
            ]),

            # New visualizations
            html.Div(style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'gap': '20px',
                'margin': '20px 0'
            }, children=[
                # Stacked bar chart
                html.Div(style={
                    'flex': '1',
                    'minWidth': '300px',
                    'padding': '20px',
                    'color': self.colors['text']
                }, children=[
                    html.H3('Accident Severity by Category', 
                           style={'color': self.colors['text']}),
                    dcc.Dropdown(
                        id='category-selector',
                        options=[
                            {'label': 'Nationality Group', 'value': 'NATIONALITY_GROUP_OF_ACCIDENT_'},
                            {'label': 'Accident Nature', 'value': 'ACCIDENT_NATURE'},
                            {'label': 'Accident Reason', 'value': 'ACCIDENT_REASON'}
                        ],
                        value='NATIONALITY_GROUP_OF_ACCIDENT_',
                        style={
                            'width': '200px',
                            'backgroundColor': self.colors['background'],
                            'color': 'black'
                        }
                    ),
                    dcc.Graph(id='severity-bar-chart')
                ]),

                # Scatter plot
                html.Div(style={
                    'flex': '1',
                    'minWidth': '300px',
                    'padding': '20px',
                    'color': self.colors['text']
                }, children=[
                    html.H3('Age vs Number of Accidents', 
                           style={'color': self.colors['text']}),
                    dcc.Graph(id='age-scatter-plot')
                ])
            ])
        ])
        
        @app.callback(
            [Output('map-iframe', 'srcDoc'),
             Output('zone-stats-content', 'children')],
            [Input('year-selector', 'value')]
        )
        def update_map_and_stats(selected_year):
            # Update map
            map_path = self.create_map(selected_year)
            map_html = open(map_path, 'r').read()
            
            # Update stats
            year_data = self.df[self.df['ACCIDENT_YEAR'] == selected_year]
            zone_counts = year_data['ZONE'].value_counts().sort_values(ascending=False)
            
            stats_content = []
            for zone, count in zone_counts.items():
                zone_name = self.zone_names.get(str(zone), f'Zone {zone}')
                stats_content.append(html.Div(style={
                    'marginBottom': '10px',
                    'padding': '8px',
                    'backgroundColor': 'rgba(255, 0, 255, 0.1)',
                    'borderRadius': '5px'
                }, children=[
                    html.Div(zone_name, style={'color': self.colors['neon_cyan']}),
                    html.Div(f'Accidents: {count}', style={'fontSize': '0.9em'})
                ]))
            
            return map_html, stats_content

        @app.callback(
            Output('severity-bar-chart', 'figure'),
            [Input('category-selector', 'value')]
        )
        def update_severity_bar_chart(selected_category):
            if selected_category not in self.df.columns or 'ACCIDENT_SEVERITY' not in self.df.columns:
                return go.Figure()  # Return an empty figure if columns are missing
            
            severity_counts = self.df.groupby([selected_category, 'ACCIDENT_SEVERITY']).size().unstack().fillna(0)
            fig = px.bar(severity_counts, barmode='stack', title='Accident Severity by ' + selected_category)
            fig.update_layout(
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text'],
                colorway=['rgb(245,245,220)', 'rgb(176,48,96)', 'rgb(139,0,0)']  # Beige to shades of maroon
            )
            return fig

        @app.callback(
            Output('age-scatter-plot', 'figure'),
            [Input('year-selector', 'value')]
        )
        def update_age_scatter_plot(selected_year):
            if 'BIRTH_YEAR_OF_ACCIDENT_PERPETR' not in self.df.columns:
                return go.Figure()  # Return an empty figure if column is missing
            
            year_data = self.df[self.df['ACCIDENT_YEAR'] == selected_year]
            year_data['AGE'] = year_data['BIRTH_YEAR_OF_ACCIDENT_PERPETR'].apply(lambda x: selected_year - x if pd.notnull(x) else None)
            year_data = year_data[(year_data['AGE'] >= 0) & (year_data['AGE'] <= 90)]  # Filter age between 0 and 90
            age_counts = year_data.groupby('AGE').size().reset_index(name='ACCIDENT_COUNT')
            mean_age = year_data['AGE'].mean()
            
            fig = px.scatter(age_counts, x='AGE', y='ACCIDENT_COUNT', size='ACCIDENT_COUNT', title='Age vs Number of Accidents')
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.95, y=1.05,
                text=f"Mean Age: {mean_age:.1f}",
                showarrow=False,
                font=dict(
                    size=12,
                    color=self.colors['text']
                ),
                align="right"
            )
            fig.update_layout(
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text'],
                colorway=['rgb(245,245,220)', 'rgb(176,48,96)', 'rgb(139,0,0)']  # Beige to shades of maroon
            )
            return fig
        
        return app
    
    def run_dashboard(self, debug=True):
        # Create assets folder for map
        Path('assets').mkdir(exist_ok=True)
        
        app = self.create_dashboard()
        app.run_server(debug=debug)

    def calculate_metrics(self):
        # Calculate annual average accidents from 2020 onwards
        recent_data = self.df[self.df['ACCIDENT_YEAR'] >= 2020]
        annual_avg = len(recent_data) / len(recent_data['ACCIDENT_YEAR'].unique())
        
        # Calculate total deaths till 2024
        total_deaths = self.df['DEATH_COUNT'].sum()
        
        # Calculate pedestrian collision deaths
        pedestrian_deaths = self.df[
            self.df['ACCIDENT_NATURE'] == 'COLLISION WITH PEDESTRIANS'
        ]['DEATH_COUNT'].sum()
        
        # Calculate total accidents
        total_accidents = len(self.df)
        
        return {
            'annual_avg': round(annual_avg, 1),
            'total_deaths': int(total_deaths),
            'pedestrian_deaths': int(pedestrian_deaths),
            'total_accidents': total_accidents
        }

    def format_number(self, num):
        if num >= 1_000_000:
            return f'{num/1_000_000:.1f}M+'
        elif num >= 1_000:
            return f'{num/1_000:.1f}K+'
        else:
            return str(num)

if __name__ == "__main__":
    dashboard = QatarAccidentsDashboard()
    dashboard.run_dashboard()