from google.appengine.api import memcache

class UserHandler():
  def add_user(self, sk=None, user=None):
    users = memcache.get(sk)
    if users is not Null:
      users.add(user)
      memcache.set(sk, users)
    else:
      users = set(user)
      memcache.add(sk, users)

  def remove_user(sk=None, user=None):
    users = memcache.get(sk)
    users.discard(user)
    
  def get_users(sk=None):
    return memcache.get(sk)