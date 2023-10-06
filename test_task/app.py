from dash import html, Output, Input, State, dcc
from dash.html import Div
from dash_extensions.enrich import (DashProxy,
                                    ServersideOutputTransform,
                                    MultiplexerTransform)
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime, timedelta

CARD_STYLE = dict(withBorder=True,
                  shadow="sm",
                  radius="md",
                  style={'height': '400px'})


class EncostDash(DashProxy):
    def __init__(self, **kwargs):
        self.app_container = None
        super().__init__(transforms=[ServersideOutputTransform(),
                                     MultiplexerTransform()], **kwargs)


"""
    Запрос из базы данных
"""
engine = create_engine("sqlite:///../testDB.db")
query = """
SELECT *
FROM sources
"""
df = pd.read_sql(query, con=engine)

"""
    Цветовая схема
"""
color_map = dict(zip(df['reason'], df['color']))

app = EncostDash(name=__name__)


def get_date() -> datetime:
    """
    Преобразование даты/времени
    :return:
    """
    time_str = df.shift_begin[0]
    date_str = df.calendar_day[0]
    time = datetime.strptime(time_str, '%H:%M:%S')
    date = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_datetime = time.replace(year=date.year,
                                      month=date.month,
                                      day=date.day)
    return formatted_datetime


def get_layout() -> Div:
    return html.Div([
        dmc.Paper([
            dmc.Grid([
                dmc.Col([
                    dmc.Card([
                        html.H1(['Клиент: ', df.client_name[0]]),
                        html.Br(),
                        html.P(['Сменный день: ',
                                df.shift_day[0]]),
                        html.P(['Точка учета: ',
                                df.endpoint_name[0]]),
                        html.P(['Начало периода: ',
                                get_date().strftime('%H:%M:%S (%d.%m)')]),
                        html.P(['Конец периода: ',
                                (get_date() + timedelta(days=1)).strftime('%H:%M:%S (%d.%m)')]),
                        dcc.Dropdown(df.reason.unique(),
                                     id='filters',
                                     multi=True),
                        dmc.Button('Фильтровать',
                                   id='button'),
                        ],
                        **CARD_STYLE)
                ], span=6),
                dmc.Col([
                    dmc.Card([
                        dcc.Graph(id="graph"),
                        dcc.Input(id='initial_pie', disabled=True)],
                        **CARD_STYLE),

                ], span=6),
                dmc.Col([
                    dmc.Card([
                        dcc.Graph(id='timeline')],
                        **CARD_STYLE)
                ], span=12),
            ], gutter="xl", )
        ])
    ])


app.layout = get_layout()


@app.callback(
    Output('timeline', 'figure'),
    State('filters', 'value'),
    Input('initial_pie', 'value'),
    Input('button', 'n_clicks'),
    prevent_initial_call=False,
)
def update_graph(
        value,
        *args
):

    fig = px.timeline(df,
                      'state_begin',
                      'state_end',
                      y="endpoint_name",
                      color='reason',
                      color_discrete_map=color_map)
    if value:
        fig.update_traces(visible='legendonly')
        for reason in value:
            fig.update_traces(selector={'name': reason}, visible=True)
    fig.update_layout(showlegend=False)
    return fig


@app.callback(
    Output("graph", "figure"),
    Input("initial_pie", "value"))
def generate_chart(_):
    fig = px.pie(df,
                 values='duration_min',
                 names='reason',
                 hole=.3,
                 color='reason',
                 color_discrete_map=color_map)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
