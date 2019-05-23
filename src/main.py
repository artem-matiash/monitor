import base64
import datetime
import io

import dash
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from player import Player

import pandas as pd

# GLOBAL DF
price_df = None
logs_df = None
tradelog_df = None

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Upload(
        id='upload-tradelog-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Tradelog File')
        ]),
        style={
            'width': '40%',
            'height': '10%',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'float': 'left',
            'position': 'relative'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    dcc.Upload(
        id='upload-price-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Historical Price File')
        ]),
        style={
            'width': '40%',
            'height': '10%',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'float': 'right',
            'position': 'relative'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    html.Button(
        'Start',
        id='button',
        style={
            'width': '10%',
            'float': 'center',
            'height': '10%',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderRadius': '5px',
            'textAlign': 'center',
            'left': '5%',
            'position': 'relative'
        },
        n_clicks=0
    ),
    html.Div(
        [
            dcc.Graph(
                id='graph-equity',
                style={'height': '250px'}
            ),
            dcc.Graph(
                id='graph-price',
                style={'height': '250px'}
            ),
            html.Div(
                dcc.Slider(
                    id='year-slider'
                ),
                id='slider-container'
            )
        ],
        id='container',
        style = {
            'display': 'inline-block',
            'textAlign': 'center',
            'width': '75%',
            'margin-left': '3%'
        }
    )
])

def parse_content(content):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

@app.callback(
    [
        Output('graph-equity', 'figure'),
        Output('graph-price', 'figure')
    ],
    [
        Input('year-slider', 'value')
    ]
)
def update_graph(value):
    if price_df is not None and logs_df is not None:
        price_df_last_year = price_df.loc[pd.Timestamp(value, 1, 1):pd.Timestamp(value, 12, 31)]
        logs_df_last_year = logs_df.loc[pd.Timestamp(value, 1, 1):pd.Timestamp(value, 12, 31)]

        price_df_stripped = price_df.loc[:pd.Timestamp(value, 1, 1)]
        logs_df_stripped = logs_df.loc[:pd.Timestamp(value, 1, 1)]

        equity = figure={
            'data': [
                {
                    'x': logs_df_stripped.index,
                    'y': logs_df_stripped['equity'].values,
                    'name': 'Previous Equity'
                },
                {
                    'x': logs_df_last_year.index,
                    'y': logs_df_last_year['equity'].values,
                    'marker': {
                        'color': 'green'
                    },
                    'name': 'Current Year'
                }
            ],
            'layout': {
                'title': 'Equity curve'
            }
        }
        price = figure={
            'data': [
                {
                    'x': price_df_stripped.index,
                    'y': price_df_stripped['price'].values,
                    'name': 'Previous Prices'
                },
                {
                    'x': price_df_last_year.index,
                    'y': price_df_last_year['price'].values,
                    'marker': {
                        'color': 'green'
                    },
                    'name': 'Current Year'
                }
            ],
            'layout': {
                'title': 'Historical prices'
            }
        }
        return equity, price
    else:
        return {}, {}

@app.callback(
    Output('slider-container', 'children'),
    [
        Input('button', 'n_clicks'),
        Input('upload-tradelog-data', 'contents'),
        Input('upload-price-data', 'contents')
    ]
)
def init_graphs(n_clicks, tradelog_content, price_content):
    if n_clicks > 0:
        global tradelog_df, price_df, logs_df
        tradelog_df = parse_content(tradelog_content)
        price_df = parse_content(price_content)

        # Crop data_df
        price_df = price_df.loc[tradelog_df.index[0]:]

        player = Player(tradelog_df, price_df)
        logs_df = player.generate_equity_curve()

        # Slider info
        months = price_df.index.map(lambda x: x.replace(day=1)).unique()
        years = price_df.index.map(lambda x: x.year).unique()

        data = [
            dcc.Slider(
                id='year-slider',
                min=years.min(),
                max=years.max(),
                marks={str(year): str(year) for year in years},
                step=None,
                value=years.max()
            )
        ]
        return html.Div(
            data
        )


if __name__ == '__main__':
    app.run_server(debug=True)
