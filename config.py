from dotenv import load_dotenv
import os

load_dotenv()

from app import app

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'] = os.getenv('UPLOAD_FOLDER_SONG_THUMBNAIL')
app.config['UPLOAD_FOLDER_AUDIO'] = os.getenv('UPLOAD_FOLDER_AUDIO')
app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'] = os.getenv('UPLOAD_FOLDER_ALBUM_THUMBNAIL')
app.config['PLAYLIST_THUMBNAIL'] = os.getenv('PLAYLIST_THUMBNAIL')
app.config['GRAPH_FOLDER'] = os.getenv('GRAPH_FOLDER')