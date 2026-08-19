from . import message, callbacks

def register_all(app):
    message.register(app)
    callbacks.register(app)
