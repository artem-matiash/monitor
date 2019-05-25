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
from textwrap import dedent

import pandas as pd
import numpy as np

# Assumptions
base = 1e6

# GLOBAL DF
price_df = None
logs_df = None
tradelog_df = None

def human_format(num):
    if num is None:
        return ""
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

def format_stats(sharpe=None, dif_return=None, roi=None, vol=None):
    str_sharpe = "{0:.2f}".format(sharpe) if sharpe is not None else ""
    str_dif_return = human_format(dif_return)
    str_roi = "{:.1%}".format(roi) if roi is not None else ""
    str_vol = "{0:.2f}".format(vol) if vol is not None else ""
    return dedent('''
        #### **Annual Statistics**
        * Sharpe Ratio: {}
        * Differential return: {}
        * ROI: {}
        * Volatility: {}
    '''.format(str_sharpe, str_dif_return, str_roi, str_vol))

def form_advice():
    return dedent('''
        #### **Advice**
        * Trend:
        *
    '''.format())

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
                style={'height': '275px'}
            ),
            dcc.Graph(
                id='graph-price',
                style={'height': '275px'}
            ),
            html.Div(
                dcc.Slider(
                    id='year-slider'
                ),
                id='slider-container',
                style={
                    'margin-left': '5%'
                }
            )
        ],
        id='container',
        style={
            'display': 'inline-block',
            'textAlign': 'center',
            'width': '75%',
            'float': 'left',
            'margin-left': '3%'
        }
    ),
    dcc.Markdown(
        format_stats(),
        id='text'
    ),
    dcc.Markdown(
        form_advice(),
        id='advice'
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
        Output('graph-price', 'figure'),
        Output('text', 'children'),
        Output('advice', 'children')
    ],
    [
        Input('year-slider', 'value')
    ]
)
def update_graph(value):
    if price_df is not None and logs_df is not None and value is not None:
        price_df_last_year = price_df.loc[pd.Timestamp(value, 1, 1):pd.Timestamp(value + 1, 1, 1)]
        logs_df_last_year = logs_df.loc[pd.Timestamp(value, 1, 1):pd.Timestamp(value + 1, 1, 1)]

        price_df_stripped = price_df.loc[:pd.Timestamp(value, 1, 1)]
        logs_df_stripped = logs_df.loc[:pd.Timestamp(value, 1, 1)]
        tradelog_df_stripped = tradelog_df.loc[:pd.Timestamp(value + 1, 1, 1)]
        color = 'green' if logs_df_last_year['equity'].iloc[-1] >= logs_df_last_year['equity'].iloc[0] else 'red'

        equity = figure={
            'data': [
                {
                    'x': logs_df_stripped.index,
                    'y': logs_df_stripped['equity'].values,
                    'marker': {
                        'color': 'black'
                    },
                    'name': 'Previous Equity'
                },
                {
                    'x': logs_df_last_year.index,
                    'y': logs_df_last_year['equity'].values,
                    'marker': {
                        'color': color
                    },
                    'name': 'Current Year'
                },
                {
                    'x': tradelog_df_stripped[tradelog_df_stripped['side'] == 'BUY'].index,
                    'y': logs_df[logs_df.index.isin(tradelog_df_stripped[tradelog_df_stripped['side'] == 'BUY'].index)]['equity'].values,
                    'mode': 'markers',
                    'marker': {
                        'color': 'green'
                    },
                    'name': 'BUY Signal'
                },
                {
                    'x': tradelog_df_stripped[tradelog_df_stripped['side'] == 'SELL'].index,
                    'y': logs_df[logs_df.index.isin(tradelog_df_stripped[tradelog_df_stripped['side'] == 'SELL'].index)]['equity'].values,
                    'mode': 'markers',
                    'marker': {
                        'color': 'red'
                    },
                    'name': 'SELL Signal'
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
                    'marker': {
                        'color': 'black'
                    },
                    'name': 'Previous Prices'
                },
                {
                    'x': price_df_last_year.index,
                    'y': price_df_last_year['price'].values,
                    'marker': {
                        'color': color
                    },
                    'name': 'Current Year'
                },
                {
                    'x': tradelog_df_stripped[tradelog_df_stripped['side'] == 'BUY'].index,
                    'y': price_df[price_df.index.isin(tradelog_df_stripped[tradelog_df_stripped['side'] == 'BUY'].index)]['price'].values,
                    'mode': 'markers',
                    'marker': {
                        'color': 'green'
                    },
                    'name': 'BUY Signal'
                },
                {
                    'x': tradelog_df_stripped[tradelog_df_stripped['side'] == 'SELL'].index,
                    'y': price_df[price_df.index.isin(tradelog_df_stripped[tradelog_df_stripped['side'] == 'SELL'].index)]['price'].values,
                    'mode': 'markers',
                    'marker': {
                        'color': 'red'
                    },
                    'name': 'SELL Signal'
                }
            ],
            'layout': {
                'title': 'Historical prices'
            }
        }

        # Calculate statistics
        returns = logs_df_last_year['equity'].pct_change().fillna(0)#(logs_df_last_year['equity'] - logs_df_last_year['equity'].shift(1)).dropna() / base
        sharpe = returns.mean() / returns.std() * np.sqrt(252 / len(logs_df_last_year.index))
        dif_return = (logs_df_last_year['equity'].iloc[-1] - logs_df_last_year['equity'].iloc[0]) * 252 / len(logs_df_last_year.index)
        roi = dif_return / base
        vol = returns.std() * np.sqrt(252 / len(logs_df_last_year.index))
        stats = format_stats(sharpe, dif_return, roi, vol)

        # Form an advice
        advice = None
        return equity, price, stats, advice
    else:
        return {}, {}, format_stats(), form_advice()

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

        player = Player(tradelog_df, price_df, base)
        logs_df = player.generate_equity_curve()
        logs_df.to_csv("../results/logs.csv")

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
