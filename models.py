from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import app

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passhash, password)

# class Album(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), nullable=False)
#     artist_id = db.Column(db.Integer, nullable=False)
#     release_date = db.Column(db.Date)
#
# class Song(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), nullable=False)
#     lyrics = db.Column(db.Text)
#     duration = db.Column(db.Integer)
#     date_created = db.Column(db.Date)
#     album_id = db.Column(db.Integer)
#
# class Playlist(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), nullable=False)
#     user_id = db.Column(db.Integer)
#
# class PlaylistSong(db.Model):
#     playlist_id = db.Column(db.Integer, primary_key=True)
#     song_id = db.Column(db.Integer, primary_key=True)
#
# class Rating(db.Model):
#     user_id = db.Column(db.Integer, primary_key=True)
#     song_id = db.Column(db.Integer, primary_key=True)
#     rating_value = db.Column(db.Float)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(is_admin=True).first()
    if admin is None:
        admin = User(username='admin', password='admin', name='admin', role='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()