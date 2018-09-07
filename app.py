import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# import pandas as pd
import numpy as np
import xprafts
import plotly.graph_objs as go
from flask_cache import Cache
import base64

app = dash.Dash(__name__)
cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})

# rafts_file = r'example_files\Pallara_DEV01.loc'
# events_file = r'example_files\event_names.txt'

# # def parse_contents(rafts_file, events_file):
# rafts_data, event_times, events = xprafts.parse_rafts_file(rafts_file, events_file)

table = html.Div([
            html.Tr([
                dcc.Markdown('Select XP-RAFTS and event names files:'),
                dcc.Upload(
                    id='rafts-file-1',
                    children=html.Div([
                        'RAFTS File: Drag & Drop or ',
                        html.A('Select')
                    ]),
                    style={
                        'width': '100%',
                        'height': '30px',
                        'lineHeight': '30px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    }
                ),
                dcc.Upload(
                    id='events-file-1',
                    children=html.Div([
                        'Event File: Drag & Drop or ',
                        html.A('Select')
                    ]),
                    style={
                        'width': '100%',
                        'height': '30px',
                        'lineHeight': '30px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    }
                )
            ]),
            html.Tr(
                [html.Th('Hydrograph 1'), html.Th('Hydrograph 2')]
            ),
            html.Tr([
                html.Td([
                    dcc.Markdown('Select event and node:'),
                    dcc.Dropdown(
                            id='selected-event-1',
                            options=[{'Events file not uploaded.': None}],
                            value='Events file not uploaded.'
                    ),
                    dcc.Dropdown(
                            id='selected-node-1',
                            options={'RAFTS file not uploaded.': None},
                            value='RAFTS file not uploaded.'
                    )
                ]),
                html.Td([
                    dcc.Markdown('Select event and node:'),
                    dcc.Dropdown(
                            id='selected-event-2',
                            options=[{'Events file not uploaded.': None}],
                            value='Events file not uploaded.'
                    ),
                    dcc.Dropdown(
                            id='selected-node-2',
                            options=[{'RAFTS file not uploaded.': None}],
                            value='RAFTS file not uploaded.'
                    )
                ])
            ])
        ])

main = html.Div([
        # html.H3('XP-RAFTS Hydrographs'),
        dcc.Graph(
            id='xprafts-hydrographs',
            style={'width': '95vw', 'height': '65vh'}
        ),
        table,
        html.Div(id='rafts-file-1-signal', style={'display': 'none'}),
        html.Div(id='events-file-1-signal', style={'display': 'none'}),
        # html.Div(id='rafts-data-2', style={'display': 'none'}),
        # html.Div(id='events-2', style={'display': 'none'})
    ])

app.layout = main

@app.callback(
    dash.dependencies.Output('xprafts-hydrographs', 'figure'),
    [dash.dependencies.Input('selected-event-1', 'value'),
     dash.dependencies.Input('selected-node-1', 'value'),
     dash.dependencies.Input('selected-event-2', 'value'),
     dash.dependencies.Input('selected-node-2', 'value'),
     dash.dependencies.Input('rafts-file-1-signal', 'children'),
     dash.dependencies.Input('events-file-1-signal', 'children')]
    )
def update_graph(selected_event_1, selected_node_1, 
                 selected_event_2, selected_node_2,
                 rafts_file_1, events_file_1):

    rafts_data, event_times = global_store_rafts_file(rafts_file_1)
    events = global_store_events_file(events_file_1)

    data = []
    max_time, max_flow = np.timedelta64(0, 'm'), 0
    for event, node in zip([selected_event_1, selected_event_2],
                           [selected_node_1, selected_node_2]):

        times = event_times[event]
        flows = rafts_data[event][node]

        max_time = max(max_time, *times)
        max_flow = max(max_flow, *flows)

        data.append(go.Scatter(x=times / np.timedelta64(1, 'm'), 
                            y=flows, name='{0} {1}'.format(node,
                                events[event])))

    return {
        'data': data,
        'layout': go.Layout(
                            xaxis=dict(
                                range=[0,max_time/np.timedelta64(1, 'm')],
                                title='Time (minutes)',
                                # domain=[0,1],
                                position=0
                            ),
                            yaxis=dict(
                                range=[0,max_flow*1.1],
                                title='Discharge (m3/s)',
                                # domain=[0.0,1]
                            ),
                            legend=go.Legend(
                                orientation='h'
                                # x=0.5, y=0.9
                                ),
                            margin={'l':65, 'b': 40, 't': 10, 'r': 0},
                            # height=600
                        )
    }

@app.callback(
    Output('rafts-file-1-signal', 'children'),
    [Input('rafts-file-1', 'contents'),
     Input('rafts-file-1', 'filename')]
    )
def parse_uploaded_rafts_file(rafts_file_contents, rafts_file_name):
    content_type, content_string = rafts_file_contents.split(',')
    decoded_rafts_file_data = base64.b64decode(content_string)

    global_store_rafts_file(decoded_rafts_file_data)
    return rafts_file_name

@cache.memoize()
def global_store_rafts_file(decoded_rafts_file_data):
    rafts_data, event_times = xprafts.parse_rafts_file(decoded_rafts_file_data)
    return rafts_data, event_times

@app.callback(
    Output('events-file-1-signal', 'children'),
    [Input('events-file-1', 'contents'),
     Input('events-file-1', 'filename')]
    )
def parse_uploaded_events_file(events_file_contents, events_file_name):
    content_type, content_string = events_file_contents.split(',')
    decoded_events_file_data = base64.b64decode(content_string)

    global_store_events_file(decoded_events_file_data)
    return events_file_name

@cache.memoize()
def global_store_events_file(events_file_data):
    events = xprafts.parse_events_file(events_file_data)
    return events

@app.callback(
    dash.dependencies.Output('selected-event-1', 'options'),
    [dash.dependencies.Input('events-file-1-signal', 'children')]
    )
def update_event_dropdown_1(events_file_1):
    events = global_store_events_file(events_file_1)
    return [{'label': val, 'value': key} for key, val in events.iteritems()]

@app.callback(
    dash.dependencies.Output('selected-node-1', 'options'),
    [dash.dependencies.Input('rafts-file-1-signal', 'children')]
    )
def update_event_dropdown_1(rafts_file_1):
    rafts_data, _ = global_store_rafts_file(rafts_file_1)
    return [{'label': key, 'value': key} for key in rafts_data[1].keys()]

@app.callback(
    dash.dependencies.Output('selected-event-2', 'options'),
    [dash.dependencies.Input('events-file-1-signal', 'children')]
    )
def update_event_dropdown_2(events_file_1):
    events = global_store_events_file(events_file_1)
    return [{'label': val, 'value': key} for key, val in events.iteritems()]

@app.callback(
    dash.dependencies.Output('selected-node-2', 'options'),
    [dash.dependencies.Input('rafts-file-1-signal', 'children')]
    )
def update_event_dropdown_2(rafts_file_1):
    rafts_data, _ = global_store_rafts_file(rafts_file_1)
    return [{'label': key, 'value': key} for key in rafts_data[1].keys()]

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})
app.title = 'XP-RAFTS Hydrograph Viewer'

if __name__ == '__main__':
    app.run_server(debug=True)
