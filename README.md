# skyrim-alchemy

Start the app by executing `python index.py`. There are 3 routes available:
1. /ingredients
2. /potions
3. /kits

## Ingredient Explorer
This renders a table of all available ingredients, with their 4 effects. This set can be filtered based on effects (with a toggle for AND/OR logic), as well as whether or not the ingredient can be (re)grown in the gardens added in the Hearthfire expansion.
![Alt text](./screenshots/ingredient_explorer.png?raw=true "Optional Title")

## Potion Crafter
This route renders a table of all possible potions, which you can filter based on effects. The table will display the 2-3 ingredients, as well as all the effects the potion contains.
![Alt text](./screenshots/potion_crafter.png?raw=true "Optional Title")

## Kit Creator
This route aims to aid the creation of a potion "kit": a set of potions a player would carry to achieve a number of effects. For example, say the player wanted to have Resist Fire, Fortify Destruction, and Regenerate Stamina available to them. This tool builds upon the potion filtering to recommend a set of potions that can yield the desired effects. Each recommendation is randomly generated, but if you see a particular potion that you like, you can add it to your final kit, and generate another set of potions.
![Alt text](./screenshots/kit_generator.png?raw=true "Optional Title")
