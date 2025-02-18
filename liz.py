import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import logging
from flask_caching import Cache

# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR)

class LicenseDashboard:
    def __init__(self, license_file='liz.csv'):
        self.license_file = license_file
        self.license_df = None
        self.colors = {
            'background': '#000000',  # Changed to black
            'text': '#FFFFFF',
            'neon_pink': '#FF00FF',
            'neon_cyan': '#00FFFF',
            'neon_green': '#39FF14',
            'neon_blue': '#0000FF',  # Added neon blue
            'maroon': '#800000'
        }
        self.load_data()
        
    def load_data(self):
        try:
            self.license_df = pd.read_csv(self.license_file, skipinitialspace=True)
            self.license_df['FIRST_ISSUEDATE'] = pd.to_datetime(self.license_df['FIRST_ISSUEDATE'])
            self.license_df['AGE'] = self.license_df['FIRST_ISSUEDATE'].dt.year - self.license_df['BIRTHYEAR']
            self.license_df['MONTH'] = self.license_df['FIRST_ISSUEDATE'].dt.month
            self.license_df['YEAR'] = self.license_df['FIRST_ISSUEDATE'].dt.year
        except Exception as e:
            logging.error("Error loading data: %s", e)
        
    def create_dashboard(self):
        app = dash.Dash(__name__)
        cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})
        
        app.layout = html.Div(style={
            'backgroundColor': self.colors['background'], 
            'padding': '20px',
            'minHeight': '100vh',
            'fontFamily': 'Space Grotesk, sans-serif'
        }, children=[
            html.H1('TraffiQ',
                   style={'color': self.colors['neon_cyan'], 
                          'textAlign': 'center',
                          'fontSize': '3em',
                          'fontWeight': 'bold'}),
            
            # License Section
            html.H2('License Dashboard', style={'color': self.colors['neon_pink'], 'textAlign': 'center'}),
            html.Div(style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'gap': '20px',
                'margin': '20px 0'
            }, children=[
                # Line chart for annual license issue
                html.Div(style={
                    'flex': '1 1 100%',
                    'backgroundColor': '#000000',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'color': self.colors['text'],
                    'border': '1px solid #333'  # Thin border
                }, children=[
                    html.H3('Annual License Issue', 
                           style={'color': self.colors['neon_pink']}),
                    dcc.Graph(id='annual-license-line-chart')
                ]),
                
                # Bubble chart for age at license issue
                html.Div(style={
                    'flex': '1',
                    'minWidth': '300px',
                    'backgroundColor': '#000000',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'color': self.colors['text'],
                    'border': '1px solid #333'  # Thin border
                }, children=[
                    html.H3('Age at License Issue', 
                           style={'color': self.colors['neon_pink']}),
                    dcc.Graph(id='age-bubble-chart')
                ]),
                
                # Line chart for license by category
                html.Div(style={
                    'flex': '1',
                    'minWidth': '300px',
                    'backgroundColor': '#000000',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'color': self.colors['text'],
                    'border': '1px solid #333'  # Thin border
                }, children=[
                    html.H3('License Issued by Category', 
                           style={'color': self.colors['neon_pink']}),
                    html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
                        dcc.Dropdown(
                            id='license-category-selector',
                            options=[
                                {'label': 'Gender', 'value': 'GENDER'},
                                {'label': 'Nationality Group', 'value': 'NATIONALITY_GROUP'}
                            ],
                            value='GENDER',
                            style={
                                'width': '200px',
                                'backgroundColor': self.colors['background'],
                                'color': 'black'
                            }
                        ),
                        dcc.Dropdown(
                            id='year-selector',
                            options=[{'label': str(year), 'value': year} for year in sorted(self.license_df['YEAR'].unique())],
                            value=self.license_df['YEAR'].max(),
                            style={
                                'width': '200px',
                                'backgroundColor': self.colors['background'],
                                'color': 'black'
                            }
                        )
                    ]),
                    dcc.Graph(id='license-line-chart')
                ])
            ])
        ])
        
        @cache.memoize(timeout=60)
        def get_license_counts(selected_category, selected_year):
            return self.license_df[self.license_df['YEAR'] == selected_year].groupby([selected_category, pd.Grouper(key='FIRST_ISSUEDATE', freq='W')]).size().reset_index(name='COUNT')
        
        @cache.memoize(timeout=60)
        def get_age_counts():
            return self.license_df.groupby('AGE').size().reset_index(name='COUNT')
        
        @cache.memoize(timeout=60)
        def get_monthly_counts():
            return self.license_df.groupby(['YEAR', 'MONTH']).size().reset_index(name='COUNT')
        
        @app.callback(
            Output('license-line-chart', 'figure'),
            [Input('license-category-selector', 'value'),
             Input('year-selector', 'value')]
        )
        def update_license_line_chart(selected_category, selected_year):
            if selected_category not in self.license_df.columns:
                return go.Figure()  # Return an empty figure if column is missing
            
            license_counts = get_license_counts(selected_category, selected_year)
            try:
                fig = px.line(license_counts, x='FIRST_ISSUEDATE', y='COUNT', color=selected_category, title=f'License Issued by {selected_category} in {selected_year}')
                fig.update_traces(line=dict(width=3, shape='spline'))
                fig.update_layout(
                    xaxis_title='Issue Date',  # Updated x-axis title
                    yaxis_title='Number of Licenses',  # Updated y-axis title
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font_color=self.colors['text']
                )
                return fig
            except Exception as e:
                logging.error("Error creating line chart for %s in %s: %s", selected_category, selected_year, e)
                return None
        
        @app.callback(
            Output('age-bubble-chart', 'figure'),
            [Input('license-category-selector', 'value')]
        )
        def update_age_bubble_chart(selected_category):
            try:
                age_counts = get_age_counts()
                mean_age = (self.license_df['AGE'].mean())
                fig = px.scatter(age_counts, x='AGE', y='COUNT', size='COUNT', title='',  # Removed title
                                 color_discrete_sequence=[self.colors['neon_blue']])  # Changed color to neon blue
                fig.add_annotation(
                    x=0.95, y=0.95, xref='paper', yref='paper',
                    text=f'Mean Age: {mean_age:.2f}', showarrow=False,
                    font=dict(color=self.colors['neon_green'], size=14),
                    bgcolor=self.colors['background']
                )
                fig.update_layout(
                    xaxis_title='Age at License Issue',  # Updated x-axis title
                    yaxis_title='Number of Licenses Issued',  # Updated y-axis title
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font_color=self.colors['text']
                )
                return fig
            except Exception as e:
                logging.error("Error creating bubble chart: %s", e)
                return go.Figure()  # Return an empty figure if there's an error
        
        @app.callback(
            Output('annual-license-line-chart', 'figure'),
            [Input('license-category-selector', 'value')]
        )
        def update_annual_license_line_chart(selected_category):
            monthly_counts = get_monthly_counts()
            try:
                fig = px.line(monthly_counts, x='MONTH', y='COUNT', color='YEAR', title='Annual License Issue')
                fig.update_traces(line=dict(width=3, shape='spline'))
                fig.update_layout(
                    xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']),
                    xaxis_title='Month',  # Updated x-axis title
                    yaxis_title='Number of Licenses Issued',  # Updated y-axis title
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font_color=self.colors['text']
                )
                return fig
            except Exception as e:
                logging.error("Error creating annual license line chart: %s", e)
                return None
        
        return app
    
    def run_dashboard(self, debug=True):
        app = self.create_dashboard()
        app.run_server(debug=debug)

if __name__ == "__main__":
    dashboard = LicenseDashboard()
    dashboard.run_dashboard()
