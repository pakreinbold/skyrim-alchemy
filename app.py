import dash

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title='Skyrim Alchemist'
)

server = app.server
