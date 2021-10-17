# %%
import pickle
import numpy as np
import pandas as pd

from util import get_kit_effects


def count_n_fx(fx):
    fx = set(fx.split(', '))
    return len(fx)


def count_n_bad_fx(fx):
    fx = set(fx.split(', '))
    return len(fx.intersection(poisons))


def get_score(kit_fx):
    return len(fx - kit_fx)


# Load data
potions = pd.read_csv('cache/all_potions.csv', index_col=0)
with open('cache/all_fx.pkl', 'rb') as pickle_file:
    all_fx = pickle.load(pickle_file)

# Effects to punish
poison_words = [
    'Damage', 'Ravage', 'Lingering', 'Weakness', 'Fear', 'Frenzy',
    'Paralysis', 'Slow'
]
poisons = {
    effect for effect in all_fx
    if np.any([
        keyword in effect for keyword in poison_words
    ])
}

# Effects to reward
fx = {
    'Resist Fire', 'Resist Frost', 'Resist Shock', 'Resist Magic',
    'Fortify Two-handed', 'Fortify Destruction', 'Fortify Block',
    'Regenerate Stamina', 'Regenerate Magicka', 'Regnerate Health',
    'Fortify Health', 'Fortify Magicka', 'Fortify Stamina'
}

# Process garden potions
potions['# Effects'] = potions['Effects'].apply(count_n_fx)
potions['# Bad'] = potions['Effects'].apply(count_n_bad_fx)
potions['# Good'] = potions['# Effects']\
                          - potions['# Bad']
potions = potions[potions['# Bad'] == 0]\
    .reset_index(drop=True)
n_potions = potions.index.shape[0]

# %%
kit_size = 5

# Initialize kit
kit_inds = np.random.randint(n_potions, size=(kit_size,))
kit_fx = get_kit_effects(potions.iloc[kit_inds].to_dict('records'))
score = get_score(kit_fx)

new_kit_inds = kit_inds.copy()
searching = True
n_failures = 0
n_iter = 0
failure_history = [None] * 10
while searching:
    n_iter += 1

    # Choose the index to try replacing
    n = np.random.randint(1, 3)
    nn = np.random.choice(kit_size, n, replace=False)

    # Make a new kit
    new_kit_inds[nn] = np.random.randint(n_potions, size=(n,))
    new_kit_fx = get_kit_effects(
        potions.iloc[new_kit_inds].to_dict('records')
    )

    # See if the new kit is good
    new_score = get_score(new_kit_fx)

    # Update
    if new_score < score:
        kit_inds[nn] = new_kit_inds[nn]
        kit_fx = new_kit_fx.copy()
        score = new_score
        n_failures = 0
    else:
        new_kit_inds[nn] = kit_inds[nn]
        n_failures += 1

    if score == 0:
        searching = False
    elif n_iter >= 1e4:
        searching = False

kit = potions.iloc[kit_inds]
print(f'Score of {score} after {n_iter} iterations')
if score > 0:
    print(f'Missing effects: {", ".join(fx - kit_fx)}')
kit
