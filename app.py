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
            'background': '#111111',
            'text': '#FFFFFF',
            'neon_pink': '#FF00FF',
            'neon_cyan': '#00FFFF',
            'neon_green': '#39FF14',
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
            tiles='CartoDB dark_matter',
            prefer_canvas=True
        )
        
        # Get accident counts for the selected year
        year_data = self.df[self.df['ACCIDENT_YEAR'] == year]
        zone_counts = year_data['ZONE'].value_counts().to_dict()
        max_count = max(zone_counts.values()) if zone_counts else 1
        
        # Create color scale
        colormap = cm.LinearColormap(
            colors=['#ff00ff', '#00ffff', '#ff0000'],
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
            html.H1('Qatar Traffic Accidents Analysis',
                   style={'color': self.colors['neon_cyan'], 
                          'textAlign': 'center'}),
            
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
                        'backgroundColor': '#222',
                        'padding': '20px',
                        'borderRadius': '10px',
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
                        'backgroundColor': '#222',
                        'borderRadius': '10px',
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
                    'backgroundColor': '#222',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'color': self.colors['text'],
                    'height': '680px',  # Add this line
                    'overflowY': 'auto'  # Add this line for scrolling
                }, children=[
                    html.H3('Zone Statistics', 
                           style={'color': self.colors['neon_pink']}),
                    html.Div(id='zone-stats-content')
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
        
        return app
    
    def run_dashboard(self, debug=True):
        # Create assets folder for map
        Path('assets').mkdir(exist_ok=True)
        
        app = self.create_dashboard()
        app.run_server(debug=debug)

if __name__ == "__main__":
    dashboard = QatarAccidentsDashboard()
    dashboard.run_dashboard()