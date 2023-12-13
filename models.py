from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import app

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    blacklist = db.Column(db.Boolean, default=False)
    albums = db.relationship('Album', backref='artist', lazy=True)
    songs = db.relationship('Song', backref='artist', lazy=True)
    playlists = db.relationship('Playlist', backref='user', lazy=True)
    admins = db.relationship('Admin', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passhash, password)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    lyrics = db.Column(db.Text)
    release_date = db.Column(db.Date)
    genre = db.Column(db.String(64))
    flag = db.Column(db.Boolean, default=False)
    thumbnail = db.Column(db.String(255), nullable=False, unique=True)
    music_src = db.Column(db.String(255), nullable=False, unique=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    release_date = db.Column(db.Date)
    genre = db.Column(db.String(64))
    thumbnail = db.Column(db.String(255), nullable=False, unique=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class AlbumSong(db.Model):
    album_id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, primary_key=True)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class PlaylistSong(db.Model):
    playlist_id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, primary_key=True)

class Rating(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, primary_key=True)
    rating_value = db.Column(db.Float, default=0.0)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passhash, password)

with app.app_context():
    db.create_all()
    admin = Admin.query.filter_by(name='admin').first()
    if admin is None:
        admin_user = User(username='admin', password='admin', name='admin', role='Creator')
        db.session.add(admin_user)
        db.session.commit()

        admin = Admin(name='admin', user_id=admin_user.id, password='admin')
        db.session.add(admin)
        db.session.commit()