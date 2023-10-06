from dash import html, Output, Input, State, dcc, dash_table
from dash_extensions.enrich import (DashProxy,
                                    ServersideOutputTransform,
                                    MultiplexerTransform)
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate
import pandas as pd
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


engine = create_engine("sqlite://///home/sergey/PycharmProjects/testtask/test_task/testDB.db")
query = """
SELECT *
FROM sources
"""
df = pd.read_sql(query, con=engine)
print(df)
app = EncostDash(name=__name__)


def get_layout():
    return html.Div([
        dmc.Paper([
            dmc.Grid([
                dmc.Col([
                    dmc.Card([
                        dmc.TextInput(
                            label='Введите что-нибудь',
                            id='input'),
                        dmc.Button(
                            'Первая кнопка',
                            id='button1'),
                        dmc.Button(
                            'Вторая кнопка',
                            id='button2'),
                        html.Div(
                            id='output')],
                        **CARD_STYLE)
                ], span=6),
                dmc.Col([
                    dmc.Card([
                        html.Div('Верхняя правая карточка')],
                        **CARD_STYLE),

                ], span=6),
                dmc.Col([
                    dmc.Card([
                        html.Div('Нижняя карточка')],
                        **CARD_STYLE)
                ], span=12),
            ], gutter="xl", )
        ])
    ])


app.layout = get_layout()


@app.callback(
    Output('output', 'children'),
    State('input', 'value'),
    Input('button1', 'n_clicks'),
    prevent_initial_call=True,
)
def update_div1(
        value,
        click
):
    if click is None:
        raise PreventUpdate

    return f'Первая кнопка нажата, данные: {value}'


@app.callback(
    Output('output', 'children'),
    State('input', 'value'),
    Input('button2', 'n_clicks'),
    prevent_initial_call=True,
)
def update_div2(
        value,
        click
):
    if click is None:
        raise PreventUpdate

    return f'Вторая кнопка нажата, данные: {value}'


if __name__ == '__main__':
    app.run_server(debug=True)
