import pandas as pd
import numpy as np
import json
import folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
from sklearn.metrics.pairwise import cosine_similarity
from flask_caching import Cache
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR)

# Load and process data
def load_json_data(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)
    return df

def create_fingerprint(df):
    violation_cols = [
        'lsr_lzy_d_lrdr_over_speed_radar',
        'mkhlft_qt_lshr_ldwy_y_passing_traffic_signal_violations',
        'mkhlft_lrshdt_walt_ltnbyh_guidlines_and_alarm_signals_violations',
        'mkhlft_llwht_lm_dny_metallic_plates_violations',
        'mkhlft_ltjwz_overtaking_violations',
        'mkhlft_tsjyl_w_dm_tjdyd_lstmr_registration_and_form_non_renewal_violations',
        'mkhlft_rkhs_lqyd_driving_licenses_violations',
        'mkhlft_lhrk_lmrwry_traffic_movement_violations',
        'mkhlft_qw_d_wltzmt_lwqwf_wlntzr_stand_and_wait_rules_and_obligations_violations',
        'khr_other'
    ]
    missing_cols = [col for col in violation_cols if col not in df.columns]
    for col in missing_cols:
        df[col] = 0
    fingerprints = df[violation_cols].div(df['mjmw_lmkhlft_lmrwry_total_traffic_violations'], axis=0)
    fingerprints = fingerprints.replace([np.inf, -np.inf], 0).fillna(0)
    return fingerprints

# Initialize the Dash app
app = Dash(__name__)
cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})

# Load data
df_viola = load_json_data('viola.json')
df_viola['month'] = pd.to_datetime(df_viola['month'])
df_viola = df_viola.sort_values('month')
fingerprints = create_fingerprint(df_viola)
similarity_matrix = cosine_similarity(fingerprints)

df_accidents = pd.read_csv('facc.csv', skipinitialspace=True)
df_accidents['ZONE'] = df_accidents['ZONE'].astype(str).str.strip()
df_accidents['ZONE'] = df_accidents['ZONE'].apply(lambda x: str(int(float(x))) if x.replace('.', '').isdigit() else 'Unknown')
df_accidents['HOUR'] = df_accidents['ACCIDENT_TIME'].str.extract('(\d+)').astype(float)
current_year = df_accidents['ACCIDENT_YEAR'].max()

try:
    df_license = pd.read_csv('liz.csv', skipinitialspace=True)
    df_license['FIRST_ISSUEDATE'] = pd.to_datetime(df_license['FIRST_ISSUEDATE'])
    df_license['AGE'] = df_license['FIRST_ISSUEDATE'].dt.year - df_license['BIRTHYEAR']
    df_license['MONTH'] = df_license['FIRST_ISSUEDATE'].dt.month
    df_license['YEAR'] = df_license['FIRST_ISSUEDATE'].dt.year
except Exception as e:
    logging.error(f"Error reading liz.csv: {e}")
    df_license = pd.DataFrame(columns=['FIRST_ISSUEDATE', 'BIRTHYEAR', 'GENDER', 'NATIONALITY_GROUP'])

# App layout
app.layout = html.Div(style={
    'backgroundColor': '#000000', 
    'padding': '20px',
    'minHeight': '100vh',
    'fontFamily': 'Space Grotesk, sans-serif'
}, children=[
    html.H1('TraffiQ Dashboard', style={'color': '#00FFFF', 'textAlign': 'center', 'fontSize': '3em', 'fontWeight': 'bold'}),
    
    # Section for Traffic Violation Analysis
    html.Div(style={'backgroundColor': '#000000', 'padding': '20px', 'borderRadius': '10px', 'color': '#FFFFFF', 'border': '1px solid #333', 'marginBottom': '20px'}, children=[
        html.H2('Traffic Violation Analysis', style={'color': '#FF00FF'}),
        html.Label('Select Violation Type:', style={'fontWeight': 'bold', 'color': '#FF00FF'}),
        dcc.Dropdown(
            id='violation-type-selector',
            options=[{'label': col, 'value': col} for col in fingerprints.columns],
            value='lsr_lzy_d_lrdr_over_speed_radar',
            style={'width': '100%', 'backgroundColor': '#000000', 'color': 'black'}
        ),
        dcc.Graph(id='monthly-violation-line-chart')
    ]),
    
    # Section for Traffic Accidents Analysis
    html.Div(style={'backgroundColor': '#000000', 'padding': '20px', 'borderRadius': '10px', 'color': '#FFFFFF', 'border': '1px solid #333', 'marginBottom': '20px'}, children=[
        html.H2('Traffic Accidents Analysis', style={'color': '#FF00FF'}),
        html.Label('Select Year:', style={'fontWeight': 'bold', 'color': '#FF00FF'}),
        dcc.Dropdown(
            id='year-selector',
            options=[{'label': str(year), 'value': year} for year in sorted(df_accidents['ACCIDENT_YEAR'].unique())],
            value=current_year,
            style={'width': '100%', 'backgroundColor': '#000000', 'color': 'black'}
        ),
        dcc.Graph(id='accidents-map')
    ]),
    
    # Section for License Analysis
    html.Div(style={'backgroundColor': '#000000', 'padding': '20px', 'borderRadius': '10px', 'color': '#FFFFFF', 'border': '1px solid #333', 'marginBottom': '20px'}, children=[
        html.H2('License Analysis', style={'color': '#FF00FF'}),
        html.Label('Select Category:', style={'fontWeight': 'bold', 'color': '#FF00FF'}),
        dcc.Dropdown(
            id='license-category-selector',
            options=[{'label': 'Gender', 'value': 'GENDER'}, {'label': 'Nationality Group', 'value': 'NATIONALITY_GROUP'}],
            value='GENDER',
            style={'width': '100%', 'backgroundColor': '#000000', 'color': 'black'}
        ),
        dcc.Graph(id='license-line-chart')
    ])
])

# Callbacks
@app.callback(
    Output('monthly-violation-line-chart', 'figure'),
    [Input('violation-type-selector', 'value')]
)
def update_monthly_violation_line_chart(selected_violation):
    if selected_violation not in df_viola.columns:
        return go.Figure()
    monthly_data = df_viola.groupby([df_viola['month'].dt.year, df_viola['month'].dt.month])[selected_violation].sum().unstack(level=0)
    fig = px.line(monthly_data, title=f'Monthly {selected_violation} Violations')
    fig.update_traces(line=dict(width=4, shape='spline'))
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']),
        yaxis_title='Number of Violations',
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF'
    )
    return fig

@app.callback(
    Output('accidents-map', 'figure'),
    [Input('year-selector', 'value')]
)
def update_accidents_map(selected_year):
    year_data = df_accidents[df_accidents['ACCIDENT_YEAR'] == selected_year]
    zone_counts = year_data['ZONE'].value_counts().to_dict()
    max_count = max(zone_counts.values()) if zone_counts else 1
    colormap = cm.LinearColormap(colors=['#F5F5DC', '#B03060', '#8B0000'], vmin=0, vmax=max_count)
    m = folium.Map(location=[25.2867, 51.5333], zoom_start=11, tiles='CartoDB positron', prefer_canvas=True)
    for zone, count in zone_counts.items():
        if zone.lower() == 'unknown':
            continue
        zone_int = str(int(float(zone)))
        zone_data = zones_data.get(zone_int)
        if zone_data:
            coordinates = [[p['lat'], p['lng']] for p in zone_data['coordinates']]
            opacity = 0.2 + (count / max_count * 0.8)
            folium.Polygon(
                locations=coordinates,
                weight=0,
                fill=True,
                fill_color=colormap(count),
                fill_opacity=opacity,
                popup=f'Zone {zone_int}<br>Accidents: {count}',
                tooltip=f'Zone {zone_int}'
            ).add_to(m)
    colormap.add_to(m)
    map_path = 'assets/map.html'
    m.save(map_path)
    return open(map_path, 'r').read()

@app.callback(
    Output('license-line-chart', 'figure'),
    [Input('license-category-selector', 'value')]
)
def update_license_line_chart(selected_category):
    if selected_category not in df_license.columns:
        return go.Figure()
    license_counts = df_license.groupby([selected_category, pd.Grouper(key='FIRST_ISSUEDATE', freq='W')]).size().reset_index(name='COUNT')
    fig = px.line(license_counts, x='FIRST_ISSUEDATE', y='COUNT', color=selected_category, title=f'License Issued by {selected_category}')
    fig.update_traces(line=dict(width=3, shape='spline'))
    fig.update_layout(
        xaxis_title='Issue Date',
        yaxis_title='Number of Licenses',
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF'
    )
    return fig

if __name__ == '__main__':
    Path('assets').mkdir(exist_ok=True)
    app.run_server(debug=True)
