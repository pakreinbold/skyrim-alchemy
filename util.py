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
    effects = defaultdict(set)
    effects['all'] = fx
    kinds = [
        'Fortify', 'Damage', 'Weakness', 'Restore', 'Ravage',
        'Resist', 'Lingering', 'Regenerate'
    ]
    for effect in fx:
        kind_ = effect.split()[0]
        if kind_ in kinds:
            effects[kind_.lower()].add(effect)
        else:
            effects['other'].add(effect)
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
    fx = get_effects(ingredients)
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


def filter_potions(potions, effects):
    if len(effects) == 0:
        return potions
    effects = set(effects)
    filter = potions['Effects'].apply(
        lambda x: effects.issubset(set(x.split(', '))))
    return potions[filter]


def make_kit(potions, effects):
    if len(effects) == 0:
        return (
            pd.DataFrame(columns=[
                'Ingredient 1', 'Ingredient 2', 'Ingredient 3', 'Effects'
            ]),
            pd.Series(),
            'no-effects'
        )

    # Initialize
    kit = []
    fx = defaultdict(int)

    # Find potions randomly for desired effects
    for effect in effects:

        # If already found, skip
        if effect not in fx.keys():

            # Filter full potion list by those with effect
            filtered_ptns = filter_potions(potions, [effect])

            # If no potions have the desired effect, skip
            if len(filtered_ptns) == 0:
                fx[effect] = -1
                continue

            # Randomly select potion with effect
            n = np.random.randint(len(filtered_ptns))
            ptn = filtered_ptns.iloc[n]
            kit.append(ptn)

            # Keep track of what's been found already
            ptn_fx = ptn['Effects'].split(', ')
            for ptn_fct in ptn_fx:
                fx[ptn_fct] += 1

    kit = pd.DataFrame(
        kit,
        columns=['Ingredient 1', 'Ingredient 2', 'Ingredient 3', 'Effects']
    )
    kit['# Effects'] = kit['Effects'].apply(lambda x: len(x.split(', ')))
    kit.sort_values('# Effects', inplace=True)

    fx = pd.Series(fx)

    # Return failure if no potions found at all
    if (fx <= 0).all():
        return kit, fx, 'no-potions'

    # Try and remove redundants
    if (fx > 1).any():

        for ind in kit.index:
            ptn_fx = kit.loc[ind]['Effects'].split(', ')
            ptn_fx = pd.Series(np.ones(len(ptn_fx)), index=ptn_fx)

            fct_dif = (fx - ptn_fx).fillna(fx)
            check = fct_dif[effects] >= 1
            if check.all():
                kit.drop(ind, inplace=True)
                fx = fct_dif

    # If some effects not found, report partial-success
    if (fx < 0).any():
        status = 'partial-success'
    else:
        status = 'success'

    return kit, fx, status


def get_kit_effects(potions):
    '''
    Get all effects in a set of potions

    Args:
        potions (list of dicts): Record format of pd.DataFrame
            - keys: Ingredient 1, Ingredient 2, Ingredient 3, Effects

    Returns:
        (set): All effects in the passed set of potions
    '''
    n_potions = len(potions)
    if n_potions == 0:
        return []

    effects = []
    for n in range(n_potions):
        effects += potions[n]['Effects'].split(', ')
    return set(effects)
