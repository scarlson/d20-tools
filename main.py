import cgi
import logging
import os
import random
import urllib
import userhandler
from django.utils import simplejson
from google.appengine.api import channel
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


from models.sessionmodels import *
from models.Message import Message
from slashcommands import *

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
#use_library('django', '1.1')
template.register_template_library('templatetags.urltargetblank')

# Set the debug level
_DEBUG = True
SERVER = "SERVER"

CURRENT_USER = None
CURRENT_USER_NICKNAME = None
UserHandler = userhandler.UserHandler

def sendMessage(command=None,session=None,content=None,author=None):
    '''
        Process message sending to specific channels
    '''
    val = simplejson.dumps({ 'command':command, 'text': content, 'author': author })

    if _DEBUG:
        captureMessage(SERVER, "/room/" + session.slug, val)

    users = memcache.get(str(session.key()))
    users = set(users)
    for user in users:
      channel.send_message(user.user.user_id(), val)

def captureMessage(a=None, b=None, c=None):
    '''
        Capture JSON messages between server and client
    '''
    Msg = Message(source=a, destination=b, content=c)
    Msg.put()

def addDict(basedict, sourcedict):
    '''
        Concatenate 2 dictionaries, unsure why python lacks this feature
    '''
    for k, v in sourcedict.iteritems(): 
        basedict[k]=v
    return basedict

def find_or_add_player(session=None, user=None):
    current_player = None
    for player in session.players:
      if player.user == user:
        return player
    
    current_player = GamePlayer()
    current_player.user = user
    current_player.nickname = user.nickname()
    current_player.session = session
    current_player.put()
    
    return current_player

def find_or_create_session(slug=None):
    '''
        Search for existing session, if none exist create one
    '''
    query = db.Query(GameSession)
    query.filter('slug =', slug)
    session = query.get()
    
    if not session:
      session = GameSession(slug=slug)
      session.put()
    
    return session

def post_users_to_channel(sk=None):
    '''
        Send full user list to channel clients via JSON
    '''
    users = memcache.get(sk)
    session = GameSession.get(sk)
    players = []

    for user in users:
        players.append(user.nickname)
    
    players.sort()
    val = simplejson.dumps({ 'command':'users' , 'text': players })
    
    if _DEBUG:
      captureMessage(SERVER, "/room/" + session.slug, val)

    for player in session.players:
      channel.send_message(player.user.user_id(), val)    
      
class BaseRequestHandler(webapp.RequestHandler):
  """Base request handler extends webapp.Request handler

     It defines the generate method, which renders a Django template
     in response to a web request
  """

  def generate(self, template_name, template_values={}):
    """Generate takes renders and HTML template along with values
       passed to that template

       Args:
         template_name: A string that represents the name of the HTML template
         template_values: A dictionary that associates objects with a string
           assigned to that object to call in the HTML template.  The defualt
           is an empty dictionary.
    """
    # We check if there is a current user and generate a login or logout URL
    user = users.get_current_user()

    if user:
      log_in_out_url = users.create_logout_url('/')
    else:
      log_in_out_url = users.create_login_url(self.request.path)

    # We'll display the user name if available and the URL on all pages
    values = {'user': user, 'log_in_out_url': log_in_out_url}
    values.update(template_values)

    # Construct the path to the template
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, 'templates', template_name)

    # Respond to the request by rendering the template
    self.response.out.write(template.render(path, values, debug=_DEBUG))

class MainRequestHandler(BaseRequestHandler):
  def get(self):
    user = users.get_current_user() 
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    template_values = {}
    self.generate('index.html', template_values)

class RoomHandler(BaseRequestHandler):
  def get(self, slug):
    session = find_or_create_session(slug)
    user = users.get_current_user() 

    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    # determine whether the player is already in the room before adding
    current_player = find_or_add_player(session, user)

    players = memcache.get(str(session.key()))
    if players is not None:
      for player in players:
        if current_player.key() == player.key():
            break
        elif [player] == players[-1:]:
            players.append(current_player)
        else:
            pass
      players.sort()    
      memcache.set(str(session.key()), players)
    else:
      players = [current_player]
      memcache.add(str(session.key()), players)

    
    token = channel.create_channel(current_player.user.user_id())

    template_values = { 'token' : token,
                        'nickname': user.nickname(),
                        'session_key' : session.key(),
                        'slug' : slug,
                        'players' : players}
    self.generate('room.html', template_values)
  
  def post(self,slug):
    pass

class FlushCacheHandler(BaseRequestHandler):    
  def get(self):
    memcache.flush_all()

class ViewCacheHandler(BaseRequestHandler):    
  def get(self):
    dict = [['Session Key', 'Room Players']]
    z = db.GqlQuery("SELECT __key__ from GameSession")
    stats = memcache.get_stats()
    for key in z:
        key = str(key)
        dict.append([key, memcache.get(key)])
    template_values = { 'stats':stats,
                        'cache': dict}
    self.generate('memcache.html', template_values)

class FetchUsersHandler(webapp.RequestHandler):
  def post(self):
    sk = self.request.get('sk')
    post_users_to_channel(sk)  

class UserAddHandler(webapp.RequestHandler):
  def post(self):
    sk = self.request.get('sk')
    session = GameSession.get(sk)
    user = cgi.escape(self.request.get('u'))
    users = memcache.get(sk)
    
    sendMessage(command='system',session=session,content=user + ' entered the room.',author='*')
    post_users_to_channel(sk)  

class UserRemoveHandler(webapp.RequestHandler):    
  def post(self):
    sk = cgi.escape(self.request.get('sk'))
    session = GameSession.get(sk)
    token = cgi.escape(self.request.get('token'))
    tokens = memcache.get(sk)
    try:
        tokens.remove(token)
    except:
        pass
    memcache.set(sk, tokens)
    for player in session.players:
      if player.key() == token:
        CURRENT_USER_NICKNAME = player.nickname
        CURRENT_USER_NICKNAME = player.nickname
        break
      else:
        CURRENT_USER_NICKNAME = user

    sendMessage('system',session,user + ' left the room.','*')
    
    if _DEBUG:
      captureMessage("/room/" + session.slug, SERVER, "REM: " + user)

    post_users_to_channel(sk)  

class ChatRequestHandler(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    session_key = self.request.get('sk')
    session = GameSession.get(session_key)
    msg = cgi.escape(self.request.get('m'))
    
    for player in session.players:
      if player.user == user:
        CURRENT_USER_NICKNAME = player.nickname
        break

    if _DEBUG:
        captureMessage("/room/" + session.slug, SERVER, "CHAT: " + msg)

    if msg.startswith('/'):
      if msg.startswith('/nick'):
        CURRENT_USER_NICKNAME = msg[6:18]
        msg = msg[:18]
      if msg.startswith('/roll'):
        msg = CURRENT_USER_NICKNAME + " rolls " + self.handle_slash_command(urllib.unquote(msg), session, user)[5:]
      else:
        msg = self.handle_slash_command(msg, session, user)
      command = "system"
      user = '*'
    else:
      command = "chat"
      user = CURRENT_USER_NICKNAME


    sendMessage(command, session, msg, user)

  def handle_slash_command(self, content, session, user):
    command, _, args = content.partition(' ')
    return SlashCommandHandlerFactory.create(command, session, user).handle(command, args) 

application = webapp.WSGIApplication(
                                       [('/', MainRequestHandler),
                                        ('/room/([^/]+)/?', RoomHandler),
                                        ('/chat', ChatRequestHandler),
                                        ('/getusers', FetchUsersHandler),
                                        ('/userrem', UserRemoveHandler),
                                        ('/useradd', UserAddHandler),
                                        ('/flushcache', FlushCacheHandler),
                                        ('/viewcache', ViewCacheHandler)],
                                        debug=_DEBUG)

def main():
  random.seed()
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
