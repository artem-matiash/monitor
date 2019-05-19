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
        id='container',
        style = {'display': 'inline-block', 'width': '100%'}
    )
])

def parse_content(content):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

# def parse_contents(contents, filename, date):
#     content_type, content_string = contents.split(',')
#
#     decoded = base64.b64decode(content_string)
#     try:
#         if 'csv' in filename:
#             # Assume that the user uploaded a CSV file
#             df = pd.read_csv(
#                 io.StringIO(decoded.decode('utf-8')))
#         elif 'xls' in filename:
#             # Assume that the user uploaded an excel file
#             df = pd.read_excel(io.BytesIO(decoded))
#     except Exception as e:
#         print(e)
#         return html.Div([
#             'There was an error processing this file.'
#         ])
#
#     return html.Div([
#         html.H5(filename),
#         html.H6(datetime.datetime.fromtimestamp(date)),
#
#         dash_table.DataTable(
#             data=df.to_dict('records'),
#             columns=[{'name': i, 'id': i} for i in df.columns]
#         ),
#
#         html.Hr(),  # horizontal line
#
#         # For debugging, display the raw contents provided by the web browser
#         html.Div('Raw Content'),
#         html.Pre(contents[0:200] + '...', style={
#             'whiteSpace': 'pre-wrap',
#             'wordBreak': 'break-all'
#         })
#     ])


# @app.callback(Output('output-data-upload', 'children'),
#               [Input('upload-tradelog-data', 'contents'), Input('upload-price-data', 'contents')],
#               [
#                 State('upload-tradelog-data', 'filename'),
#                 State('upload-tradelog-data', 'last_modified'),
#                 State('upload-price-data', 'filename'),
#                 State('upload-price-data', 'last_modified')
#               ])
# def update_output(list_of_contents, list_of_names, list_of_dates):
#     if list_of_contents is not None:
#         children = [
#             parse_contents(c, n, d) for c, n, d in
#             zip(list_of_contents, list_of_names, list_of_dates)]
#         return children

# @app.callback(
#     dash.dependencies.Output('container-button-basic', 'children'),
#     [dash.dependencies.Input('button', 'n_clicks')],
#     [dash.dependencies.State('input-box', 'value')])
# def update_output(n_clicks, value):
#     return 'The input value was "{}" and the button has been clicked {} times'.format(
#         value,
#         n_clicks
#     )

@app.callback(
    Output('container', 'children'),
    [
        Input('button', 'n_clicks'),
        Input('upload-tradelog-data', 'contents'),
        Input('upload-price-data', 'contents')
    ]
)
def init_graphs(n_clicks, tradelog_content, price_content):
    if n_clicks > 0:
        tradelog_df = parse_content(tradelog_content)
        price_df = parse_content(price_content)

        # Crop data_df
        price_df = price_df.loc[tradelog_df.index[0]:]

        player = Player(tradelog_df, price_df)
        logs_df = player.generate_equity_curve()

        data = [
            dcc.Graph(
                id='graph-equity',
                figure={
                    'data': [
                        {
                            'x': logs_df.index,
                            'y': logs_df['equity'].values
                        }

                    ],
                    'layout': {
                        'title': 'Equity curve'
                    }
                },
                style={'height': '300px'}
            ),
            dcc.Graph(
                id='graph-price',
                figure={
                    'data': [
                        {
                            'x': price_df.index,
                            'y': price_df['price'].values
                        }
                    ],
                    'layout': {
                        'title': 'Historical prices'
                    }
                },
                style={'height': '300px'}
            )
        ]
        return html.Div(data)


if __name__ == '__main__':
    app.run_server(debug=True)
