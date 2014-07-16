import psycopg2

import time
import db
from flask import Flask
from flask.ext.restful import reqparse, abort, Api, Resource
from youtube_dl import YoutubeDL
from youtube_dl import FFmpegExtractAudioPP
import boto
import boto.s3.connection
from boto.s3.key import Key


ydl = YoutubeDL({
  'outtmpl': '%(id)s.%(ext)s',
  'format': 'bestaudio/best'
  })
ydl.add_default_info_extractors()
ydl.add_post_processor(FFmpegExtractAudioPP(preferredcodec='mp3', preferredquality='5', nopostoverwrites=False))

app = Flask(__name__)
api = Api(app)

conn = boto.connect_s3()
bucket = conn.get_bucket('turntable.dongs.in')


def abort_if_song_doesnt_exist(song_id):
        abort(404, message="song {} doesn't exist".format(song_id))

parser = reqparse.RequestParser()
parser.add_argument('hash', type=str)


# Todo
#   show a single todo item and lets you delete them
class Song(Resource):
    def get(self, song_id):
        args = parser.parse_args()
        song = db.session.query(db.Song).filter(db.Song.yt_hash == song_id).first()
        url = key.generate_url(0, query_auth=False, force_http=True)
        if song is None:
            abort(404, message="error song {} not in db!".format(song_id))
        ret_song = {
            'title': song.title,
            'song_title': song.song_title,
            'artist': song.artist,
            'yt_hash': song.yt_hash,
            'url': url,
        }
        
        return ret_song, 200


    def put(self, song_id):
        args = parser.parse_args()
        song = {
            'title': args['title'],
            'artist': args['artist'],
            'length': args['length'],
        }
        return song, 201


# TodoList
#   shows a list of all todos, and lets you POST to add new tasks
class SongList(Resource):
    def get(self):
        songs = db.session.query(db.Song)
        ret_songs = []
        for song in songs:
            key = bucket.get_key(song.yt_hash + '.mp3')
            url = key.generate_url(0, query_auth=False, force_http=True)
            ret_song = {
                'title': song.title,
                'song_title': song.song_title,
                'artist': song.artist,
                'yt_hash': song.yt_hash,
                'url': url,
            }
            ret_songs.append(ret_song)
        return ret_songs

    def post(self):
        args = parser.parse_args()
        song_id = args['hash']
        song = db.session.query(db.Song).filter(db.Song.yt_hash == args['hash']).first()
        if song is None:
            info = ydl.extract_info('http://www.youtube.com/watch?v=' + args['hash'],  download=True)
            song = db.Song( 
                title=info['title'],
                song_title='',
                artist='',
                yt_hash=args['hash'],
            )
            db.session.add(song)
            db.session.commit()
            k = Key(bucket)
            k.key = args['hash'] + '.mp3'
            k.set_contents_from_filename(args['hash'] + '.mp3')
            url = k.generate_url(0, query_auth=False, force_http=True)
            ret_song = {
            'title': song.title,
            'song_title': song.song_title,
            'artist': song.artist,
            'yt_hash': song.yt_hash,
            'url': url,
        }
        
        return ret_song, 201

##
## Actually setup the Api resource routing here
##
api.add_resource(SongList, '/songs')
api.add_resource(Song, '/songs/<string:song_id>')

@app.teardown_request
def shutdown_session(exception=None):
      db.session.remove()
if __name__ == '__main__':
      app.run(debug=True)
