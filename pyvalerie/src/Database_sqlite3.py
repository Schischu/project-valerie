import os
import Config

from sqlite3 import dbapi2 as sqlite
#------------------------------------------------------------------------------------------

class Database_sqlite3(object):
    
    def __init__(self):
        pass
    
    def OpenDatabase(self):
        connectstring = "/hdd/Valerie.db"
        # make connection string variable over Config
        db_exists = False
        if os.path.exists(connectstring):
            db_exists = True
        try:
            connection = sqlite.connect(connectstring)
            if not os.access(connectstring, os.W_OK):
                print "[Project Valerie] Error: database file needs to be writable, can not open %s for writing..." % connectstring
                connection.close()
                return None
        except:
            print "[Project Valerie] unable to open database file: %s" % connectstring
            return None
        if not db_exists :
            connection.execute('CREATE TABLE IF NOT EXISTS Movies (imdb_id INTEGER NOT NULL PRIMARY KEY, title TEXT, day INTEGER, year INTEGER, path TEXT, filename TEXT, extension TEXT, plot TEXT, runtime INTEGER, popularity INTEGER, genre_id INTEGER);')
            connection.execute('CREATE TABLE IF NOT EXISTS Series (imdb_id INTEGER NOT NULL PRIMARY KEY, thetvdb_id INTEGER, title TEXT, day INTEGER, year INTEGER, plot TEXT, runtime INTEGER, popularity INTEGER, genre_id INTEGER);')
            connection.execute('CREATE TABLE IF NOT EXISTS Episodes (thetvdb_id INTEGER NOT NULL PRIMARY KEY, title TEXT, year INTEGER, path TEXT, filename TEXT, extension TEXT, episode INTEGER, plot TEXT, runtime INTEGER, popularity INTEGER, serie_id INTEGER, genre_id INTEGER);')
            connection.execute('CREATE TABLE IF NOT EXISTS Genre (genre_id INTEGER NOT NULL PRIMARY KEY, genre_text TEXT);')
            printl("Database created")    
        
        return connection
    
    def addMovie(self,values):
        pass
    
    def addSerie(self, values):
        pass
    
    def addEpisode(self, values):
        pass    