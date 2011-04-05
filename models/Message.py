from google.appengine.ext import db

class Message(db.Model):
  source = db.StringProperty()
  destination = db.StringProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
