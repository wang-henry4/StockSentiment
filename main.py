import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from database import get_db
from datetime import datetime

class data_getter():
    def __init__(self, max_size=1800):
        self.max_size = max_size
        self._data = self.populate()
        self.db = get_db()

    def populate(self):
        query = self.db.averages.find().sort("time", -1).limit(self.max_size)
        return [(d["MovingAvg"], d["time"]) for d in query][::-1]
        
    def update(self):
        self._data = self.populate()

    @property
    def data(self):
        return list(zip(*self._data))

db = get_db()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('Sentiment Feed'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=120*1000, # in milliseconds
            n_intervals=0
        )
    ])
)

data = data_getter()

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
    app.run_server(debug=True, host='0.0.0.0')