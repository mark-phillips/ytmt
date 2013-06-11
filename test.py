#!/usr/bin/python
import datetime
import logging
import os
import re, string, time
from bs4 import BeautifulSoup

import logging
logging.basicConfig(level=logging.DEBUG,)

from ytmt import Ytmt

RetryInterval = 60
google_id= 'markrp@gmail.com'

def main():
    name = "markp1999"
    s = Ytmt.ReadGamesPageFromWeb( name )        

    #
    #  Get Table Rows GAMEID (2 urls), TYPE (text), STATUS (text), Last Action (text)
    soup = BeautifulSoup(s)
    #
    #  Process rows ID(2 urls), TYPE(text), STATUS(text), Last Action(text)
    table = soup.find(text="Opponent's turn " + name).findPrevious('table')
    logging.debug( table )
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

                        print "NAME: " + name
                        print "Type: " + type                        
                        print "Num: " + number
                        print "URI:" + this_game.clicklink 
                        games_found = True















    return
           
        
        
    s = Ytmt.ReadYourGamesPageFromWeb ()
    games = Ytmt.parseYourGamesPage(s)

    if (games != {}):
        print "================================================="
        for g in games:
            #
            # If this is a new game - send a notification
            if oldgames.has_key(games[g].id) == False :
                notification =  "It's your turn against " +games[g].opponent +" in " + games[g].type + " game "+ games[g].id + "\n" + games[g].clicklink 
                print notification
                Notifier().notify(google_id, notification)

            else:
            # Else, old games so ignore it
                print "<a href=" + games[g].clicklink + ">It's still your turn against " + games[g].opponent +" in " + games[g].type + " game "+ games[g].id + "</a>"
        print "================================================="
    else:
        print "No games to play"
   
    time.sleep(30)
   
   

if __name__ == '__main__':
  main()
