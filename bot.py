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
logging.basicConfig(level=logging.DEBUG,)

from gamedb import Game
from userdb import User

from ytmt import Ytmt
from notifier import Notifier

HELP_MSG = ("I am the game alert bot.  Use the following commands to control your game alerts."
            "\n   'add {ytmt-id}' - Register a YTMT user and start receiving alerts to %s"
            "\n   'remove {ytmt-id}|{*ALL}' - Stop receiving alerts for one or all users."
            "\n   'list users' - Get a list of all your registered users"
            "\n   'list games' - Get a list of all games for your registered users"
            "\To see all games and users being monitored go to %s")



class XmppHandler(xmpp_handlers.CommandHandler):
  """Handler class for all XMPP activity."""

  def help(self, message=None,message_subcmd=None):
    logging.debug(  "processing 'help' command" )

    if len(message.arg.split()) > 1:
        message_subcmd = message.arg.upper().strip().split()[1]
    if message_subcmd:
        if (message_subcmd == "LIST"):
            message.reply("""LIST SYNTAX:
            -  "list games" - Show all games you are participating in
            -  "list users" - Show all registered YTMT users""")
    # Show help text
    google_user = db.IM("xmpp", message.sender).address.split('/')[0]
    message.reply(HELP_MSG % (google_user, self.request.host_url + "?google_user=" + google_user))

  #
  #  Process incoming message
  def text_message(self, message=None):
    logging.debug(  "processing command" )
    message_cmd = message.arg.upper().strip().split()[0]

    if (message_cmd == "HELP"):
        self.help(message)
    elif (message_cmd == "LIST"):
        if ( len(message.arg.split()) > 1):
            message_subcmd = message.arg.upper().strip().split()[1]
            if message_subcmd:
                if (message_subcmd == "USERS"):
                    self.list_users(message)
                else:
                    self.list_games(message)
        else:
            self.list_games(message)
    elif (message_cmd == "ADD"):
        self.add_user(message)
    elif (message_cmd == "REMOVE"):
        self.remove_user(message)
    else:
      self.help(message)


  def list_games(self, message=None):
    logging.debug(  "processing 'list games' command" )
    #
    # List the games in the Db
    # TODO - need to limit to current user's registrations
    # google_id =  db.IM("xmpp", message.sender).address.split('/')[0]
    # users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_id)
    # if ( users.count() == 0  ) :
        # notification = "You haven't registered any YTMT ids.  Use the 'add' command to register an Id."
    # else:


    games_now = db.GqlQuery("SELECT * FROM Game")
    if ( games_now.count() == 0  ) :
        notification = "No games in database"
    else:
        notification = ""
        for g in games_now:
                if (g.whoseturn == g.player):
                    preamble = "It's " + g.player + "'s turn against "
                else:
                    preamble = "It's NOT " + g.player + "'s turn against "
                notification = notification + ", " + preamble + g.opponent +" in " + g.type + " game "+ g.game + " - " + g.clicklink
    message.reply(notification)

  def list_users(self, message=None):
    logging.debug(  "processing 'list users' command" )
    #
    # List the users in the Db
    google_id =  db.IM("xmpp", message.sender).address.split('/')[0]
    users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_id)
    if ( users.count() == 0  ) :
        notification = "You haven't registered any YTMT ids.  Use the 'add' command to register an Id."
    else:
        notification = "You are monitoring the following YTMT users: "
        for u in users:
                notification = notification + "  " + u.ytmt_id
    message.reply(notification)

  def add_user(self, message=None, name=None):
    logging.debug(  "processing 'add user' command" )
    if len(message.arg.split()) > 1:
        name = message.arg.strip().split()[1]
        new_user = User()
        im_from = db.IM("xmpp", message.sender)
        new_user.google_id = im_from.address.split('/')[0]
        new_user.ytmt_id = name
        new_user.put()
        logging.debug( "Added " + name + " for : " + new_user.google_id  )
        message.reply("Added user '" + name + "'.  Alerts will be sent to: " + new_user.google_id + ".")
    else:
        message.reply("No name given.\nSyntax: add {ytmt-user}")

  def remove_user(self, message=None, name=None):
    logging.debug(  "processing 'remove user' command" )
    if len(message.arg.split()) > 1:
        name = message.arg.strip().split()[1]
        google_id =  db.IM("xmpp", message.sender).address.split('/')[0]
        users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_id)
        for u in users:
            if (name == "*ALL" or name == u.ytmt_id ):
                logging.debug( "Deleting " + u.ytmt_id )
                u.delete()
        if (name == "*ALL"):
            message.reply("Removed all ytmt ids for :" + google_id)
        else:
            message.reply("Removed user '" + name  + "'.  No more alerts will be sent to " + google_id + " about '" + name + "'.")
    else:
        message.reply("No name given.\nSyntax: remove {ytmt-user}|{*ALL}")

#                        for key, g in games :

# Save away the old games list to a dictionary
def copy_gamesDb_to_dict_and_purge(player, currentgames):
    old_dict = {}
    oldgames = db.GqlQuery("SELECT * FROM Game  WHERE player = :1", player)
    for g in oldgames:
        old_dict[g.game] = g
        #
        # Purge games from the database where it's not your turn any more
        if (len(currentgames) == 0 or currentgames.has_key(g.game) == False):
            g.delete()
            logging.debug(  "cleared game " + g.game + " " + player)
    return old_dict


#
# Save away the game
def save_game(g):
    this_game = Game(key_name=g.game)
    this_game.player = g.player
    this_game.opponent = g.opponent
    this_game.game = g.game
    this_game.type = g.type
    this_game.clicklink= g.clicklink
    this_game.whoseturn= g.whoseturn
    this_game.put()


################################################################
#  Build up Web page with full list of games and alert users   #
################################################################
class RootHandler(webapp.RequestHandler):

    """Displays a list of games message."""
    def get(self):
        self.response.out.write('<html><body>')
        google_user = self.request.get("google_user")
        if ( google_user != "" ) :
            self.response.out.write( "<h1>Alerts for User " + google_user + "</h1>" )
            users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_user)
        else :
            #
            # Forget the current list of games in a web document for all users
            users = db.GqlQuery("SELECT * FROM User")

        #
        # Handle case of no users being registered
        if ( users.count() == 0  ) :
            logging.debug(  "No users registered " )
            self.response.out.write( "<h2>No Users Registered</h2>" )
            self.response.out.write( "To register YTMT ids, use google talk to connect to gamealertbot@appspot.com ")
            self.response.out.write("then use the 'add {ytmt_id}' command to register your YTMT id.")
        #
        # Or handle each registered user
        else:
            for u in users:
                logging.debug(  "Processing " + u.ytmt_id)
                name = u.ytmt_id
                google_id = u.google_id
                self.response.out.write( "<h2>" + name + "'s Turn (alerting " +  google_id+ ")</h2>")
                #
                # Download the user's overview page
                s = Ytmt.ReadGamesPage_NotLoggedIn( name )
                if ( s != None ):

                    #
                    #
                    # First parse out games where it is your turn
                    games = Ytmt.FindGamesinPage_YourTurn( name, s)
                    #
                    # Save away the old "your turn" games list for this user to
                    # a dictionary and clear the database
                    old_dict = copy_gamesDb_to_dict_and_purge(name, games)
                    if (len(games) == 0):
                        self.response.out.write( "(No games)"  )
                    else:
                        self.response.out.write( "<hr>" )
                        self.response.out.write( "<ul>" )

                        for key in games:
                            g = games[key]
                            #
                            # Compare the old and new games list
                            # TODO: do this by querying the database & do away with dictionary
                            # If this is an old game and it was your turn last time then just print it - dont send IM
                            game_details = g.opponent +" in " + g.type + " game <a href=\"" + g.clicklink + "\">"+ g.game  + "</a>"
                            IM_game_details = g.opponent +" in " + g.type + " game "+ g.clicklink
                            if ( old_dict.has_key(g.game) == True and old_dict[g.game].whoseturn == g.player):
                                notification =  g.player + " still your turn against " + game_details
                                self.response.out.write( "<li>" + notification )
                            else:
                            # Else, new game or newly your turn - send the notification and save the game
                                logging.debug(  "saved game " + g.game + " " + name)
                                notification =  g.player + " it's now your turn against "
                                self.response.out.write( "<li><b>" + notification + game_details)
                                Notifier().notify(google_id, notification + IM_game_details)
                                logging.debug(  "Notifying google_id: " + notification + game_details)
                                save_game(g) # write game to database

                        self.response.out.write( "</ul>" )
                        self.response.out.write( "<hr>" )
                    #
                    # Now list games where it's not your turn
                    self.response.out.write( "<h2>" + name + "'s Opponent's Turn</h2>")
                    #
                    # List games where it's not your turn
                    games = Ytmt.FindGamesinPage_OpponentsTurn( name, s)
                    if (len(games) == 0):
                        self.response.out.write( "(No games)"  )
                    else:
                        self.response.out.write( "<ul>" )
                        for key in games:
                            g = games[key]
                            g.clicklink = g.clicklink.replace(" ", "+")
                            game_details = g.player +" in " + g.type + " game <a href=\"" + g.clicklink + "\">"+ g.game  + "</a>"
                            notification =  g.opponent + "'s turn against " + game_details
                            self.response.out.write( "<li>" + notification )

                        self.response.out.write( "</ul>" )
                    self.response.out.write( "<hr>" )

                else:
                    self.response.out.write( "No games to play or web access failed")


        self.response.out.write(   "</body></html>"   )


def main():
  app = webapp.WSGIApplication([
      ('/', RootHandler),
      ('/_ah/xmpp/message/chat/', XmppHandler),
      ], debug=True)
  wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
  main()
