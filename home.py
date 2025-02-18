import dash
from dash import dcc, html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

app.layout = html.Div(style={
    'backgroundColor': '#111111',
    'padding': '20px',
    'minHeight': '100vh',
    'fontFamily': 'Space Grotesk, sans-serif',
    'textAlign': 'center'
}, children=[
    html.H1('TraffiQ', style={
        'color': '#00FFFF',
        'fontSize': '4em',
        'marginBottom': '20px'
    }),
    dcc.Input(
        placeholder='Search...',
        type='text',
        style={
            'width': '50%',
            'padding': '10px',
            'borderRadius': '5px',
            'border': 'none',
            'marginBottom': '20px'
        }
    ),
    html.Div(style={
        'display': 'flex',
        'justifyContent': 'center',
        'gap': '20px',
        'flexWrap': 'wrap'
    }, children=[
        html.A(html.Button(style={
            'backgroundColor': '#222',
            'color': '#FFFFFF',
            'padding': '15px 30px',
            'border': 'none',
            'borderRadius': '5px',
            'fontSize': '1.2em',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px'
        }, children=[
            html.I(className='fas fa-car-crash'),
            'Accidents'
        ]), href='/accidents'),
        html.A(html.Button(style={
            'backgroundColor': '#222',
            'color': '#FFFFFF',
            'padding': '15px 30px',
            'border': 'none',
            'borderRadius': '5px',
            'fontSize': '1.2em',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px'
        }, children=[
            html.I(className='fas fa-id-card'),
            'License'
        ]), href='/license'),
        html.Button(style={
            'backgroundColor': '#222',
            'color': '#FFFFFF',
            'padding': '15px 30px',
            'border': 'none',
            'borderRadius': '5px',
            'fontSize': '1.2em',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px'
        }, children=[
            html.I(className='fas fa-exclamation-triangle'),
            'Violations'
        ]),
        html.Button(style={
            'backgroundColor': '#222',
            'color': '#FFFFFF',
            'padding': '15px 30px',
            'border': 'none',
            'borderRadius': '5px',
            'fontSize': '1.2em',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px'
        }, children=[
            html.I(className='fas fa-car'),
            'Vehicle'
        ]),
        html.Button(style={
            'backgroundColor': '#222',
            'color': '#FFFFFF',
            'padding': '15px 30px',
            'border': 'none',
            'borderRadius': '5px',
            'fontSize': '1.2em',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px'
        }, children=[
            html.I(className='fas fa-plane-departure'),
            'Immigration'
        ])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
