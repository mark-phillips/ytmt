from google.appengine.ext import db
#from google.appengine.api import datastore_types
#from google.appengine.ext.webapp import xmpp_handlers
class User(db.Model):
    "Details of a User"
    google_id = db.StringProperty()
    ytmt_id = db.StringProperty()
