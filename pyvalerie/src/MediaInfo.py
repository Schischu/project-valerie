'''
Created on 21.05.2010

@author: i7
'''
import re

class MediaInfo(object):
    '''
    classdocs
    '''

    Alternatives = {}
    Directors = []
    Writers = []
    Genres = ""
    Runtime = 0
    TagLine = ""
    Popularity = "0"
    Plot = ""

    ImdbId = "tt0000000"
    TheTvDbId = "0"
    Title = ""
    
    Filename = ""
    Path = ""
    Extension = ""
    Year = 0
    Resolution = "576"
    Sound = "Stereo"
    
    isMovie = True
    isSerie = False
    isEpisode = False
    
    Poster = ""
    Backdrop = ""
    
    Season = 0
    Episode = 0
    
    SearchString = ""

    def __init__(self, path, filename, extension):
        '''
        Constructor
        '''
        self.Path = path
        self.Filename = filename
        self.Extension = extension
        
        
        self.Alternatives = {}
        self.Directors = []
        self.Writers = []
           
           
    def copy(self):
        m = MediaInfo(self.Path, self.Filename, self.Extension)
        m.Alternatives = self.Alternatives
        m.Directors = self.Directors
        m.Writers = self.Writers
        m.Genres = self.Genres
        m.Runtime = self.Runtime
        m.TagLine = self.TagLine
        m.Popularity = self.Popularity
        m.Plot = self.Plot
        
        m.ImdbId = self.ImdbId
        m.TheTvDbId = self.TheTvDbId
        m.Title = self.Title
        m.Year = self.Year
        m.Resolution = self.Resolution
        m.Sound = self.Sound
        m.isMovie = self.isMovie
        m.isSerie = self.isSerie
        m.isEpisode = self.isEpisode
        m.Poster = self.Poster
        m.Backdrop = self.Backdrop
        m.Season = self.Season
        m.Episode = self.Episode
        m.SearchString = self.SearchString
        return m
    
    def replacements(self):
        l = {}
        l["pre"] = []
        l["post"] = []
        l["pre"].append([r' (extended|edition|part1|part2|oar|esir|eng|rus|dd5|web|hdtv|dimension|avi|vob|dth|vc1|ac3d|dl|extcut|mkv|nhd|576p|720p|1080p|1080i|dircut|directors cut|dvdrip|dvdscreener|dvdscr|avchd|wmv|ntsc|pal|mpeg|dsr|hd|r5|dvd|dvdr|dvd5|dvd9|bd5|bd9|dts|ac3|bluray|blu-ray|hdtv|pdtv|stv|hddvd|xvid|divx|x264|dxva|m2ts|FESTIVAL|LIMITED|WS|FS|PROPER|REPACK|RERIP|REAL|RETAIL|EXTENDED|REMASTERED|UNRATED|CHRONO|THEATRICAL|DC|SE|UNCUT|INTERNAL|DUBBED|SUBBED)'," "])
        
        l["post"].append([r' (oar|esir)'," "])
        return l   
    
    def isEnigma2Recording(self, name):
        try:
            f = open(name + ".meta", "r")
            f.close()
        except Exception, ex:
            #print ex
            return False
        return True
        
    def getEnigma2RecordingName(self, name):
        f = open(name + ".meta", "r")
        f.readline()
        name = f.readline()
        f.close()
        return name
 
    
    def parse(self):
        absFilename = str(self.Path) + "/" + str(self.Filename) + "." + str(self.Extension)
        if self.isEnigma2Recording(absFilename) is True:
            self.SearchString = self.getEnigma2RecordingName(absFilename).strip()
            return
        
        
        name = str(self.Filename).lower()
        
        name = re.sub(r'[.]', " ", name)
        
        ### Replacements PRE
        self.SearchString = name
        for replacement in self.replacements()["pre"]:
            self.SearchString = re.sub(replacement[0], replacement[1], self.SearchString)
        self.SearchString = self.SearchString.strip()
        
        ###
        m = re.search(r'(?P<imdbid>tt\d{7})', name)
        if m and m.group("imdbid"):
            self.ImdbId = m.group("imdbid")
            
        ###  
        m = re.search(r'\D(?P<year>\d{4})\D', name)
        if m and m.group("year"):
            self.Year = int(m.group("year"))
            self.SearchString = name[:m.start()]
            
        ###    
        m = re.search(r'720p', name)
        if m:
            self.Resolution = "720p"
        else:
            m = re.search(r'1080i', name)
            if m:
                self.Resolution = "1080i"
            else:
                m = re.search(r'1080p', name)
                if m:
                    self.Resolution = "1080p"
            
        ###    
        m = re.search(r'dts', name)
        if m:
            self.Sound = "dts"
        else:
            m = re.search(r'dd5', name)
            if m:
                self.Sound = "ac3"
            else:
                m = re.search(r'ac3', name)
                if m:
                    self.Sound = "ac3"
                
        if self.Season == 0 or self.Episode == 0:
            m = re.search(r' s(?P<season>\d+)\D?e\D?(?P<episode>\d+) ', name)
            if m and m.group("season") and m.group("episode"):
                self.isSerie = True
                self.isMovie = False
                
                self.Season = int(m.group("season"))
                self.Episode = int(m.group("episode"))
                
                self.SearchString = re.sub(r' s(?P<season>\d+)\D?e\D?(?P<episode>\d+).*', " ", self.SearchString)
              
        if self.Season == 0 or self.Episode == 0:  
            m = re.search(r' (?P<season>\d+)\D?x\D?(?P<episode>\d+) ', name)
            if m and m.group("season") and m.group("episode"):
                self.isSerie = True
                self.isMovie = False
                
                self.Season = int(m.group("season"))
                self.Episode = int(m.group("episode"))
                
                self.SearchString = re.sub(r' (?P<season>\d+)\D?x\D?(?P<episode>\d+).*', " ", self.SearchString)
                
        if self.Season == 0 or self.Episode == 0:
            m = re.search(r' (?P<season>\d{1,2})(?P<episode>\d{2}) ', name)
            if m and m.group("season") and m.group("episode"):
                s = int(m.group("season"))
                e = int(m.group("episode"))
                if (s == 0 or s == 19 and e >= 50 or s == 20 and e <= 14) is False:
                    self.isSerie = True
                    self.isMovie = False
                    
                    self.Season = int(m.group("season"))
                    self.Episode = int(m.group("episode"))
                    
                    self.SearchString = re.sub(r'(?P<season>\d{1,2})(?P<episode>\d{2}).*', " ", self.SearchString)
                    
        ### Replacements POST
        self.SearchString = re.sub(r'[-]', " ", self.SearchString)
        self.SearchString = re.sub(r' +', " ", self.SearchString)
        self.SearchString = self.SearchString.strip()
            
    def __str__(self):
        return str(self.Path) + " / " + str(self.Filename) + " . " + str(self.Extension) + \
    "\n\tImdbId:       " + str(self.ImdbId) + \
    "\n\tTheTvDbId:    " + str(self.TheTvDbId) + \
    "\n\tTitle:        " + str(self.Title) + \
    "\n\tSearchString: " + str(self.SearchString) + \
    "\n\tYear:         " + str(self.Year) + \
    "\n\tResolution:   " + str(self.Resolution) + \
    "\n\tSound:        " + str(self.Sound) + \
    "\n\tAlternatives: " + str(self.Alternatives) + \
    "\n\tDirectors:    " + str(self.Directors) + \
    "\n\tWriters:      " + str(self.Writers) + \
    "\n\tRuntime:      " + str(self.Runtime) + \
    "\n\tGenres:       " + str(self.Genres) + \
    "\n\tTagLine:      " + str(self.TagLine) + \
    "\n\tPopularity:   " + str(self.Popularity) + \
    "\n\tPlot:         " + str(self.Plot) + \
    "\n\tSeason:       " + str(self.Season) + \
    "\n\tEpisode:      " + str(self.Episode) + \
    "\n\n"
    #"\n\tPoster:       " + str(self.Poster) + \
    #"\n\tBackdrop:     " + str(self.Backdrop) + \
    #"\n\n"

    def importStr(self, string, isMovie=False, isSerie=False, isEpisode=False):
        
        self.isMovie = isMovie
        self.isSerie = isSerie
        self.isEpisode = isEpisode
        
        
        d = {} 
        lines = string.split('\n')
        for line in lines: 
            #print "Line: ", line
            if ":" in line: 
                key, value = (s.strip() for s in line.split(":", 1)) 
    
            if key == "ImdbId":
                self.ImdbId = value
            if key == "TheTvDb":
                self.TheTvDbId = value
                
            elif key == "Title":
                self.Title = value
            elif key == "LocalTitle":
                self.Title = value
                
            elif key == "Year":
                self.Year = int(value)
                
            elif key == "Path":
                self.Path, self.Filename = value.rsplit("/", 1)
                #print self.Filename
                self.Filename, self.Extension = self.Filename.rsplit('.', 1)
                
            elif key == "Plot":
                self.Plot = value
            elif key == "LocalPlot":
                self.Plot = value   
            elif key == "Runtime":
                self.Runtime = int(value)  
            elif key == "Tag":
                self.TagLine = value  
            elif key == "Popularity":
                self.Popularity = value  
            elif key == "Season":
                self.Season = int(value)  
            elif key == "Episode":
                self.Episode = int(value)
            
            

    def export(self):
        stri = "\n---BEGIN---"
        try:
            if self.isMovie:
                stri += \
                "\nImdbId: "+ self.ImdbId + \
                "\nTitle: "+ self.Title + \
                "\nLocalTitle: "+ self.Title + \
                "\nYear: "+ str(self.Year) + \
                "\nPath: "+ self.Path + "/" + self.Filename + "." + self.Extension + \
                "\nPlot: "+ self.Plot + \
                "\nLocalPlot: "+ self.Plot + \
                "\nRuntime: "+ str(self.Runtime) + \
                "\nGenres: "+ self.Genres + \
                "\nReleasedate: "+ "2000-01-01" + \
                "\nTag: "+ self.TagLine + \
                "\nPopularity: "+ self.Popularity + \
                "\nDirectors: "+ "---" + \
                "\nWriters: "+ "---"
            elif self.isSerie:
                stri += \
                "\nImdbId: "+ self.ImdbId + \
                "\nTheTvDb: "+ self.TheTvDbId + \
                "\nTitle: "+ self.Title + \
                "\nLocalTitle: "+ self.Title + \
                "\nYear: "+ str(self.Year) + \
                "\nPlot: "+ self.Plot + \
                "\nLocalPlot: "+ self.Plot + \
                "\nRuntime: "+ str(self.Runtime) + \
                "\nGenres: "+ self.Genres + \
                "\nReleasedate: "+ "2000-01-01" + \
                "\nTag: "+ self.TagLine + \
                "\nPopularity: "+ self.Popularity + \
                "\nDirectors: "+ "---" + \
                "\nWriters: "+ "---"
            elif self.isEpisode:
                stri += \
                "\nImdbId: "+ self.ImdbId + \
                "\nTheTvDb: "+ self.TheTvDbId + \
                "\nTitle: "+ self.Title + \
                "\nLocalTitle: "+ self.Title + \
                "\nYear: "+ str(self.Year) + \
                "\nPath: "+ self.Path + "/" + self.Filename + "." + self.Extension + \
                "\nPlot: "+ self.Plot + \
                "\nLocalPlot: "+ self.Plot + \
                "\nRuntime: "+ str(self.Runtime) + \
                "\nGenres: "+ self.Genres + \
                "\nReleasedate: "+ "2000-01-01" + \
                "\nTag: "+ self.TagLine + \
                "\nPopularity: "+ self.Popularity + \
                "\nSeason: "+ str(self.Season) + \
                "\nEpisode: "+ str(self.Episode) + \
                "\nDirectors: "+ "---" + \
                "\nWriters: "+ "---"
        except Exception, ex:
            print ex
            
        stri += "\n----END----\n\n"
        return stri
            