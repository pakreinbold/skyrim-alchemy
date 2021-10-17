# %%
import numpy as np
import pandas as pd
from collections import defaultdict


def check_first(s):
    bads = {'Collected', 'Harvested', 'collected', 'harvested'}
    for bad in bads:
        if bad in s:
            return False
    return True


def check_val(row, check):
    for n in range(4):
        if check in row[f'Effect {n+1}']:
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


def get_all_effects(df):
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


# %% Get the ingredients
ingredients, garden = get_ingredients()
fx = get_all_effects(ingredients)


# %% Convert to ingredient-space
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


def find_2potions(ing_space, effects=[]):
    potions = []
    num_ing = ing_space.index.shape[0]
    for n in range(num_ing):
        ing1 = ing_space.iloc[n]
        for m in range(n+1, num_ing):
            combo = ing1 + ing_space.iloc[m]
            check = combo[effects] > 1
            if check.all():
                potions.append({
                    'Ingredient 1': ing_space.index[n],
                    'Ingredient 2': ing_space.index[m],
                    'Effects': ', '.join(combo[combo > 1].index)}
                )
    return pd.DataFrame(potions)


def find_potions(ing_space, effects):
    # Initialize
    potions = []
    num_ing = ing_space.index.shape[0]

    # Search all 3-combinations
    for n in range(num_ing):
        # Get first ingredient
        ing1 = ing_space.iloc[n]

        for m in range(n+1, num_ing):
            # Get second ingredient
            ing2 = ing_space.iloc[m]

            # Combination of first 2
            combo12 = ing1 + ing2

            # If desired effects, add to potions list
            check = combo12[effects] > 1
            effects_2 = ', '.join(combo12[combo12 > 1].index)
            if check.all():
                potions.append({
                    'Ingredient 1': ing_space.index[n],
                    'Ingredient 2': ing_space.index[m],
                    'Ingredient 3': None,
                    'Effects': effects_2
                })

            for j in range(m+1, num_ing):
                # Combination of all 3
                combo123 = ing1 + ing2 + ing_space.iloc[j]

                # Make sure desired effects present
                check = combo123[effects] > 1
                effects_3 = ', '.join(combo123[combo123 > 1].index)

                # Make sure that a simpler potion isn't possible
                combo23 = ing2 + ing_space.iloc[j]
                effects_2_ = ', '.join(combo23[combo23 > 1].index)

                # Save 3-ingredient potion if valid
                if (
                    check.all()
                    & (effects_3 != effects_2)  # Make sure 3rd isn't dead
                    & (effects_3 != effects_2_)
                ):
                    potions.append({
                        'Ingredient 1': ing_space.index[n],
                        'Ingredient 2': ing_space.index[m],
                        'Ingredient 3': ing_space.index[j],
                        'Effects': effects_3
                    })

    return pd.DataFrame(potions)


def find_ALL_potions(ing_space):
    # Initialize
    potions = []
    num_ing = ing_space.index.shape[0]

    # Search all 3-combinations
    for n in range(num_ing):
        # Get first ingredient
        ing1 = ing_space.iloc[n]

        for m in range(n+1, num_ing):
            # Get second ingredient
            ing2 = ing_space.iloc[m]

            # Combination of first 2
            combo12 = ing1 + ing2

            # If desired effects, add to potions list
            check = combo12 > 1
            effects_2 = ', '.join(combo12[combo12 > 1].index)
            if check.any():
                potions.append({
                    'Ingredient 1': ing_space.index[n],
                    'Ingredient 2': ing_space.index[m],
                    'Ingredient 3': None,
                    'Effects': effects_2
                })

            for j in range(m+1, num_ing):
                # Combination of all 3
                combo123 = ing1 + ing2 + ing_space.iloc[j]

                # Make sure desired effects present
                check = combo123 > 1
                effects_3 = ', '.join(combo123[combo123 > 1].index)

                # Make sure that simpler potions aren't possible
                combo23 = ing2 + ing_space.iloc[j]
                effects_2_ = ', '.join(combo23[combo23 > 1].index)

                combo13 = ing1 + ing_space.iloc[j]
                effects_13 = ', '.join(combo13[combo13 > 1].index)

                # Save 3-ingredient potion if valid
                if (
                    check.any()
                    & (effects_3 != effects_2)  # Make sure 3rd isn't dead
                    & (effects_3 != effects_2_)  # Make sure 1st isn't dead
                    & (effects_3 != effects_13)  # Make sure 2nd isn't dead
                ):
                    potions.append({
                        'Ingredient 1': ing_space.index[n],
                        'Ingredient 2': ing_space.index[m],
                        'Ingredient 3': ing_space.index[j],
                        'Effects': effects_3
                    })

    return pd.DataFrame(potions)


def filter_find_potions(ing_space, effects=[]):
    filtered_space = filter_ing_space(ing_space, effects=effects)
    potions = find_potions(filtered_space, effects=effects)
    return potions


def filter_potions(potions, effects):
    effects = set(effects)
    filter = potions['Effects'].apply(
        lambda x: effects.issubset(set(x.split(', '))))
    return potions[filter]


def make_kit(potions, effects):
    # Initialize
    kit = []
    fx = defaultdict(int)

    # Find potions randomly for desired effects
    for effect in effects:

        # If already found, skip
        if effect not in fx.keys():

            # Randomly select potion with effect
            filtered_ptns = filter_potions(potions, [effect])
            n = np.random.randint(len(filtered_ptns))
            ptn = filtered_ptns.iloc[n]
            kit.append(ptn)

            # Keep track of what's been found already
            ptn_fx = ptn['Effects'].split(', ')
            for ptn_fct in ptn_fx:
                fx[ptn_fct] += 1

    kit = pd.DataFrame(kit)
    kit['# Effects'] = kit['Effects'].apply(lambda x: len(x.split(', ')))
    kit.sort_values('# Effects', inplace=True)

    fx = pd.Series(fx)

    # Try and remove redundants
    if (fx > 1).any():

        for n in range(kit.index.shape[0]):
            ptn_fx = kit.iloc[n]['Effects'].split(', ')
            ptn_fx = pd.Series(np.ones(len(ptn_fx)), index=ptn_fx)

            fct_dif = (fx - ptn_fx).fillna(fx)
            check = fct_dif[effects] >= 1
            if check.all():
                kit.drop(n)
                fx = fct_dif

    return kit, fx


def get_connectivity_matrix(potions, all_effects):
    
