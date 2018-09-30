import base64
import copy
import os
import json
import io

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from flask_caching import Cache
import redis

import xprafts

app = dash.Dash(__name__)
server = app.server

CACHE_CONFIG = {
    # 'CACHE_TYPE': 'simple',
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'localhost:6379')
}
cache = Cache()
cache.init_app(server, config=CACHE_CONFIG)

r = redis.from_url(CACHE_CONFIG['CACHE_REDIS_URL'])

main = html.Div([
        html.Table([
            html.Tr([
                html.Td([
                    dcc.Graph(
                    id='xprafts-hydrographs',
                    style={'width': '65vw', 'height': '95vh'}
                    )
                ]),
                html.Td([
                    html.Tr([
                        html.Td([
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
                        ], colSpan=2)
                    ]),
                    html.Tr([
                        html.Th('Hydrograph 1'), html.Th('Hydrograph 2')
                    ]),
                    html.Tr([
                        html.Td([
                            dcc.Markdown('Select event and node:'),
                            dcc.Dropdown(
                                    id='selected-event-1',
                                    # options=[{'Events file not uploaded.': None}],
                                    # value='Events file not uploaded.'
                            ),
                            dcc.Dropdown(
                                    id='selected-node-1',
                                    # options={'RAFTS file not uploaded.': None},
                                    # value='RAFTS file not uploaded.'
                            )
                        ]),
                        html.Td([
                            dcc.Markdown('Select event and node:'),
                            dcc.Dropdown(
                                    id='selected-event-2',
                                    # options=[{'Events file not uploaded.': None}],
                                    # value='Events file not uploaded.'
                            ),
                            dcc.Dropdown(
                                    id='selected-node-2',
                                    # options=[{'RAFTS file not uploaded.': None}],
                                    # value='RAFTS file not uploaded.'
                            )
                        ])
                    ])
                ], style={'vertical-align': 'top'}),
            ]),
        ]),
        html.Div(id='rafts-file-1-signal', style={'display': 'none'}),
        html.Div(id='events-file-1-signal', style={'display': 'none'}),
    ])

app.layout = main

def generate_chart_data(event, node, events, rafts_data, 
                        event_times, data, max_time, max_flow):

    times = pd.TimedeltaIndex(event_times[event])
    flows = rafts_data[event][node]

    max_time = max(max_time, *times)
    max_flow = max(max_flow, *flows)

    data.append(go.Scatter(x=times / np.timedelta64(1, 'm'), 
                        y=flows, name='{0} {1}'.format(node,
                            events[event])))

    return data, max_time, max_flow

@app.callback(
    dash.dependencies.Output('xprafts-hydrographs', 'figure'),
    [dash.dependencies.Input('selected-event-1', 'value'),
     dash.dependencies.Input('selected-node-1', 'value'),
     dash.dependencies.Input('selected-event-2', 'value'),
     dash.dependencies.Input('selected-node-2', 'value')],
    [dash.dependencies.State('rafts-file-1-signal', 'children'),
     dash.dependencies.State('events-file-1-signal', 'children')]
    )
def update_graph(selected_event_1, selected_node_1, 
                 selected_event_2, selected_node_2,
                 rafts_file_1, events_file_1):

    data = []
    max_time, max_flow = np.timedelta64(0, 'm'), 0

    if rafts_file_1 is not None:
        rafts_data = get_from_redis('rafts_data')
        event_times = get_from_redis('event_times')
    if events_file_1 is not None:
        events = get_from_redis('events')

    if rafts_file_1 and events_file_1:

        if selected_event_1 and selected_node_1:
            data, max_time, max_flow = generate_chart_data(
                selected_event_1, selected_node_1, events, rafts_data, 
                event_times, data, max_time, max_flow)

        if selected_event_2 and selected_node_2:
            data, max_time, max_flow = generate_chart_data(
                selected_event_2, selected_node_2, events, rafts_data, 
                event_times, data, max_time, max_flow)

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
    else:
        return {}

@app.callback(
    Output('rafts-file-1-signal', 'children'),
    [Input('rafts-file-1', 'contents'),
     Input('rafts-file-1', 'filename')]
    )
def parse_uploaded_rafts_file(rafts_file_contents, rafts_file_name):
    if rafts_file_contents is not None:
        rafts_content_type, rafts_content_string = rafts_file_contents.split(',')

        decoded_rafts_file_data = base64.b64decode(rafts_content_string)
        with io.StringIO(decoded_rafts_file_data.decode('utf-8')) as infile:
            rafts_data, event_times = xprafts.parse_rafts_file(infile)

        r.set('rafts_data', json.dumps(rafts_data, default=str))
        r.set('event_times', json.dumps(event_times, default=str))

        return 'rafts'
    else:
        return None

@app.callback(
    Output('events-file-1-signal', 'children'),
    [Input('events-file-1', 'contents'),
     Input('events-file-1', 'filename')]
    )
def parse_uploaded_events_file(events_file_contents, events_file_name):
    if events_file_contents is not None:
        events_content_type, events_content_string = events_file_contents.split(',')

        decoded_events_file_data = base64.b64decode(events_content_string)
        with io.StringIO(decoded_events_file_data.decode('utf-8')) as infile:
            events = xprafts.parse_events_file(infile)

        r.set('events', json.dumps(events, default=str))
        
        return 'events'
    else:
        return None

@cache.memoize()
def get_from_redis(name):
    return json.loads(r.get(name))

@app.callback(
    dash.dependencies.Output('selected-event-1', 'options'),
    [dash.dependencies.Input('events-file-1-signal', 'children')]
    )
def update_event_dropdown_1(events_file_1):
    events = get_from_redis('events')
    return [{'label': val, 'value': key} for key, val in events.items()]

@app.callback(
    dash.dependencies.Output('selected-node-1', 'options'),
    [dash.dependencies.Input('rafts-file-1-signal', 'children')]
    )
def update_node_dropdown_1(rafts_file_1):
    rafts_data = get_from_redis('rafts_data')
    return [{'label': key, 'value': key} for key in rafts_data['1'].keys()]

@app.callback(
    dash.dependencies.Output('selected-event-2', 'options'),
    [dash.dependencies.Input('events-file-1-signal', 'children')]
    )
def update_event_dropdown_2(events_file_1):
    events = get_from_redis('events')
    return [{'label': val, 'value': key} for key, val in events.items()]

@app.callback(
    dash.dependencies.Output('selected-node-2', 'options'),
    [dash.dependencies.Input('rafts-file-1-signal', 'children')]
    )
def update_node_dropdown_2(rafts_file_1):
    rafts_data = get_from_redis('rafts_data')
    return [{'label': key, 'value': key} for key in rafts_data['1'].keys()]

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})
app.title = 'XP-RAFTS Hydrograph Viewer'

if __name__ == '__main__':
    app.run_server(debug=True)
