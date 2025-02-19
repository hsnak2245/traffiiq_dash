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
    df = load_json_data('viola.json')
    
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
    app.layout = html.Div(style={
        'backgroundColor': '#000000', 
        'padding': '20px',
        'minHeight': '100vh',
        'fontFamily': 'Space Grotesk, sans-serif'
    }, children=[
        html.Div(style={
            'backgroundColor': '#800000',  # Maroon
            'padding': '10px',
            'borderRadius': '5px'
        }, children=[
            html.H1("Qatar Traffic Violation Pattern Analysis", 
                    style={'color': '#F5F5DC', 'textAlign': 'center', 'fontSize': '3em', 'fontWeight': 'bold'})  # Beige
        ]),
        
        # New section for monthly violation line chart
        html.Div(style={
            'backgroundColor': '#000000',
            'padding': '20px',
            'borderRadius': '10px',
            'color': '#FFFFFF',
            'border': '1px solid #333',
            'marginBottom': '20px'
        }, children=[
            html.H3('Monthly Violation Line Chart', style={'color': '#FF00FF'}),
            html.Label('Select Violation Type:', style={'fontWeight': 'bold', 'color': '#FF00FF'}),
            dcc.Dropdown(
                id='violation-type-selector',
                options=[{'label': violation_names[col], 'value': col} for col in violation_names.keys()],
                value='lsr_lzy_d_lrdr_over_speed_radar',
                style={'width': '100%', 'backgroundColor': '#000000', 'color': 'black'}
            ),
            dcc.Graph(id='monthly-violation-line-chart')
        ]),
        
        html.Div(style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'gap': '20px',
            'margin': '20px 0'
        }, children=[
            html.Div(style={
                'flex': '1 1 100%',
                'backgroundColor': '#000000',
                'padding': '20px',
                'borderRadius': '10px',
                'color': '#FFFFFF',
                'border': '1px solid #333'
            }, children=[
                html.Label('Select Month:', style={'fontWeight': 'bold', 'color': '#FF00FF'}),
                dcc.Dropdown(
                    id='month-selector',
                    options=[{'label': date.strftime('%B %Y'), 'value': i} for i, date in enumerate(df['month'])],
                    value=0,
                    style={'width': '100%', 'backgroundColor': '#000000', 'color': 'black'}
                )
            ])
        ]),
        
        html.Div(style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'gap': '20px',
            'margin': '20px 0'
        }, children=[
            html.Div(style={
                'flex': '1',
                'minWidth': '300px',
                'backgroundColor': '#000000',
                'padding': '20px',
                'borderRadius': '10px',
                'color': '#FFFFFF',
                'border': '1px solid #333'
            }, children=[
                html.H3('Violation Pattern Pareto Chart', style={'color': '#FF00FF'}),
                dcc.Graph(id='pareto-chart')
            ]),
            
            html.Div(style={
                'flex': '1',
                'minWidth': '300px',
                'backgroundColor': '#000000',
                'padding': '20px',
                'borderRadius': '10px',
                'color': '#FFFFFF',
                'border': '1px solid #333',
                'maxHeight': '500px',
                'overflowY': 'scroll'
            }, children=[
                html.H3('Pattern Similarity Results', style={'color': '#FF00FF'}),
                html.Div(id='similarity-results', style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'})
            ])
        ]),
        
        html.Div(style={
            'backgroundColor': '#000000',
            'padding': '20px',
            'borderRadius': '10px',
            'color': '#FFFFFF',
            'border': '1px solid #333'
        }, children=[
            html.H3("Insights", style={'color': '#FF00FF'}),
            html.P([
                "This visualization reveals the 'fingerprint' of traffic violations for each month. ",
                "The Pareto chart shows the proportion of each violation type, while the similarity results ",
                "help identify months with similar violation patterns, regardless of total volume."
            ]),
            html.P([
                "Key features to look for:",
                html.Ul([
                    html.Li("Dominant violation types (longer bars in the Pareto chart)"),
                    html.Li("Seasonal patterns (similar months across years)"),
                    html.Li("Unusual months (low similarity with others)"),
                    html.Li("Long-term changes in violation patterns")
                ])
            ])
        ])
    ])

    @app.callback(
        [Output('pareto-chart', 'figure'),
        Output('similarity-results', 'children')],
        [Input('month-selector', 'value')]
    )
    def update_graphs(selected_idx):
        if selected_idx is None:
            selected_idx = 0
            
        # Prepare Pareto chart data
        selected_fingerprint = fingerprints.iloc[selected_idx]
        selected_date = df['month'].iloc[selected_idx]
        
        sorted_fingerprint = selected_fingerprint.sort_values(ascending=False)
        
        pareto_fig = go.Figure()
        pareto_fig.add_trace(go.Bar(
            x=[violation_names[col] for col in sorted_fingerprint.index],
            y=sorted_fingerprint.values * 100,
            name='Violation Percentage',
            marker_color='#FF00FF'
         ))
        
        pareto_fig.update_layout(
            title={
                'text': f"Violation Pattern for {selected_date.strftime('%B %Y')}",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title='Violation Type',
            yaxis_title='Percentage (%)',
            showlegend=True,
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font_color='#FFFFFF'
        )
        
        # Prepare similarity results data
        similarities = similarity_matrix[selected_idx]
        similarity_df = pd.DataFrame({
            'Month': df['month'].dt.strftime('%B %Y'),
            'Similarity': similarities * 100
        })
        
        similarity_df = similarity_df.sort_values('Similarity', ascending=False)
        
        similarity_results = [
            html.Div(style={
                'backgroundColor': '#111111',
                'padding': '10px',
                'borderRadius': '5px',
                'border': '1px solid #333',
                'color': '#FFFFFF'
            }, children=[
                html.H4(f"{row['Month']}", style={'margin': '0'}),
                html.P(f"Similarity: {row['Similarity']:.2f}%", style={'margin': '0'})
            ])
            for _, row in similarity_df.iterrows()
        ]
        
        return pareto_fig, similarity_results

    @app.callback(
        Output('monthly-violation-line-chart', 'figure'),
        [Input('violation-type-selector', 'value')]
    )
    def update_monthly_violation_line_chart(selected_violation):
        if selected_violation not in df.columns:
            return go.Figure()  # Return an empty figure if column is missing
        
        monthly_data = df.groupby([df['month'].dt.year, df['month'].dt.month])[selected_violation].sum().unstack(level=0)
        fig = px.line(monthly_data, title=f'Monthly {violation_names[selected_violation]} Violations')
        
        fig.update_traces(line=dict(width=4, shape='spline'))  # Thicker and smoother lines
        
        fig.update_layout(
            xaxis=dict(
                title='Month',
                tickmode='array',
                tickvals=list(range(1, 13)),
                ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            ),
            yaxis_title='Number of Violations',
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font_color='#FFFFFF'
        )
        
        return fig
    
    if __name__ == '__main__':
        print("\nStarting server...")
        print("Once the server starts, open your web browser and go to: http://127.0.0.1:8050")
        app.run_server(debug=True)

except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
    import traceback
    print("\nFull error information:")
    print(traceback.format_exc())