import psycopg2

import time
from flask import Flask
from flask.ext.restful import reqparse, abort, Api, Resource
from youtube_dl import YoutubeDL
#from youtube_dl import (
#    AtomicParsleyPP,
#    FFmpegAudioFixPP,
#    FFmpegMetadataPP,
#    FFmpegVideoConvertor,
#    FFmpegExtractAudioPP,
#    FFmpegEmbedSubtitlePP,
#    XAttrMetadataPP,
#)
from youtube_dl import FFmpegExtractAudioPP

ydl = YoutubeDL({
  'outtmpl': '%(id)s.%(ext)s',
  'format': 'bestaudio/best'
  })
ydl.add_default_info_extractors()
ydl.add_post_processor(FFmpegExtractAudioPP(preferredcodec='mp3', preferredquality='5', nopostoverwrites=False))

try:
    conn = psycopg2.connect("dbname='turntable' user='tester' host='localhost' password='test'", cursor_factory=DictCursor)
except:
    print "I am unable to connect"
app = Flask(turntable)
api = Api(app)

songs = {
    'bw9CALKOvAI': {'title': 'Bubble Pop! - HYUNA (OFFICIAL MUSIC VIDEO)'},
    'G6JppjQSTh8': {'title': 'CHANGE - Some other KPop'},
}


def abort_if_song_doesnt_exist(song_id):
    if song_id not in songs:
        abort(404, message="song {} doesn't exist".format(song_id))

parser = reqparse.RequestParser()
parser.add_argument('hash', type=str)


# Todo
#   show a single todo item and lets you delete them
class Song(Resource):
    def get(self, song_id):
        args = parser.parse_args()
        song_id = args['hash']
        cur = conn.cursor()
        cur.execute("""SELECT * from songs""")
        rows = cur.fetchall()
        song_exists = False
        for row in rows:
            if row['hash']  == args['hash']:
                song_exists = True
                song = {
                    'hash': row['hash'],
                    'title': row['title'],
                    'song_title': row['song_title'],
                    'artist': row['artist'],
                    'added_on': row['added_on'],
                }
        if not song_exists
            abort(404, message="error song {} not in db!".format(song_id)
        return song

    def delete(self, song_id):
        abort_if_song_doesnt_exist(song_id)
        del songs[song_id]
        return '', 204

    def put(self, song_id):
        args = parser.parse_args()
        song = {
            'title': args['title'],
            'artist': args['artist'],
            'length': args['length'],
        }
        songs[song_id] = song
        return song, 201


# TodoList
#   shows a list of all todos, and lets you POST to add new tasks
class SongList(Resource):
    def get(self):
        return songs

    def post(self):
        args = parser.parse_args()
        song_id = args['hash']
        cur = conn.cursor()
        cur.execute("""SELECT * from songs""")
        rows = cur.fetchall()
        song_exists = False
        for row in rows:
            
            
            if row['hash']  == args['hash']:
                song_exists = True
                song = {
                    'hash': row['hash'],
                    'title': row['title'],
                    'song_title': row['song_title'],
                    'artist': row['artist'],
                    'added_on': row['added_on'],
                }
        if not song_exists:        
            info = ydl.extract_info('http://www.youtube.com/watch?v=' + args['hash'],  download=True)
            song = {
                'hash': args['hash'],
                'title': info['title'],
                'song_title': '',
                'artist': '',
                'added_on': time.time(),
            }
            cursor.executemany("""INSERT INTO songs(hash, title, song_title, artist, added_on) VALUES (%(hash)s, %(title)s, %(song_title)s, %(artist), %(added_on)s)""", song)
        return song, 201

##
## Actually setup the Api resource routing here
##
api.add_resource(SongList, '/songs')
api.add_resource(Song, '/songs/<string:song_id>')

@app.teardown_request
def shutdown_session(exception=None):
      db.session.remove()

