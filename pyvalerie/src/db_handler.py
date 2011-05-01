import os
import Config

from sqlite3 import dbapi2 as sqlite
#------------------------------------------------------------------------------------------
#if Config.getBoolean("sqlite") is True   
"""
schischu@ufs910 22:02 
du kennst doch die mediainfo.py oder?

Don Davici 22:02 
yep

schischu@ufs910 22:02 
momentan ist das so das das eine mischung aus den variablen titel usw ist, sowei den methoden parse usw
meiner meinung wäre es sinnvoller wenn das in 2 classen aufgetrennt würde

schischu@ufs910 22:03 
sprich class MediaInfo die nur die Variablen beinhaltet die auch in der txd abgespeichert werden.
und class MediaInfoHelper das die Methoden beinhaltet
denke das würde auch in hinblick sql einiges erleichter

schischu@ufs910 22:04 
"hoffe" ich
was hältst du davon ?

"""   
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

    ## returns true if recordcount is > 0 else false
    def queryIfExists(self):
        pass

    ## executes the given insert statement
    def queryInsert(self, sqlSatement):
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

    ## returns array with display-member and value-member
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
    
    ## returns the first value of the first row
    def querySingleValue(self, sqlSatement):
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
    

    def querySingleRow(self, sqlSatement):
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
        

    def queryMultipleRows(self, sqlSatement):
        connection = self.OpenDatabase()
        if connection is not None:
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
    
    ## returns the count of returned rows      
    def queryGetRecordCount(self):
        $db = sqlite_open('mysqlitedb');
        $result = sqlite_query($db, "SELECT * FROM mytable WHERE name='John Doe'");
        $rows = sqlite_num_rows($result);
