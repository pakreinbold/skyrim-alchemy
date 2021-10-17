from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from app import app

import pickle
import pandas as pd
from pathlib import Path
from util import filter_potions

# Load caches
cache_path = Path(
    '/Users/patri/Documents/Python Stuff/Skyrim_Alchemy/cache'
)
with open(cache_path / 'all_fx.pkl', 'rb') as pickle_file:
    all_fx = pickle.load(pickle_file)
fx_options = [{'label': effect, 'value': effect} for effect in all_fx]

all_potions = pd.read_csv(cache_path / 'all_potions.csv', index_col=0)
garden_potions = pd.read_csv(cache_path / 'garden_potions.csv', index_col=0)

layout = html.Div([
    html.H1('Potion Crafter'),
    html.H4('Select Ingredient Sub-set'),
    dcc.RadioItems(
        id='potion-subset',
        options=[
            {'label': 'All', 'value': 'ingredients'},
            {'label': 'Garden', 'value': 'garden'},
        ],
        value='ingredients'
    ),
    html.H4('Select Effect(s)'),
    dcc.Dropdown(
        id='effect-dropdown-p',
        options=fx_options,
        multi=True,
        value=[]
    ),
    html.H4('Potion Table'),
    html.P(
        id='potion-count',
        children=[f'Number of Potions: {all_potions.index.shape[0]}']),
    dash_table.DataTable(
        id='potion-table',
        columns=[{"name": i, "id": i}
                 for i in all_potions.columns],
        data=all_potions.to_dict('records'),
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="paleturquoise"),
        style_data=dict(backgroundColor="lavender")
    ),
    dcc.Store(id='potion-storage')
])


@app.callback(
    Output('potion-storage', 'data'),
    Input('potion-subset', 'value'),
    Input('effect-dropdown-p', 'value'),
)
def update_potion_storage(subset, effects):
    if subset == 'ingredients':
        filtered_potions = filter_potions(all_potions, effects)
    elif subset == 'garden':
        filtered_potions = filter_potions(garden_potions, effects)
    return (
        filtered_potions.to_dict('records'),
        filtered_potions.index.shape[0]
    )


@app.callback(
    Output('potion-table', 'data'),
    Input('potion-storage', 'data')
)
def update_potion_table(tup):
    return tup[0]


@app.callback(
    Output('potion-count', 'children'),
    Input('potion-storage', 'data')
)
def update_potion_count(tup):
    return f'Number of Potions: {tup[1]}'
