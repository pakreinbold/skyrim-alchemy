from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

from util import get_ingredients, get_effects, filter_by_effect
from app import app


ingredients, garden = get_ingredients()
fx = get_effects(ingredients)
all_fx = fx['all']
fx_options = [{'label': effect, 'value': effect} for effect in all_fx]

layout = html.Div([
    html.H1('Ingredient Explorer'),
    # Selections
    html.Div([
        html.Div([
            html.H4('Select Set of Ingredients'),
            dcc.RadioItems(
                id='df-toggle',
                options=[
                    {'label': 'All', 'value': 'ingredients'},
                    {'label': 'Garden', 'value': 'garden'},
                ],
                value='ingredients'
            ),
        ], style={'display': 'inline-block', 'margin-right': 50}),
        html.Div([
            html.H4('Select Effect Filter Logic'),
            dcc.RadioItems(
                id='logic-toggle',
                options=[
                    {'label': 'Union', 'value': '|'},
                    {'label': 'Intersection', 'value': '&'},
                ],
                value='&'
            ),
        ], style={'display': 'inline-block'})
    ]),
    html.H4('Filter by Effect(s)'),
    dcc.Dropdown(
        id='effect-dropdown',
        options=fx_options,
        multi=True,
        value=[]
    ),
    html.H4('Ingredients Table'),
    dash_table.DataTable(
        id='ingredient-table',
        columns=[{"name": i, "id": i}
                 for i in ingredients.columns],
        data=ingredients.to_dict('records'),
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="paleturquoise"),
        style_data=dict(backgroundColor="lavender")
    ),
])


@app.callback(
    Output('ingredient-table', 'data'),
    Input('effect-dropdown', 'value'),
    Input('df-toggle', 'value'),
    Input('logic-toggle', 'value'))
def update_figure(effects, kind, logic):
    # Check whether or not to use garden
    if kind == 'garden':
        df = garden
    elif kind == 'ingredients':
        df = ingredients

    # Check whether to filter by effect
    if len(effects) == 0:
        filtered_df = df
    else:
        filtered_df = filter_by_effect(df, effects, logic=logic)

    # Return the result
    return filtered_df.to_dict('records')
