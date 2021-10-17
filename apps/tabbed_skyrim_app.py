import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

import numpy as np
import pandas as pd
from collections import defaultdict


def check_first(s):
    bads = {'Collected', 'Harvested', 'collected', 'harvested'}
    for bad in bads:
        if bad in s:
            return False
    return True


def get_ingredients():
    # Scrape the table
    dfs = pd.read_html('https://en.uesp.net/wiki/Skyrim:Ingredients')

    # Clean columns
    ingredients = dfs[0].drop(columns=['Ingredient Name (ID)'])
    renames = {
        'Ingredient Name (ID).1': 'Ingredient Name',
        'Primary Effect': 'Effect 1',
        'Secondary Effect': 'Effect 2',
        'Tertiary Effect': 'Effect 3',
        'Quaternary Effect': 'Effect 4',
        'Unnamed: 6': 'Value',
        'Unnamed: 7': 'Weight',
        'GardenHF': 'Garden Yield'
    }
    ingredients.rename(columns=renames, inplace=True)

    # Get rid of acquisition rows
    is_good = ingredients['Effect 1'].apply(check_first)
    ingredients = ingredients[is_good]
    assert ingredients.index.shape[0] == 109

    # Typing
    ingredients['Value'] = ingredients['Value'].astype(int)
    ingredients['Weight'] = ingredients['Weight'].astype(float)
    ingredients['Garden Yield'] = ingredients['Garden Yield']\
        .fillna(0).astype(int)

    # Get the ones you can grow
    garden = ingredients[ingredients['Garden Yield'] > 0]\
        .sort_values('Garden Yield', ascending=False)

    return ingredients, garden


def get_effects(df):
    fx = set()
    for n in range(4):
        temp = df[f'Effect {n+1}'].unique()
        temp = [s.split(' (')[0] for s in temp]
        fx = fx.union(temp)
    effects = defaultdict(list)
    effects['all'] = fx
    kinds = [
        'Fortify', 'Damage', 'Weakness', 'Restore', 'Ravage',
        'Resist', 'Lingering', 'Regenerate'
    ]
    for effect in fx:
        kind_ = effect.split()[0]
        if kind_ in kinds:
            effects[kind_.lower()].append(effect)
        else:
            effects['other'].append(effect)
    return effects


def check_val(row, check):
    for n in range(4):
        temp = row[f'Effect {n+1}'].split(' (')[0]
        if check == temp:
            return True
    return False


def filter_by_effect(df, effects, logic='&'):
    if isinstance(effects, str):
        effects = [effects]
    is_effects = None
    for effect in effects:
        is_effect = df.apply(lambda row: check_val(row, effect), axis=1)
        if is_effects is None:
            is_effects = is_effect
        else:
            exec(f'is_effects {logic}= is_effect')
    return df[is_effects].copy()


def get_ing_space(ingredients):
    num_ing = ingredients.index.shape[0]
    num_fx = len(fx['all'])
    ing_space = pd.DataFrame(
        np.zeros((num_ing, num_fx), int),
        index=ingredients['Ingredient Name'],
        columns=fx['all']
    )

    for n in range(num_ing):
        row = ingredients.iloc[n]
        name = row['Ingredient Name']
        for m in range(4):
            effect = row[f'Effect {m+1}'].split(' (')[0]
            ing_space.loc[name, effect] += 1

    return ing_space


def filter_ing_space(ing_space, effects=[], logic='|'):
    if len(effects) == 0:
        return ing_space

    conds = None
    for effect in effects:
        cond = ing_space[effect] == 1
        if conds is None:
            conds = cond
        else:
            exec(f'conds {logic}= cond')

    return ing_space[conds]


def find_potions(ing_space, effects=[]):
    potions = []
    num_ing = ing_space.index.shape[0]
    for n in range(num_ing):
        ing1 = ing_space.iloc[n]
        for m in range(n+1, num_ing):
            ing2 = ing_space.iloc[m]
            combo = ing1 + ing2
            check = combo[effects] > 1
            if check.all():
                potions.append({
                    'Ingredient 1': ing_space.index[n],
                    'Ingredient 2': ing_space.index[m],
                    'Ingredient 3': None,
                    'Effects': ', '.join(combo[combo > 1].index)
                })
            for j in range(m+1, num_ing):
                combo = ing1 + ing2 + ing_space.iloc[j]
                check = combo[effects] > 1
                if check.all():
                    potions.append({
                        'Ingredient 1': ing_space.index[n],
                        'Ingredient 2': ing_space.index[m],
                        'Ingredient 3': ing_space.index[j],
                        'Effects': ', '.join(combo[combo > 1].index)
                    })
    return pd.DataFrame(potions)


def filter_find_potions(ing_space, effects=[]):
    filtered_space = filter_ing_space(ing_space, effects=effects)
    potions = find_potions(filtered_space, effects=effects)
    return potions


ingredients, garden = get_ingredients()
fx = get_effects(ingredients)
ing_space = get_ing_space(ingredients)
fire_potions = filter_find_potions(ing_space, effects=['Resist Fire'])
all_fx = fx['all']
fx_options = [{'label': effect, 'value': effect} for effect in all_fx]

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = app.layout = html.Div([
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Ingredient Explorer', value='tab-1'),
        dcc.Tab(label='Potion Finder', value='tab-2'),
    ]),
    html.Div(id='tabs-content')
])


@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.Label('Select Set of Ingredients'),
            dcc.RadioItems(
                id='df-toggle',
                options=[
                    {'label': 'All', 'value': 'ingredients'},
                    {'label': 'Garden', 'value': 'garden'},
                ],
                value='ingredients',
                labelStyle={'display': 'inline-block'}
            ),
            html.Label('Select Effect Filter Logic'),
            dcc.RadioItems(
                id='logic-toggle',
                options=[
                    {'label': 'Union', 'value': '|'},
                    {'label': 'Intersection', 'value': '&'},
                ],
                value='&',
                labelStyle={'display': 'inline-block'}
            ),
            html.Label('Filter by Effect(s)'),
            dcc.Dropdown(
                id='effect-dropdown',
                options=fx_options,
                multi=True,
                value=[]
            ),
            dash_table.DataTable(
                id='ingredient-table',
                columns=[{"name": i, "id": i}
                         for i in ingredients.columns],
                data=ingredients.to_dict('records'),
                style_cell=dict(textAlign='left'),
                style_header=dict(backgroundColor="paleturquoise"),
                style_data=dict(backgroundColor="lavender")
            )
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.Label('Select Effect(s)'),
            dcc.Dropdown(
                id='effect-dropdown-p',
                options=fx_options,
                multi=True,
                value=[]
            ),
            dash_table.DataTable(
                id='potion-table',
                columns=[{"name": i, "id": i}
                         for i in fire_potions.columns],
                data=fire_potions.to_dict('records'),
                style_cell=dict(textAlign='left'),
                style_header=dict(backgroundColor="paleturquoise"),
                style_data=dict(backgroundColor="lavender")
            )
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


@app.callback(
    Output('potion-table', 'data'),
    Input('effect-dropdown-p', 'value')
)
def update_potion_table(effects):
    potions = filter_find_potions(ing_space, effects=effects)
    return potions.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
