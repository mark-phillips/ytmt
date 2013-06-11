#!/usr/bin/python
# Copyright 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
import logging
import os
import wsgiref.handlers
from google.appengine.api import xmpp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.ereporter import report_generator
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import xmpp_handlers

import re, string, time
from bs4 import BeautifulSoup

import logging
logging.basicConfig(level=logging.DEBUG,)

#import games
import gamedb
from ytmt import Ytmt
from notifier import Notifier

HELP_MSG = ("I am the game alert bot."
            "\nRegister a user for alerts by typing 'add' "
            "\nStop receiving alerts by typing 'remove'."
            "\nGet a list of all your games by typing 'list' "
            "\nLearn more... go to %s/")


user_ids = { "markp1999" : "markrp@gmail.com", "Spann" : "dpfilter@gmail.com"}

RetryInterval = 60
google_id= 'markrp@gmail.com'


class XmppHandler(xmpp_handlers.CommandHandler):
  """Handler class for all XMPP activity."""

  def help(self, message=None,message_subcmd=None):
    if message_subcmd == None and len(message.arg.split()) > 1:
        message_subcmd = message.arg.upper().strip().split()[1]
    if message_subcmd:
        if (message_subcmd == "LIST"):
            message.reply("""LIST SYNTAX:
            -  "list games" - Show all games you are participating in
            -  "list sites" - Show all sites where you have registered users""")
    # Show help text
    message.reply(HELP_MSG % (self.request.host_url,))

      #
  #  Process incoming message
  def text_message(self, message=None):
    im_from = db.IM("xmpp", message.sender)

    message_cmd = message.arg.upper().strip().split()[0]
    
    if (message_cmd == "HELP"):
        self.help(message)
    elif (message_cmd == "LIST"):
        self.list_games(message)
    elif (message_cmd == "DUMP"):
        self.dump_games(message,)
    else:
      self.help(message)
    
  def list_games(self, message=None):
    # Show help text
    message.reply("List of games coming up...")
    #
    # List the games in the Db
    games_now = db.GqlQuery("SELECT * FROM Game")
    for g in games_now:
        notification =  "It's your turn against " + g.opponent +" in " + g.type + " game "+ g.id + " - " + g.clicklink 
        Notifier().notify(google_id, notification) 

  def dump_games(self, message=None, name=None):
    if name == None and len(message.arg.split()) > 1:
        message_subcmd = message.arg.strip().split()[1]
    else:
        name = "markp1999"
        
    # Show help text
    message.reply("HTML dump coming up...")
    message.reply( Ytmt.ReadGamesPageFromWeb( name ) )
    
#
# Save away the old games list to a dictionary and clear the database
def move_gamesDb_to_dict():
    old_dict = {}
    oldgames = db.GqlQuery("SELECT * FROM Game")
    for g in oldgames:
        old_dict[g.id] = g
        g.delete()
    return old_dict


    
class RootHandler(webapp.RequestHandler):
    
    """Displays a list of games message."""
    def get(self):
        self.response.out.write('<html><body><ul>')
        #
        # Get the current list of games in a web document
        s = Ytmt.ReadYourGamesPageFromWeb ()
        if ( s != None ):
            #
            # Save away the old games list to a dictionary and clear the database
            old_dict = move_gamesDb_to_dict()
            #
            # Parse the list of games and load into the database
            Ytmt.parseYourGamesPage(s)
            print "<br>================================================="
            #
            # Compare the old and new games list 
            games_now = db.GqlQuery("SELECT * FROM Game")
            for g in games_now:
                #
                # If this is an old game just print it - dont send IM
                if ( old_dict.has_key(g.id) == True ):
                    notification =  "It's still your turn against " + g.opponent +" in " + g.type + " game "+ g.id                  
                    self.response.out.write( "<li>" + notification + "<br/><a href=\"" + g.clicklink + "\">"+ g.clicklink  + "</a>")                    
                else:
                # Else, new game - send a notification
                    notification =  "It's your turn against " + g.opponent +" in " + g.type + " game "+ g.id + " - " + g.clicklink 
                    self.response.out.write( "<li>" + "It's your turn against " + g.opponent +" in " + g.type + " game "+ g.id + "<br><a href=\"" + g.clicklink + "\">"+ g.clicklink + "</a>")
                    Notifier().notify(google_id, notification) 
            print "<br>================================================="
        else:
            self.response.out.write( "No games to play or web access failed")
        
        self.response.out.write(   "</ul></body></html>"   )


def main():
  app = webapp.WSGIApplication([
      ('/', RootHandler),
      ('/_ah/xmpp/message/chat/', XmppHandler),
      ], debug=True)
  wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
  main()
