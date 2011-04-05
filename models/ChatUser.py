from google.appengine.ext import db

class ChatUser(db.Model):
  chatuser = db.UserProperty()
  password = db.BlobProperty()
  salt = db.BlobProperty()
  joined = db.DateTimeProperty(auto_now_add=True)
  room = db.StringProperty()
