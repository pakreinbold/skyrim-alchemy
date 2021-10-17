from dash import dcc, html
from dash.dependencies import Input, Output

from app import app
from apps import ingredients_app, potions_app, kit_app


app.layout = html.Div([
    # represents the URL bar, doesn't render anything
    dcc.Location(id='url', refresh=False),

    # Hyperlinks for page navigation
    dcc.Link('Navigate to Ingredient Explorer', href='/ingredients'),
    html.Br(),
    dcc.Link('Navigate to Potion Crafter', href='/potions'),
    html.Br(),
    dcc.Link('Navigate to Potion Kit Generator', href='/kit'),

    # App(let) layout based on url path
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/ingredients':
        return ingredients_app.layout
    elif pathname == '/potions':
        return potions_app.layout
    elif pathname == '/kit':
        return kit_app.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
