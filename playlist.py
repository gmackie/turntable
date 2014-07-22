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
    while r.llen("djlist:%s" % room) < 4 and r.scard("djwaitset:%s" % room) > 0:
        new_user = r.spop("djwaitset:%s" % room)
        r.lpush("djlist:%s" % room, new_user)
        print "adding user : " + new_user + " to list"
    if r.llen("djlist:%s" % room) > 0:
        username = r.rpop("djlist:%s" % room)
        song_hash = r.rpop("queue:%s" % username)
        print "playing song for user: " + username
        
        r.zincrby("user:%s:plays" % username, song_hash) 
        if r.sismember("djset:%s" % room):
            print "user : " + username + " has left the room while dj'ing!"
        elif r.llen("queue:%s" username) > 0:
            print "keeping user: " + username + " : has queue"
            r.lpush("djlist:%s" % room, username)
        else:
            print "removing user: " + username + " from dj list due to empty queue"
            r.srem("djset:%s" % room, username)
            
    else:
        print 'No one available to DJ'
        print 'Choosing random song.....'
        song_hash = r.srandmember("songs")
    title = r.hget("song:%s" % song_hash, "title")
    song_title = r.hget("song:%s" % song_hash, "song_title")
    artist = r.hget("song:%s" % song_hash, "artist")
    
    r.zincrby("room:%s:plays" % room, song_hash) 
    r.hset("room:%s" % room, "current_song", song_hash)
    r.hset("room:%s" % room, "skips", 0)

    return "/home/ices/music/%s.mp3" % song_hash
# This function, if defined, returns the string you'd like used
# as metadata (ie for title streaming) for the current song. You may
# return null to indicate that the file comment should be used.
def ices_get_metadata ():
    song_hash = r.hget("room:%s" % room, "current_song")
    title = r.hget("song:%s" % song_hash, "title")
    song_title = r.hget("song:%s" % song_hash, "song_title")
    artist = r.hget("song:%s" % song_hash, "artist")

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
