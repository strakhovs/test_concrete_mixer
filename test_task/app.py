from datetime import timedelta
from pathlib import Path

import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, dcc, html
from dash.html import Div
from dash_extensions.enrich import (DashProxy, MultiplexerTransform,
                                    ServersideOutputTransform)
from sqlalchemy import create_engine

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
DB_PATH = str(Path(__file__).parents[1])
engine = create_engine(f"sqlite:///{DB_PATH}/testDB.db")
query = """
SELECT *
FROM sources
"""
df = pd.read_sql(query,
                 con=engine,
                 parse_dates=['shift_day',
                              'calendar_day',
                              'state_begin',
                              'state_end',
                              'shift_begin'])

"""
    Цветовая схема
"""
color_map = dict(zip(df['reason'], df['color']))

app = EncostDash(name=__name__)


def get_layout() -> Div:
    period_begin = (df.shift_day[0] + timedelta(hours=df.shift_begin[0].hour))
    return html.Div([
        dmc.Paper([
            dmc.Grid([
                dmc.Col([
                    dmc.Card([
                        html.H1(['Клиент: ', df.client_name[0]]),
                        html.Br(),
                        html.P(['Сменный день: ',
                                df.shift_day[0].strftime('%Y-%m-%d')]),
                        html.P(['Точка учета: ',
                                df.endpoint_name[0]]),
                        html.P(['Начало периода: ',
                                period_begin.strftime('%H:%M:%S (%d.%m)')]),
                        html.P(['Конец периода: ',
                                (period_begin + timedelta(days=1)).strftime('%H:%M:%S (%d.%m)')]),
                        dmc.MultiSelect(id='filters',
                                        data=df.reason.unique()),
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
                        html.H4('График состояний',
                                style={'text-align': 'center'}),
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
)
def update_graph(value, *args):
    """
    Обновление графика состояний
    """
    fig = px.timeline(df,
                      'state_begin',
                      'state_end',
                      y="endpoint_name",
                      color='reason',
                      color_discrete_map=color_map,
                      height=200,
                      custom_data=['state',
                                   'reason',
                                   'state_begin',
                                   'duration_min',
                                   'shift_day',
                                   'shift_name',
                                   'operator']
                      )
    if value:
        fig.update_traces(visible='legendonly')
        for reason in value:
            fig.update_traces(selector={'name': reason}, visible=True)
    fig.update_layout(showlegend=False, yaxis={'visible': False})
    template = """
        Состояние - <b>%{customdata[0]}</b><br>
        Причина - <b>%{customdata[1]}</b><br>
        Начало - <b>%{customdata[2]|%X</b> <i>(%d.%m)</i>}<br>
        Длительность - <b>%{customdata[3]:.2f}</b> мин.<br>
        <br>
        Сменный день - <b>%{customdata[4]|%d.%m.%y}</b><br>
        Смена - <b>%{customdata[5]}</b><br>
        Оператор - <b>%{customdata[6]}</b><br><extra></extra>
    """
    fig.update_traces(hovertemplate=template)
    return fig


@app.callback(
    Output("graph", "figure"),
    Input("initial_pie", "value"))
def generate_chart(_):
    """
    Отрисовка круговой диаграммы
    """
    fig = px.pie(df,
                 values='duration_min',
                 names='reason',
                 hole=.3,
                 color='reason',
                 color_discrete_map=color_map)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
