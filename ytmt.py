#!/usr/bin/python
import urllib
import urllib2
import cookielib

import logging
import re, string, time
from bs4 import BeautifulSoup
#from gamedb import Game

HOME_PAGE = "http://www.yourturnmyturn.com/index.php"
PROFILE_INFORMATION_PREFIX = "http://www.yourturnmyturn.com/user.php?username="
PROFILE_INFORMATION_SUFFIX  = "&toonbeurt=1"
game_host_user = 'markp1999'
game_host_pwd = 'ytmt-b4h'


class Ytmt():
    ########################################################################
    #   Log in and read page from web
    ########################################################################
    @staticmethod
    def ReadYourGamesPageFromWeb () :
        s = None
        handle = None
        try:
            logging.debug( """Fetching At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ))
            #
            #  Set up openers for cookie handling
            urlopen = urllib2.urlopen
            Request = urllib2.Request
            cj = cookielib.LWPCookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)
            logging.debug(  "Opener installed " )
            #
            #  Post login form
			#<form name="myform" method="post" action="/index.php" id="myform">
			#<input type="text" name="username_form" size="30" maxlength="30" />
			#<input type="password" name="password_form" size="30" maxlength="30" />
			#<input type="checkbox" name="inloggen" value="1" />Automatic login? 
			#<input type="submit" name="submit" value='Log in' />
            logging.debug(  "Posting form " )
            values = {'username_form' : game_host_user,'password_form' : game_host_pwd,'inloggen' : "1", 'submit' : 'Log in'  }
            data = urllib.urlencode(values)
            url = HOME_PAGE 
            req = urllib2.Request(url, data)
            logging.debug(  req )
            logging.debug(  "Opening handle " )
            handle = urlopen(req)
            logging.debug(  "Reading handle " )
            s = handle.read()
            logging.debug(  "Finished - dumping page" )
            #logging.debug( s )
            return s

        except:
            logging.debug(  """COMMS ERROR At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ) )
            if (handle):
                logging.debug (handle.info())
            return None

    @staticmethod
    def parseYourGamesPage(s):
        #
        #  Get Table Rows GAMEID (2 urls), TYPE (text), STATUS (text), Last Action (text)
        soup = BeautifulSoup(s)
        #
        #  Process rows ID(2 urls), TYPE(text), STATUS(text), Last Action(text)
        table = soup.find(text='Your turn against').findPrevious('table')
        #logging.debug( table )
        games_found = False
        for row in table.findAll('tr',recursive=False):
            #logging.debug( row )
            column = row.findAll('td',recursive=False)
            if (column[0]): 
                #
                # Ignore the row if it doesn't have > 2 columns
                if (len(column) > 2):
                    #logging.debug( column[0].a.string  )
                    iframe = column[0].a['onclick']
                    if (iframe):
                        #logging.debug( iframe )
                        #  Just keep the text after the 'username' prefix - 
                        #  The name is the text before the ampersand
                        if ((iframe.find("username=") == -1) or
                            (iframe.find("username=") == -1) or
                            (iframe.find("username=") == -1)) :
                            print ("Invalid game string")
                        else:
                            gamedata = iframe.split("username=")[1]
                            name = gamedata.split("&")[0]
                            name.strip()
                            #  Just keep the text after the 'gametype' prefix
                            gamedata = gamedata.split("gametype=")[1]
                            type = gamedata.split("&")[0]
                            type.strip()
                            #  Just keep the text after the 'gamenumber' prefix
                            gamedata = gamedata.split("gamenumber=")[1]
                            number = gamedata.split("\"")[0]
                            number.strip()
                            link = "http://www.yourturnmyturn.com/" + type + "/play.php?gamenumber=" + number
                            this_game = Game()
                            this_game.opponent=name
                            this_game.id = number
                            this_game.type = type
                            this_game.clicklink=link
                            this_game.yourturn=True
                            this_game.put()
                            print "NAME: " + name
                            print "Type: " + type                        
                            print "Num: " + number
                            print "URI:" + this_game.clicklink 
                            games_found = True
        return games_found

    ########################################################################
    #   Read anyone's page from web
    ########################################################################
    @staticmethod
    def ReadGamesPageFromWeb (name) :
        s = None
        handle = None
        try:
            logging.debug( """Fetching At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ))

            url = PROFILE_INFORMATION_PREFIX + name + PROFILE_INFORMATION_SUFFIX
            response = urllib2.urlopen(url)
            s = response.read()
            logging.debug(  "Finished - dumping page" )
            logging.debug( s )
            return s

        except:
            logging.debug(  """COMMS ERROR At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ) )
            return None
        

        
        