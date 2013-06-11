#!/usr/bin/python
import urllib2
import logging
import time
from bs4 import BeautifulSoup
from game import Game

HOME_PAGE = "http://www.yourturnmyturn.com/index.php"
PROFILE_INFORMATION_PREFIX = "http://www.yourturnmyturn.com/user.php?username="
PROFILE_INFORMATION_SUFFIX  = "&toonbeurt=1"

class Ytmt():

    ########################################################################
    #   Read anyone's page from web
    ########################################################################
    @staticmethod
    def ReadGamesPage_NotLoggedIn (name) :
        s = None
        handle = None
        try:
            logging.debug( """Fetching At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ))

            url = PROFILE_INFORMATION_PREFIX + name + PROFILE_INFORMATION_SUFFIX
            response = urllib2.urlopen(url)
            s = response.read()
            logging.debug(  "Finished" )
            #logging.debug( s )
            return s

        except:
            logging.debug(  """COMMS ERROR At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ) )
            return None
        
    ########################################################################
    #   Parse games page to get a list of games 
    ########################################################################
    @staticmethod
    def FindGamesinPage_NotLoggedIn (name, isItYourTurn, page) :
        games = []
        #
        #  Get Table Rows 
        soup = BeautifulSoup(page)
        #
        #  Whose turn are we looking for?
        if isItYourTurn:
            whoseTurn= "Turn " + name
        else:
            whoseTurn= "Opponent's turn " + name
        #
        # Find the appropriate table
        table = soup.find(text=whoseTurn).findPrevious('table')
        #logging.debug( table.prettify() )
        for row in table.findAll('tr',recursive=True):
            #logging.debug( row )
            column = row.findAll('td',recursive=False)
            if (column[0]): 
                #
                # Ignore the row if it doesn't have > 2 columns
                if (len(column) > 2):
                    this_game = Game()
                    
                    opponent = column[0].contents[0][2:] # Name starts in 2nd character
                    if (column[1].a) :
                        type = unicode(column[1].contents[1] ) # Skip the hyperlink if found
                    else:
                        type = unicode(column[1].contents[0] )  # or use contents
                    relpath = column[2].a['href'] 
                    number = relpath.split("gamenumber=")[1]
                    link = "http://www.yourturnmyturn.com/" + type + "/play.php?gamenumber=" + number
                    yourturn = False

                    this_game.player=name
                    this_game.opponent=opponent
                    this_game.id = number
                    this_game.type = type
                    this_game.clicklink=link
                    this_game.yourturn=isItYourTurn
                    games.append(this_game)

        return games

            
            