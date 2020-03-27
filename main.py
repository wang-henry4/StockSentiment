import datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from database import db, Ema_data


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('Sentiment Feed'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=5*1000, # in milliseconds
            n_intervals=0
        )
    ])
)

data = Ema_data()

@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics(n):
    latest = db.averages.find_one({"latest": True})
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('EMA: {0:.2f}'.format(latest["ema"]), style=style)
    ]

# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    data.update()
    ema, time = data.data
    # Create the graph with subplots
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=ema,
                    mode='lines+markers',
                    name='lines+markers'))
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)