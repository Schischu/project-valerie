import os
import Config

from sqlite3 import dbapi2 as sqlite
#------------------------------------------------------------------------------------------
#if Config.getBoolean("sqlite") is True      
#------------------------------------------------------------------------------------------

class db_handler(object):
    
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

    ##
    # Executes a single query
    # @param sqlStatement: complete SQL Statement
    # @return: True for OK or False for Error
    def singleQuery(self, sqlSatement):
        connection = self.OpenDatabase()
        if connection is not None:
            try:
                cursor = connection.cursor()
                cursor.execute(sqlSatement)
                cursor.close()
                connection.commit()
                connection.close()
                return True
            except sqlite.IntegrityError:
                return False 

    ##
    # Executes a query and returns a result list element
    # @param sqlStatement: complete SQL Statement
    # @return: list element
    def queryToList(self, sqlSatement):
        connection = self.OpenDatabase()
        if connection is not None:
            connection.text_factory = str
            cursor = connection.cursor()
            result_list = []
            cursor.execute(sqlSatement)
            for row in cursor:
                result_list.append((row[1], row[0]))
            cursor.close()  
            connection.close()
            return result_list
        else:
            return None
    
    ##
    # Executes a query and returns one single value
    # @param sqlStatement: complete SQL Statement
    # @return: row[0]
    def executeScalar(self, sqlSatement):
        connection = self.OpenDatabase()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute(sqlSatement)
            row = cursor.fetchone()
            cursor.close()
            connection.commit()
            connection.close()
            return row[0]
        else:
            return None   
