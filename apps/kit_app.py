from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from app import app

import pickle
import pandas as pd
from pathlib import Path
from util import make_kit, get_kit_effects

# Load caches
cache_path = Path(
    '/Users/patri/Documents/Python Stuff/Skyrim_Alchemy/cache'
)
with open(cache_path / 'all_fx.pkl', 'rb') as pickle_file:
    all_fx = pickle.load(pickle_file)
fx_options = [{'label': effect, 'value': effect} for effect in all_fx]

all_potions = pd.read_csv(cache_path / 'all_potions.csv', index_col=0)
garden_potions = pd.read_csv(cache_path / 'garden_potions.csv', index_col=0)
empty_kit = pd.DataFrame(
    columns=['Ingredient 1', 'Ingredient 2', 'Ingredient 3', 'Effects']
)

layout = html.Div([
    # Title
    html.H1('Potion Kit Generator'),

    # Ingredient sub-set selection
    html.H3('Select Ingredient Sub-set'),
    dcc.RadioItems(
        id='kit-subset',
        options=[
            {'label': 'All', 'value': 'ingredients'},
            {'label': 'Garden', 'value': 'garden'},
        ],
        value='ingredients'
    ),

    # Effect selection
    html.H3('Select Effect(s)'),
    dcc.Dropdown(
        id='effect-dropdown-k',
        options=fx_options,
        multi=True,
        value=[]
    ),
    html.Button(id='generate-button', n_clicks=0, children='Generate'),

    # Status message
    html.P(
        id='status-message',
        children=['No kit generated yet.'],
        style={'color': 'orange', 'fontSize': 25}
    ),

    # Potion table
    html.H3('Possible Set of Potions with Desired Effects'),
    dash_table.DataTable(
        id='potion-table-k',
        columns=[{"name": i, "id": i}
                 for i in empty_kit.columns],
        data=empty_kit.to_dict('records'),
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="wheat"),
        style_data=dict(backgroundColor="lavender"),
        # style_as_list_view=True,
        # filter_action='native',
        row_selectable="multi",
        selected_rows=[]
    ),
    html.P(
        id='potion-count-k',
        children=[f'Number of Potions: {empty_kit.index.shape[0]}']
    ),

    # Permanent Kit
    html.Button(id='add-button', n_clicks=0, children='Add to Kit'),
    html.H3('Potions in Kit'),
    dash_table.DataTable(
        id='kit-table',
        columns=[{"name": i, "id": i}
                 for i in empty_kit.columns],
        data=empty_kit.to_dict('records'),
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="wheat"),
        style_data=dict(backgroundColor="lavender"),
        # style_as_list_view=True,
        # filter_action='native',
        # row_selectable="multi",
        # selected_rows=[],
        row_deletable=True,
    ),
    html.P(
        id='kit-count',
        children=[f'Number of Potions: {empty_kit.index.shape[0]}']
    ),
    html.P(
        id='kit-effects',
        children=[
            'Effects in Kit: '
            + ", ".join(get_kit_effects(empty_kit.to_dict("records")))
        ]
    ),
    # html.Button(id='remove-button', n_clicks=0, children='Remove from kit'),

    # Storage variables
    dcc.Store(id='potion-storage-k'),
    dcc.Store(id='kit-storage'),
])


@app.callback(
    Output('potion-storage-k', 'data'),
    Input('generate-button', 'n_clicks'),
    State('kit-subset', 'value'),
    State('effect-dropdown-k', 'value'),
)
def update_potion_storage(n_clicks, subset, effects):
    if subset == 'ingredients':
        kit_potions, fx, status = make_kit(all_potions, effects)
    elif subset == 'garden':
        kit_potions, fx, status = make_kit(garden_potions, effects)
    return (
        kit_potions.to_dict('records'),
        kit_potions.index.shape[0],
        status,
        fx.to_dict()
    )


@app.callback(
    Output('potion-table-k', 'data'),
    Input('potion-storage-k', 'data')
)
def update_potion_table(tup):
    return tup[0]


@app.callback(
    Output('potion-count-k', 'children'),
    Input('potion-storage-k', 'data')
)
def update_potion_count(tup):
    return f'Number of Potions: {tup[1]}'


@app.callback(
    Output('status-message', 'children'),
    Input('potion-storage-k', 'data')
)
def update_status_message(tup):
    status = tup[2]
    if status == 'no-effects':
        return 'No effects selected'
    elif status == 'success':
        return 'Kit successfully generated'
    elif status == 'partial-success':
        fx = pd.Series(tup[3])
        missing_fx = ', '.join(fx[fx == -1].index)
        return f'Some effects not possible: {missing_fx}'
    elif status == 'no-potions':
        return 'No potions with desired effects found'


@app.callback(
    Output('status-message', 'style'),
    Input('potion-storage-k', 'data')
)
def update_status_color(tup):
    status = tup[2]
    style = {'fontSize': 25}
    if status == 'no-effects':
        style['color'] = 'orange'
    elif status == 'success':
        style['color'] = 'green'
    elif status == 'partial-success':
        style['color'] = 'orange'
    elif status == 'no-potions':
        style['color'] = 'red'
    return style


@app.callback(
    Output('kit-table', 'data'),
    Input('add-button', 'n_clicks'),
    State('potion-table-k', 'selected_rows'),
    State('potion-table-k', 'data'),
    State('kit-table', 'data')
)
def update_kit_storage(n_clicks, selected_rows, potion_table, kit_potions):
    new_potions = [
        potion_table[ind] for ind in selected_rows
        if potion_table[ind] not in kit_potions
    ]
    new_potions += kit_potions
    return new_potions


@app.callback(
    Output('kit-count', 'children'),
    Input('kit-table', 'data')
)
def update_kit_count(kit_potions):
    return f'Number of Potions: {len(kit_potions)}'


@app.callback(
    Output('kit-effects', 'children'),
    Input('kit-table', 'data')
)
def update_kit_effects(kit_potions):
    return f'Effects in Kit: {", ".join(get_kit_effects(kit_potions))}'
