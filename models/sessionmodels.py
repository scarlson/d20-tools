from google.appengine.ext import db

class GameSession(db.Model):
  slug = db.StringProperty()


class GamePlayer(db.Model):
  session = db.ReferenceProperty(GameSession, collection_name = "players")
  user = db.UserProperty()
  nickname = db.StringProperty()