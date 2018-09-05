import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import rainevents
import plotly.graph_objs as go

app = dash.Dash()

minimum_interevent_time = '3 hours'
no_rain_threshold = 0.2 # mm/hr
rainfall_field = 'Value (Millimetres)'

#events = pd.read_csv('events.csv', index_col=0, parse_dates=True)
#selected_events = pd.read_csv('selected_events.csv', index_col=0, parse_dates=True)
#selected_events = selected_events[selected_events['Event_Total'] > 20]
#ifd = pd.read_csv('ifd.csv', index_col=0, parse_dates=True)
#ifd.index = pd.to_timedelta(ifd.index)

raw_data = rainevents.parse_raw_data(r'DataSetExport-1529644243786.csv', 'Value (Millimetres)')
events = rainevents.find_events(raw_data, minimum_interevent_time, no_rain_threshold, rainfall_field)
selected_events = rainevents.select_events(events)
selected_events = selected_events[selected_events['Event_Total'] > 20]
ifd = rainevents.ifd('table.csv')

available_events = selected_events['Event'].unique()

app.layout = html.Div([
        dcc.Graph(id='rainfall-graphic'),
        dcc.Dropdown(
                id='selected-event',
                options=[{'label': i, 'value': i} for i in available_events],
                value=available_events[0]
                ),
#        dcc.Graph(id='data-table',
#                  figure={'layout': go.Table(
#                                        header=dict(values=list(selected_events.columns),
#                                                    fill = dict(color='#C2D4FF'),
#                                                    align = ['left'] * 5),
#                                        cells=dict(values=[selected_events[c] for c in selected_events.columns],
#                                                   fill = dict(color='#F5F8FF'),
#                                                   align = ['left'] * 5))
#                         })
                ])

@app.callback(
    dash.dependencies.Output('rainfall-graphic', 'figure'),
    [dash.dependencies.Input('selected-event', 'value')]
    )
def update_graph(selected_event):
    dff = events[events['Event'] == selected_event]
    dff['Cumulative'] = dff[rainfall_field].cumsum()
    
    ifds = [go.Scatter(x=ifd.index.values / np.timedelta64(1, 'm'), y=ifd[c], mode='lines+markers', name=c, line=dict(shape='spline'), marker=dict(symbol='triangle')) for c in ifd.columns]
    
    bursts = rainevents.storm_bursts(dff, 5, 180, rainfall_field, step=5)

    actual = [go.Scatter(x=bursts.index.values / np.timedelta64(1, 'm'), 
                         y=bursts['Max_Intensity'], name='Actual Storm')]
    
    raw = [go.Bar(x=dff.index, y=dff[rainfall_field], 
              xaxis='x2', yaxis='y2', name='Raw Rainfall')]
    
    cumulative = [go.Scatter(x=dff.index, y=dff['Cumulative'], 
                     xaxis='x2', yaxis='y3', name='Cumulative Rainfall')]
    
    data = ifds + actual + raw + cumulative

    return {
        'data': data,
        'layout': go.Layout(
                            xaxis=dict(
                                range=[0,185],
                                title='Storm Duration (minutes)',
                                domain=[0,0.4],
                                position=0
                            ),
                            yaxis=dict(
                                range=[0,max(max(bursts['Max_Intensity']*1.2), ifd.values.max())],
                                title='Rainfall Intensity (mm/hr)',
                                domain=[0.02,1]
                            ),
                            xaxis2=dict(
                                title='Date & Time',
                                domain=[0.5,0.9],
                                autorange=True,
                                position=0
                            ),
                            yaxis2=dict(
                                title='Raw Rainfall (mm)',
                                anchor='x2',
                                domain=[0.02,1],
                                autorange=True
                            ),
                            yaxis3=dict(
                                title='Cumulative Rainfall (mm)',
                                domain=[0,1],
                                range=[0,max(dff['Cumulative'])*1.05],
                                overlaying='y2',
                                side='right',
                                showgrid=False,
                                position=0.92
                            )
                        )
    }


if __name__ == '__main__':
    app.run_server()