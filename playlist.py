import redis
r = redis.Redis("localhost")
room = 'interns'
songnumber = -1
title = ''
song_title = ''
artist = ''
# Function called to initialize your python environment.
# Should return 1 if ok, and 0 if something went wrong.
def ices_init ():
    print 'Executing initialize() function..'
    return 1

# Function called to shutdown your python enviroment.
# Return 1 if ok, 0 if something went wrong.
def ices_shutdown ():
    print 'Executing shutdown() function...'
    return 1

# Function called to get the next filename to stream. 
# Should return a string.
def ices_get_next ():
    print 'Executing get_next() function...'
    username = r.rpop("djlist:%s" % room)
    print username
    song_hash = r.rpop("queue:%s" % username)
    print song_hash
    title = r.hget("song:%s" % song_hash, "title")
    song_title = r.hget("song:%s" % song_hash, "song_title")
    artist = r.hget("song:%s" % song_hash, "artist")
    
    r.hset("room:%s" % room, "current_song", song_hash)

    
    r.lpush("djlist:%s" % room, username)
    r.lpush("queue:%s" % username, song_hash)
    return "/home/ices/music/%s.mp3" % song_hash
# This function, if defined, returns the string you'd like used
# as metadata (ie for title streaming) for the current song. You may
# return null to indicate that the file comment should be used.
def ices_get_metadata ():
    if song_title != '':
        metadata = song_title + " - " + artist
    else:
        metadata = title
    return metadata

# Function used to put the current line number of
# the playlist in the cue file. If you don't care about this number
# don't use it.
def ices_get_lineno ():
    global songnumber
    print 'Executing get_lineno() function...'
    songnumber = songnumber + 1
    return songnumber
