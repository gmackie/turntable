import psutil
import os
import signal
import time
from hashlib import md5
from flask import Flask
from flask.ext.restful import reqparse, abort, Api, Resource
from youtube_dl import YoutubeDL
from youtube_dl import FFmpegExtractAudioPP
import redis
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

r = redis.Redis("localhost")

def abort_if_song_doesnt_exist(song_id):
        abort(404, message="song {} doesn't exist".format(song_id))

parser = reqparse.RequestParser()
parser.add_argument('hash', type=str)
parser.add_argument('username', type=str)
parser.add_argument('password', type=str)
parser.add_argument('room', type=str)


# Todo
#   show a single todo item and lets you delete them
class Song(Resource):
    def get(self, song_id):
        args = parser.parse_args()
        if r.sismember("songs", song_id):
            title = r.hget("song:%s" % song_id, "title")
            song_title = r.hget("song:%s" % song_id, "song_title")
            artist = r.hget("song:%s" % song_id, "artist")
            yt_hash = r.hget("song:%s" % song_id, "yt_hash")

            key = bucket.get_key(song.yt_hash + '.mp3')
            url = key.generate_url(0, query_auth=False, force_http=True)
            ret_song = {
                'title': title,
                'song_title': song_title,
                'artist': artist,
                'yt_hash': yt_hash,
                'url': url,
            }
        else:
            abort(404, message="error song {} not in db!".format(song_id))
        return ret_song, 200


# TodoList
#   shows a list of all todos, and lets you POST to add new tasks
class SongList(Resource):
    def get(self):
        ret_songs = []
        song_hashes = r.smembers("songs")
        for song_id in song_hashes:
            title = r.hget("song:%s" % song_id, "title")
            song_title = r.hget("song:%s" % song_id, "song_title")
            artist = r.hget("song:%s" % song_id, "artist")
            yt_hash = r.hget("song:%s" % song_id, "yt_hash")
            
            key = bucket.get_key(song_id + '.mp3')
            url = key.generate_url(0, query_auth=False, force_http=True)
            
            ret_song = {
                'title': title,
                'song_title': song_title,
                'artist': artist,
                'yt_hash': yt_hash,
                'url': url,
            }
            ret_songs.append(ret_song)
        return ret_songs

    def post(self):
        args = parser.parse_args()
        song_id = args['hash']
        if r.sadd("songs", song_id):
            info = ydl.extract_info('http://www.youtube.com/watch?v=' + args['hash'],  download=True)
            print song_id
            r.hset("song:%s" % song_id, "title", info['title'])
            r.hset("song:%s" % song_id, "song_title", '')
            r.hset("song:%s" % song_id, "artist", '')
            r.hset("song:%s" % song_id, "yt_hash", args['hash'])
            
            k = Key(bucket)
            k.key = args['hash'] + '.mp3'
            k.set_contents_from_filename(args['hash'] + '.mp3')
            url = k.generate_url(0, query_auth=False, force_http=True)
            os.remove(k.key)
            r.set("song:%s:url" % song_id, url)
            
            ret_song = {
            'title': info['title'],
            'song_title': '',
            'artist': '',
            'yt_hash': song_id,
            'url': url,
            'success': True,
            }
        else:
            title = r.hget("song:%s" % song_id, "title")
            song_title = r.hget("song:%s" % song_id, "song_title")
            artist = r.hget("song:%s" % song_id, "artist")
            yt_hash = r.hget("song:%s" % song_id, "yt_hash")
            url = r.hget("song:%s" % song_id, "url")
            
            ret_song = {
                'title': title,
                'song_title': song_title,
                'artist': artist,
                'yt_hash': yt_hash,
                'url': url,
                'success': False,
                'uploaded': True,
            }
        
        return ret_song, 201

class User(Resource):
    def get(self, username):
        args = parser.parse_args()
        if r.sismember("users", username):
            plays = r.hget("user:%s" % username, "plays")
            points = r.hget("user:%s" % username, "points")
            skips = r.hget("user:%s" % username, "skips")
            created_on = r.hget("user:%s" % username, "created_on")
            
            ret_user = {
                'username': username,
                'created_on': created_on,
                'plays': plays,
                'points': points,
                'skips': skips,
            }
        else:
            abort(404, message="error song {} not in db!".format(song_id))
        return ret_user, 200


class UserList(Resource):
    def get(self):
        ret_users = []
        users = r.smembers("users")
        for username in users:
            plays = r.hget("user:%s" % username, "plays")
            points = r.hget("user:%s" % username, "points")
            skips = r.hget("user:%s" % username, "skips")
            created_on = r.hget("user:%s" % username, "created_on")
            
            ret_user = {
                'username': username,
                'created_on': created_on,
                'plays': plays,
                'points': points,
                'skips': skips,
            }
            ret_users.append(ret_users)
        return ret_users

    def post(self):
        args = parser.parse_args()
        username = args['username']
        password = args['password']
        print username
        print password
        if r.sadd("users", username):
            ts = time.time()
            timestamp = int(ts)
            r.hset("user:%s" % username, "created_on", timestamp)
            r.hset("user:%s" % username, "plays", 0)
            r.hset("user:%s" % username, "points", 0)
            r.hset("user:%s" % username, "skips", 0)
            r.hset("user:%s" % username, "password", md5(password).hexdigest())
                
            ret_user = {
            'username': username,
            'created_on': timestamp,
            'plays': 0,
            'points': 0,
            'skips': 0,
            }
        else:
            abort(404, message="{'error': 'user {} already in db'}".format(username))
        
        return ret_user, 201

class Queue(Resource):
    def get(self, username):
        ret_songs = []
        song_hashes = r.lrange("queue:%s" % username, 0 ,-1)
        for song_id in song_hashes:
            title = r.hget("song:%s" % song_id, "title")
            song_title = r.hget("song:%s" % song_id, "song_title")
            artist = r.hget("song:%s" % song_id, "artist")
            yt_hash = r.hget("song:%s" % song_id, "yt_hash")
            
            key = bucket.get_key(song_id + '.mp3')
            url = key.generate_url(0, query_auth=False, force_http=True)
            
            ret_song = {
                'title': title,
                'song_title': song_title,
                'artist': artist,
                'yt_hash': yt_hash,
                'url': url,
            }
            ret_songs.append(ret_song)
        return ret_songs

    def post(self, username):
        args = parser.parse_args()
        song_id = args['hash']
        title = r.hget("song:%s" % song_id, "title")
        username = username

        if r.lpush("queue:%s" % username, song_id):
            ret = {
            'title': title,
            'song': song_id,
            'added': 1,
            }
        else:
            abort(404, message="{'error': 'user {} already in db'}".format(username))
        
        return ret, 201

class Room(Resource):
    def get(self, room):
        args = parser.parse_args()
        if r.sismember("rooms", room):
            users = r.hget("room:%s" % room, "users")
            current_song = r.hget("room:%s:" % room, "current_song")
            favorite_song = r.hget("room:%s" % room, "favorite_song")
            created_on = r.hget("room:%s" % room, "created_on")
            req_skips = r.hget("room:%s" % room, "req_skips")
            
            ret_room = {
                'room': room,
                'users': users,
                'created_on': created_on,
                'current_song': current_song,
                'favorite_song': favorite_song,
                'req_skips': req_skips,
            }
        else:
            abort(404, message="error song {} not in db!".format(song_id))
        return ret_room, 200


class RoomList(Resource):
    def get(self):
        ret_rooms = []
        rooms = r.smembers("rooms")
        for room in rooms:
            users = r.hget("room:%s" % room, "users")
            current_song = r.hget("room:%s:" % room, "current_song")
            favorite_song = r.hget("room:%s" % room, "favorite_song")
            created_on = r.hget("room:%s" % room, "created_on")
            req_skips = r.hget("room:%s" % room, "req_skips")
            
            ret_room = {
                'room': room,
                'users': users,
                'created_on': created_on,
                'current_song': current_song,
                'favorite_song': favorite_song,
                'req_skips': req_skips,
            }
            ret_rooms.append(ret_room)
        return ret_rooms

    def post(self):
        args = parser.parse_args()
        room = args['room']
        if r.sadd("rooms", room):
            ts = time.time()
            timestamp = int(ts)
            r.hset("room:%s" % room, "created_on", timestamp)
            r.hset("room:%s" % room, "users", 0)
            r.hset("room:%s" % room, "current_song", '')
            r.hset("room:%s" % room, "favorite_song", '')
            r.hset("room:%s" % room, "req_skips", 2)
                
            ret_room = {
                'room': room,
                'users': 0,
                'created_on': timestamp,
                'current_song': '',
                'favorite_song': '',
                'req_skips': req_skips,
            }
        else:
            abort(404, message="{'error': 'user {} already in db'}".format(room))
        
        return ret_room, 201

class DJList(Resource):
    def get(self, room):
        ret_users = []
        users = r.lrange("djlist:%s" % room, 0, -1)
        for username in users:
            plays = r.hget("user:%s" % username, "plays")
            points = r.hget("user:%s" % username, "points")
            skips = r.hget("user:%s" % username, "skips")
            created_on = r.hget("user:%s" % username, "created_on")
            next_song = r.lindex("user:%s:queue" % username, -1)
            ret_user = {
                'username': username,
                'created_on': created_on,
                'plays': plays,
                'points': points,
                'skips': skips,
                'next_song': next_song,
            }
            ret_users.append(ret_users)
        return ret_users

    def post(self):
        ret = {
            'error': 'not implemented',
        }
        return ret, 500

class Skip(Resource):
    def post(self, room):
        args = parser.parse_args()
        username = args['username']
        song_id = r.hget("room:%s" % room, "current_song")
        req_skips = r.hget("room:%s" % room, "req_skips")
        skips = r.hincrby("room:%s" % room, "skips", 1)
        print req_skips
        print skips
        print (skips >= req_skips)
        print (int(req_skips) <= int(skips))
        did_skip = (int(req_skips) <= int(skips))
        if (did_skip):
            for proc in psutil.process_iter():
                if proc.name() == 'ices':
                    os.kill(proc.pid, signal.SIGUSR1)		
            
        ret= {
            'song': song_id,
            'skips': skips,
            'req_skips': req_skips,
        }
        return ret, 200

class Join(Resource):
    def post(self, room):
        args = parser.parse_args()
        username = args['username']
        if r.sismember("rooms", room):
            if r.sismember("users", username):
                r.sadd("djset:%s" % room, username) 
                numDj = r.lpush("djlist:%s" % room, username)
                ret= {
                    'room': room,
                    'success': True,
                    'numDj': numDj,
                    'user': username,
                }

            else:
                ret= {
                    'room': room,
                    'success': False,
                    'error': 'user does not exist',
                    'user': username,
                }
        else:
            ret= {
                'room': room,
                'success': False,
                'error': 'room does not exist',
                'user': username,
            }
        return ret, 200

class Leave(Resource):
    def post(self, room):
        args = parser.parse_args()
        username = args['username']
        if r.sismember("rooms", room):
            if r.sismember("djset:%s" % room, username):
                r.srem("djset:%s" % room, username) 
                ret= {
                    'room': room,
                    'success': True,
                    'removed': True,
                    'user': username,
                }

            else:
                ret= {
                    'room': room,
                    'success': False,
                    'error': 'user is not in this room',
                    'user': username,
                }
        else:
            ret= {
                'room': room,
                'success': False,
                'error': 'room does not exist',
                'user': username,
            }
        return ret, 200
##
## Actually setup the Api resource routing here
##
api.add_resource(SongList, '/api/songs')
api.add_resource(Song, '/api/songs/<string:song_id>')
api.add_resource(UserList, '/api/users')
api.add_resource(User, '/api/users/<string:username>')
api.add_resource(Queue, '/api/users/<string:username>/queue')
api.add_resource(RoomList, '/api/rooms')
api.add_resource(Room, '/api/rooms/<string:room>')
api.add_resource(DJList, '/api/rooms/<string:room>/djlist')
api.add_resource(Skip, '/api/rooms/<string:room>/skip')
api.add_resource(Join, '/api/rooms/<string:room>/join')
api.add_resource(Leave, '/api/rooms/<string:room>/leave')

if __name__ == '__main__':
      app.run(debug=True)
