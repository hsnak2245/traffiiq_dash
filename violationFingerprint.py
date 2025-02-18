import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px
import json

def load_json_data(filename):
    """Load data from JSON file and clean it"""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Fill NaN values with 0 for numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)
    
    print("Data shape:", df.shape)
    print("Columns with remaining NaN values:", df.isna().sum()[df.isna().sum() > 0])
    
    return df

def create_fingerprint(df):
    """Create violation fingerprints"""
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
    
    # Ensure all required columns exist
    missing_cols = [col for col in violation_cols if col not in df.columns]
    if missing_cols:
        print("Warning: Missing columns:", missing_cols)
        for col in missing_cols:
            df[col] = 0
    
    # Calculate fingerprints
    fingerprints = df[violation_cols].div(df['mjmw_lmkhlft_lmrwry_total_traffic_violations'], axis=0)
    
    # Replace any infinite values with 0
    fingerprints = fingerprints.replace([np.inf, -np.inf], 0)
    
    # Fill any remaining NaN values with 0
    fingerprints = fingerprints.fillna(0)
    
    return fingerprints

# Friendly names mapping
violation_names = {
    'lsr_lzy_d_lrdr_over_speed_radar': 'Over Speed (Radar)',
    'mkhlft_qt_lshr_ldwy_y_passing_traffic_signal_violations': 'Traffic Signal',
    'mkhlft_lrshdt_walt_ltnbyh_guidlines_and_alarm_signals_violations': 'Guidelines & Alarms',
    'mkhlft_llwht_lm_dny_metallic_plates_violations': 'Metallic Plates',
    'mkhlft_ltjwz_overtaking_violations': 'Overtaking',
    'mkhlft_tsjyl_w_dm_tjdyd_lstmr_registration_and_form_non_renewal_violations': 'Registration',
    'mkhlft_rkhs_lqyd_driving_licenses_violations': 'Licenses',
    'mkhlft_lhrk_lmrwry_traffic_movement_violations': 'Traffic Movement',
    'mkhlft_qw_d_wltzmt_lwqwf_wlntzr_stand_and_wait_rules_and_obligations_violations': 'Parking',
    'khr_other': 'Other'
}

# Initialize the Dash app
app = Dash(__name__)

try:
    # Load and prepare data
    print("Loading data...")
    df = load_json_data('qatar-monthly-statistics-traffic-violations.json')
    
    print("\nConverting dates...")
    df['month'] = pd.to_datetime(df['month'])
    df = df.sort_values('month')
    
    print("\nCreating fingerprints...")
    fingerprints = create_fingerprint(df)
    print("Fingerprint shape:", fingerprints.shape)
    
    print("\nChecking for NaN values in fingerprints:")
    print(fingerprints.isna().sum())
    
    print("\nCalculating similarity matrix...")
    similarity_matrix = cosine_similarity(fingerprints)

    # App layout
    app.layout = html.Div([
        html.H1("Qatar Traffic Violation Pattern Analysis", 
                style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        
        html.Div([
            html.Div([
                html.Label('Select Month:', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='month-selector',
                    options=[{'label': date.strftime('%B %Y'), 'value': i} 
                            for i, date in enumerate(df['month'])],
                    value=0,
                    style={'width': '100%'}
                )
            ], style={'width': '30%', 'margin': '0 auto', 'marginBottom': '20px'})
        ]),
        
        html.Div([
            html.Div([
                dcc.Graph(id='radar-chart')
            ], style={'width': '60%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='similarity-chart')
            ], style={'width': '40%', 'display': 'inline-block'})
        ]),
        
        html.Div([
            html.H3("Insights", style={'marginTop': '20px'}),
            html.P([
                "This visualization reveals the 'fingerprint' of traffic violations for each month. ",
                "The radar chart shows the proportion of each violation type, while the similarity chart ",
                "helps identify months with similar violation patterns, regardless of total volume."
            ]),
            html.P([
                "Key features to look for:",
                html.Ul([
                    html.Li("Dominant violation types (longer spokes in the radar chart)"),
                    html.Li("Seasonal patterns (similar months across years)"),
                    html.Li("Unusual months (low similarity with others)"),
                    html.Li("Long-term changes in violation patterns")
                ])
            ])
        ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
    ])

    @app.callback(
        [Output('radar-chart', 'figure'),
        Output('similarity-chart', 'figure')],
        [Input('month-selector', 'value')]
    )
    def update_graphs(selected_idx):
        if selected_idx is None:
            selected_idx = 0
            
        # Prepare radar chart data
        selected_fingerprint = fingerprints.iloc[selected_idx]
        selected_date = df['month'].iloc[selected_idx]
        
        radar_fig = go.Figure()
        radar_fig.add_trace(go.Scatterpolar(
            r=selected_fingerprint.values * 100,
            theta=[violation_names[col] for col in fingerprints.columns],
            fill='toself',
            name=selected_date.strftime('%B %Y')
        ))
        
        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(selected_fingerprint.values * 100) * 1.2]
                )),
            showlegend=True,
            title={
                'text': f"Violation Pattern for {selected_date.strftime('%B %Y')}",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            }
        )
        
        # Prepare similarity chart data
        similarities = similarity_matrix[selected_idx]
        similarity_df = pd.DataFrame({
            'Month': df['month'].dt.strftime('%B %Y'),
            'Similarity': similarities * 100
        })
        
        similarity_df = similarity_df.sort_values('Similarity', ascending=True)
        
        similarity_fig = px.bar(
            similarity_df,
            x='Similarity',
            y='Month',
            orientation='h',
            title=f'Pattern Similarity to {selected_date.strftime("%B %Y")} (%)'
        )
        
        similarity_fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_range=[0, 100],
            height=800  # Make it taller to accommodate all months
        )
        
        return radar_fig, similarity_fig
    
    if __name__ == '__main__':
        print("\nStarting server...")
        print("Once the server starts, open your web browser and go to: http://127.0.0.1:8050")
        app.run_server(debug=True)

except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
    import traceback
    print("\nFull error information:")
    print(traceback.format_exc())
