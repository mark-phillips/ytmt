import re
import logging
from google.appengine.ext import db

class Game(db.Model):
    "Details of a Game"
    id = db.StringProperty()
    clicklink = db.StringProperty()
    type = db.StringProperty()
    opponent = db.StringProperty()
    yourturn = db.BooleanProperty()