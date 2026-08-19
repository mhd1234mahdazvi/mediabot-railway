from . import panel, users, broadcast

def register_all(app):
    panel.register(app)
    users.register(app)
    broadcast.register(app)
