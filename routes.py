from flask import render_template, request, redirect, url_for, flash, session
from models import User, Album, AlbumSong, Song, Playlist, PlaylistSong, Rating, db, Admin
from app import app
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy.sql.expression import func
import matplotlib.pyplot as plt
from functools import wraps



MAX_FILE_SIZE = 10 * 1024 * 1024

def is_blacklist(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            user = User.query.filter_by(id=session['user_id']).first()
            if user and user.blacklist:
                flash('You are blacklisted', 'info')
                return redirect(url_for('logout'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/')
@is_blacklist
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        if not os.path.exists(app.config['PLAYLIST_THUMBNAIL']):
            os.makedirs(app.config['PLAYLIST_THUMBNAIL'])

        song_random = Song.query.order_by(func.random()).limit(4).all()
        album_random = Album.query.order_by(func.random()).limit(4).all()
        playlist_random = Playlist.query.filter_by(user_id=session['user_id']).order_by(func.random()).limit(4).all()
        return render_template('index.html', songs=song_random, albums=album_random, playlists=playlist_random, Admin=Admin)

@app.route('/signup', methods = ['POST','GET'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index', Admin=Admin))
    else:
        if request.method == 'POST':
            username = request.form.get('username')
            name = request.form.get('name')
            roles = ['Creator', 'Listener']
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = roles[int(request.form.get('role')) - 1]

            if username == '' or name == '' or password == '' or confirm_password == '':
                flash('Please fill out all fields', 'info')
                return redirect(url_for('signup'))

            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('signup'))

            user = User.query.filter_by(username=username).first()
            if user is not None:
                flash('Username already exists', 'error')
                return redirect(url_for('signup'))

            new_user = User(username=username, password=password, name=name, role=role)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

        else:
            return render_template('signup.html')


@app.route('/login', methods = ['POST','GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index', Admin=Admin))
    else:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user is None:
                flash('Username does not exist', 'error')
                return redirect(url_for('login'))
            elif not user.verify_password(password):
                flash('Incorrect password', 'error')
                return redirect(url_for('login'))
            else:
                session['user_id'] = user.id
                return redirect(url_for('index', Admin=Admin))
        else:
            return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/profile')
@is_blacklist
def profile():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('profile.html', user=user, Admin=Admin)

@app.route('/change_password', methods = ['GET','POST'])
@is_blacklist
def change_password():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        user = User.query.filter_by(id=session['user_id']).first()
        old_password = request.form.get('old_password')

        if not user.verify_password(old_password):
            flash('Incorrect password', 'error')
            return redirect(url_for('profile', Admin=Admin))

        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('profile', Admin=Admin))

        user.password = new_password
        db.session.commit()
        flash('Password changed', 'info')
        return redirect(url_for('profile', Admin=Admin))

@app.route('/become_creator', methods=['GET','POST'])
@is_blacklist
def become_creator():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        user = User.query.filter_by(id=session['user_id']).first()
        user.role = 'Creator'
        db.session.commit()
        flash('You are now a creator', 'info')
        return redirect(url_for('profile', Admin=Admin))

@app.route('/my_songs')
@is_blacklist
def my_songs():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        user = User.query.filter_by(id=session['user_id']).first()
        songs = Song.query.filter_by(artist_id=user.id).all()
        return render_template('my_songs.html', user=user, songs=songs, Admin=Admin)

@app.route('/my_albums')
@is_blacklist
def my_albums():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        user = User.query.filter_by(id=session['user_id']).first()
        albums = Album.query.filter_by(artist_id=user.id).all()
        return render_template('my_albums.html', user=user, albums=albums, Admin=Admin)

@app.route('/my_playlists')
@is_blacklist
def my_playlists():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        user = User.query.filter_by(id=session['user_id']).first()
        playlists = Playlist.query.filter_by(user_id=user.id).all()
        return render_template('my_playlists.html', user=user, playlists=playlists, Admin=Admin)

@app.route('/my_songs/upload', methods=['GET','POST'])
@is_blacklist
def upload_song():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    elif User.query.filter_by(id=session['user_id']).first().role != 'Creator':
        flash('You must be a creator to upload songs', 'info')
        return redirect(url_for('index', Admin=Admin))
    else:

        if request.method == 'POST':
            user = User.query.filter_by(id=session['user_id']).first()
            title = request.form.get('title')
            genre = request.form.get('genre')
            lyrics = request.form.get('lyrics')
            thumbnail = request.files['thumbnail']
            audio = request.files['audio']

            if title == '' or genre == '' or thumbnail.filename == '' or audio.filename == '':
                flash('Please fill out all fields', 'info')
                return redirect(url_for('upload_song', Admin=Admin))

            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('upload_song', Admin=Admin))

            if audio.filename.split('.')[-1] not in ['mp3']:
                flash('Audio must be a mp3 file', 'info')
                return redirect(url_for('upload_song', Admin=Admin))

            if not os.path.exists(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL']):
                os.makedirs(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'])

            if not os.path.exists(app.config['UPLOAD_FOLDER_AUDIO']):
                os.makedirs(app.config['UPLOAD_FOLDER_AUDIO'])

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('upload_song', Admin=Admin))

            if audio.content_length > MAX_FILE_SIZE:
                flash('Audio must be less than 10 MB', 'info')
                return redirect(url_for('upload_song', Admin=Admin))

            thumbnail_filename = secure_filename(thumbnail.filename)
            audio_filename = secure_filename(audio.filename)

            song = Song(
                name=title,
                genre=genre,
                lyrics=lyrics,
                thumbnail=thumbnail_filename,
                music_src=audio_filename,
                artist_id=user.id,
                release_date=datetime.now().date())

            db.session.add(song)
            db.session.commit()

            song_id = song.id

            db.session.expunge(song)

            thumbnail_filename = f"{song.id}.{thumbnail.filename.split('.')[-1]}"
            audio_filename = f"{song.id}.{audio.filename.split('.')[-1]}"

            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], thumbnail_filename))
            audio.save(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], audio_filename))

            song = Song.query.filter_by(id=song_id).first()

            song.thumbnail = thumbnail_filename
            song.music_src = audio_filename

            db.session.commit()

            flash('Song uploaded', 'info')
            return redirect(url_for('my_songs', Admin=Admin))
        else:
            return render_template('upload_song.html', Admin=Admin)

@app.route('/my_songs/edit/<song_id>', methods=['GET','POST'])
@is_blacklist
def edit_song(song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))



    if session['user_id'] != Song.query.filter_by(id=song_id).first().artist_id:
        flash('You are not authorized to edit this song', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        title = request.form.get('title')
        genre = request.form.get('genre')
        lyrics = request.form.get('lyrics')
        thumbnail = request.files['thumbnail']
        audio = request.files['audio']

        if title == '' or genre == '':
            flash("Title and Genre can't be empty", 'info')
            return redirect(url_for('edit_song', song_id=song_id, Admin=Admin))

        song = Song.query.filter_by(id=song_id).first()
        song.name = title
        song.genre = genre
        song.lyrics = lyrics
        db.session.commit()

        if thumbnail.filename != '':
            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('edit_song', song_id=song_id, Admin=Admin))

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('edit_song', song_id=song_id, Admin=Admin))


            os.remove(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], song.thumbnail))

            thumbnail_filename = secure_filename(thumbnail.filename)
            thumbnail_filename = f"{song.id}.{thumbnail_filename.split('.')[-1]}"
            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], thumbnail_filename))
            song.thumbnail = thumbnail_filename
            db.session.commit()

        if audio.filename != '':
            if audio.filename.split('.')[-1] not in ['mp3']:
                flash('Audio must be a mp3 file', 'info')
                return redirect(url_for('edit_song', song_id=song_id, Admin=Admin))

            if audio.content_length > MAX_FILE_SIZE:
                flash('Audio must be less than 10 MB', 'info')
                return redirect(url_for('edit_song', song_id=song_id, Admin=Admin))

            os.remove(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], song.music_src))

            audio_filename = secure_filename(audio.filename)
            audio_filename = f"{song.id}.{audio_filename.split('.')[-1]}"
            audio.save(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], audio_filename))
            song.music_src = audio_filename
            db.session.commit()

        flash('Song updated', 'info')
        return redirect(url_for('my_songs', Admin=Admin))

    else:
        song = Song.query.filter_by(id=song_id).first()
        return render_template('edit_song.html', song=song, Admin=Admin)

@app.route('/my_songs/delete/<song_id>')
@is_blacklist
def delete_song(song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Song.query.filter_by(id=song_id).first().artist_id:
        flash('You are not authorized to delete this song', 'info')
        return redirect(url_for('index', Admin=Admin))

    song = Song.query.filter_by(id=song_id).first()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], song.thumbnail))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], song.music_src))
    db.session.delete(song)
    db.session.commit()
    flash('Song deleted', 'info')
    return redirect(url_for('my_songs', Admin=Admin))

@app.route('/my_albums/create', methods=['GET','POST'])
@is_blacklist
def create_album():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    if User.query.filter_by(id=session['user_id']).first().role != 'Creator':
        flash('You must be a creator to create albums', 'info')
        return redirect(url_for('index', Admin=Admin))
    else:

        if request.method == 'POST':
            user = User.query.filter_by(id=session['user_id']).first()
            album_name = request.form.get('album_name')
            genre = request.form.get('genre')

            thumbnail = request.files['thumbnail']

            if album_name == '' or genre == '' or thumbnail.filename == '':
                flash('Please fill out all fields', 'info')
                return redirect(url_for('create_album', Admin=Admin))

            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('upload_album', Admin=Admin))

            if not os.path.exists(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL']):
                os.makedirs(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'])

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('upload_album', Admin=Admin))

            thumbnail_filename = secure_filename(thumbnail.filename)

            album = Album(
                name=album_name,
                genre=genre,
                thumbnail=thumbnail_filename,
                artist_id=user.id,
                release_date=datetime.now().date())

            db.session.add(album)
            db.session.commit()

            album_id = album.id

            db.session.expunge(album)

            thumbnail_filename = f"{album.id}.{thumbnail.filename.split('.')[-1]}"
            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], thumbnail_filename))

            album = Album.query.filter_by(id=album_id).first()

            album.thumbnail = thumbnail_filename
            db.session.commit()

            return redirect(url_for('add_song_to_album', album_id=album_id, Admin=Admin))

        else:
            return render_template('create_album.html', Admin=Admin)

@app.route('/my_albums/create/<album_id>', methods=['GET','POST'])
@is_blacklist
def add_song_to_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    if User.query.filter_by(id=session['user_id']).first().role != 'Creator':
        flash('You must be a creator to add songs to albums', 'info')
        return redirect(url_for('index', Admin=Admin))
    else:

        if request.method == 'POST':
            album_songs = request.form.getlist('song')
            for song in album_songs:
                song = Song.query.filter_by(id=song).first()
                album_song = AlbumSong(album_id=album_id, song_id=song.id)
                db.session.add(album_song)
            db.session.commit()

            flash('Song added to album', 'info')
            return redirect(url_for('my_albums', Admin=Admin))
        else:
            user = User.query.filter_by(id=session['user_id']).first()
            songs = Song.query.filter_by(artist_id=user.id).all()
            return render_template('add_song_to_album.html',album_id=album_id, songs=songs, Admin=Admin)

@app.route('/my_albums/edit/<album_id>', methods=['GET','POST'])
@is_blacklist
def edit_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to edit this album', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        album_name = request.form.get('title')
        genre = request.form.get('genre')
        thumbnail = request.files['thumbnail']

        if album_name == '' or genre == '':
            flash("Title and Genre can't be empty", 'info')
            return redirect(url_for('edit_album', album_id=album_id, Admin=Admin))

        album = Album.query.filter_by(id=album_id).first()
        album.name = album_name
        album.genre = genre
        db.session.commit()

        if thumbnail.filename != '':
            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('edit_album', album_id=album_id, Admin=Admin))

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('edit_album', album_id=album_id, Admin=Admin))

            os.remove(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], album.thumbnail))

            thumbnail_filename = secure_filename(thumbnail.filename)
            thumbnail_filename = f"{album.id}.{thumbnail_filename.split('.')[-1]}"
            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], thumbnail_filename))
            album.thumbnail = thumbnail_filename
            db.session.commit()

        flash('Album updated', 'info')
        return redirect(url_for('my_albums', Admin=Admin))

    else:
        album = Album.query.filter_by(id=album_id).first()
        return render_template('edit_album.html', album=album, Admin=Admin)

@app.route('/my_albums/edit/<album_id>/add_song', methods=['GET','POST'])
@is_blacklist
def edit_add_to_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to edit this album', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        album_songs = request.form.getlist('song')
        for song in album_songs:
            song = Song.query.filter_by(id=song).first()
            album_song = AlbumSong(album_id=album_id, song_id=song.id)
            db.session.add(album_song)
        db.session.commit()

        flash('Songs added to album', 'info')
        return redirect(url_for('my_albums', Admin=Admin))

    else:
        user = User.query.filter_by(id=session['user_id']).first()
        songs = Song.query.filter_by(artist_id=user.id).all()
        song_list = []
        for song in songs:
            album_song = AlbumSong.query.filter_by(album_id=album_id, song_id=song.id).first()
            if album_song is None:
                song_list.append(song)
        return render_template('edit_add_to_album.html',album_id=album_id, songs=song_list, Admin=Admin)

@app.route('/my_albums/edit/<album_id>/remove_song', methods=['GET','POST'])
@is_blacklist
def edit_remove_from_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to edit this album', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        album_songs = request.form.getlist('song')
        for song in album_songs:
            song = Song.query.filter_by(id=song).first()
            album_song = AlbumSong.query.filter_by(album_id=album_id, song_id=song.id).first()
            db.session.delete(album_song)
        db.session.commit()

        flash('Songs removed from album', 'info')
        return redirect(url_for('my_albums', Admin=Admin))

    else:
        user = User.query.filter_by(id=session['user_id']).first()
        songs = Song.query.filter_by(artist_id=user.id).all()
        song_list = []
        for song in songs:
            album_song = AlbumSong.query.filter_by(album_id=album_id, song_id=song.id).first()
            if album_song is not None:
                song_list.append(song)
        return render_template('edit_remove_from_album.html', Admin=Admin,album_id=album_id, songs=song_list)

@app.route('/my_albums/delete/<album_id>')
@is_blacklist
def delete_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to delete this album', 'info')
        return redirect(url_for('index', Admin=Admin))

    album = Album.query.filter_by(id=album_id).first()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], album.thumbnail))
    album_songs = AlbumSong.query.filter_by(album_id=album_id).all()
    db.session.delete(album)
    for album_song in album_songs:
        db.session.delete(album_song)
    db.session.commit()
    flash('Album deleted', 'info')
    return redirect(url_for('my_albums', Admin=Admin))

@app.route('/my_albums/<album_id>')
@is_blacklist
def my_albums_view(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to enter this page', 'info')
        return redirect(url_for('index', Admin=Admin))

    album = Album.query.filter_by(id=album_id).first()
    songs = AlbumSong.query.filter_by(album_id=album_id).all()
    song_list = []
    for song in songs:
        song_list.append(Song.query.filter_by(id=song.song_id).first())
    return render_template('my_albums_view.html', Admin=Admin, album=album, songs=song_list)

@app.route('/album/<album_id>')
@is_blacklist
def album_view(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    album = Album.query.filter_by(id=album_id).first()
    songs = AlbumSong.query.filter_by(album_id=album_id).all()
    song_list = []
    for song in songs:
        song_list.append(Song.query.filter_by(id=song.song_id).first())
    return render_template('album_view.html', Admin=Admin, album=album, songs=song_list)

@app.route('/my_albums/<album_id>/remove_song/<song_id>')
@is_blacklist
def my_albums_remove_song(album_id, song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login', Admin=Admin))


    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to remove songs from this album', 'info')
        return redirect(url_for('index', Admin=Admin))

    album_song = AlbumSong.query.filter_by(album_id=album_id, song_id=song_id).first()
    db.session.delete(album_song)
    db.session.commit()
    flash('Song removed from album', 'info')
    return redirect(url_for('my_albums_view', album_id=album_id, Admin=Admin))



@app.route('/my_playlists/create', methods=['GET','POST'])
@is_blacklist
def create_playlist():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:


        if request.method == 'POST':
            user = User.query.filter_by(id=session['user_id']).first()
            playlist_name = request.form.get('playlist_name')

            if playlist_name == '':
                flash('Please fill out all fields', 'info')
                return redirect(url_for('create_playlist', Admin=Admin))

            playlist = Playlist(
                name=playlist_name,
                user_id=user.id)

            db.session.add(playlist)
            db.session.commit()

            return redirect(url_for('add_song_to_playlist', playlist_id=playlist.id, Admin=Admin))

        else:
            return render_template('create_playlist.html', Admin=Admin)

@app.route('/my_playlists/create/<playlist_id>', methods=['GET','POST'])
@is_blacklist
def add_song_to_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:


        if request.method == 'POST':
            playlist_songs = request.form.getlist('song')
            for song in playlist_songs:
                song = Song.query.filter_by(id=song).first()
                playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song.id)
                db.session.add(playlist_song)
            db.session.commit()

            flash('Song added to playlist', 'info')
            return redirect(url_for('my_playlists', Admin=Admin))
        else:
            songs = Song.query.all()
            return render_template('add_song_to_playlist.html', Admin=Admin,playlist_id=playlist_id, songs=songs)

@app.route('/my_playlists/edit/<playlist_id>', methods=['GET','POST'])
@is_blacklist
def edit_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))


    if session['user_id'] != Playlist.query.filter_by(id=playlist_id).first().user_id:
        flash('You are not authorized to edit this playlist', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        playlist_name = request.form.get('title')

        if playlist_name == '':
            flash("Title can't be empty", 'info')
            return redirect(url_for('edit_playlist', Admin=Admin, playlist_id=playlist_id))

        playlist = Playlist.query.filter_by(id=playlist_id).first()
        playlist.name = playlist_name
        db.session.commit()

        flash('Playlist updated', 'info')
        return redirect(url_for('my_playlists', Admin=Admin))

    else:
        playlist = Playlist.query.filter_by(id=playlist_id).first()
        return render_template('edit_playlist.html', Admin=Admin, playlist=playlist)

@app.route('/my_playlists/edit/<playlist_id>/add_song', methods=['GET','POST'])
@is_blacklist
def edit_add_to_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))


    if session['user_id'] != Playlist.query.filter_by(id=playlist_id).first().user_id:
        flash('You are not authorized to edit this playlist', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        playlist_songs = request.form.getlist('song')
        for song in playlist_songs:
            song = Song.query.filter_by(id=song).first()
            playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song.id)
            db.session.add(playlist_song)
        db.session.commit()

        flash('Songs added to playlist', 'info')
        return redirect(url_for('my_playlists', Admin=Admin))

    else:
        songs = Song.query.all()
        song_list = []
        for song in songs:
            playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song.id).first()
            if playlist_song is None:
                song_list.append(song)
        return render_template('edit_add_to_playlist.html', Admin=Admin,playlist_id=playlist_id, songs=song_list)

@app.route('/my_playlists/edit/<playlist_id>/remove_song', methods=['GET','POST'])
@is_blacklist
def edit_remove_from_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))


    if session['user_id'] != Playlist.query.filter_by(id=playlist_id).first().user_id:
        flash('You are not authorized to edit this playlist', 'info')
        return redirect(url_for('index', Admin=Admin))

    if request.method == 'POST':
        playlist_songs = request.form.getlist('song')
        for song in playlist_songs:
            song = Song.query.filter_by(id=song).first()
            playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song.id).first()
            db.session.delete(playlist_song)
        db.session.commit()

        flash('Songs removed from playlist', 'info')
        return redirect(url_for('my_playlists', Admin=Admin))

    else:
        songs = Song.query.all()
        song_list = []
        for song in songs:
            playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song.id).first()
            if playlist_song is not None:
                song_list.append(song)
        return render_template('edit_remove_from_playlist.html', Admin=Admin,playlist_id=playlist_id, songs=song_list)

@app.route('/my_playlists/delete/<playlist_id>')
@is_blacklist
def delete_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))


    if session['user_id'] != Playlist.query.filter_by(id=playlist_id).first().user_id:
        flash('You are not authorized to delete this playlist', 'info')
        return redirect(url_for('index', Admin=Admin))

    playlist = Playlist.query.filter_by(id=playlist_id).first()
    playlist_songs = PlaylistSong.query.filter_by(playlist_id=playlist_id).all()
    db.session.delete(playlist)
    for playlist_song in playlist_songs:
        db.session.delete(playlist_song)
    db.session.commit()
    flash('Playlist deleted', 'info')
    return redirect(url_for('my_playlists', Admin=Admin))

@app.route('/my_playlists/<playlist_id>')
@is_blacklist
def my_playlists_view(playlist_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))


    if session['user_id'] != Playlist.query.filter_by(id=playlist_id).first().user_id:
        flash('You are not authorized to enter this page', 'info')
        return redirect(url_for('index', Admin=Admin))

    playlist = Playlist.query.filter_by(id=playlist_id).first()
    songs = PlaylistSong.query.filter_by(playlist_id=playlist_id).all()
    song_list = []
    for song in songs:
        song_list.append(Song.query.filter_by(id=song.song_id).first())
    return render_template('my_playlists_view.html', playlist=playlist, songs=song_list, Admin=Admin)

@app.route('/my_playlists/<playlist_id>/remove_song/<song_id>')
@is_blacklist
def my_playlists_remove_song(playlist_id, song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Playlist.query.filter_by(id=playlist_id).first().user_id:
        flash('You are not authorized to remove songs from this playlist', 'info')
        return redirect(url_for('index', Admin=Admin))

    playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
    db.session.delete(playlist_song)
    db.session.commit()
    flash('Song removed from playlist', 'info')
    return redirect(url_for('my_playlists_view', playlist_id=playlist_id, Admin=Admin))

@app.route('/song/<song_id>')
@is_blacklist
def song_view(song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    song = Song.query.filter_by(id=song_id).first()
    return render_template('song_view.html', song=song, Admin=Admin)

@app.route('/song/<song_id>/rate', methods=['GET','POST'])
@is_blacklist
def rate_song(song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:

        if request.method == 'POST':
            new_rating = request.form.get('rating')
            song = Song.query.filter_by(id=song_id).first()
            user = User.query.filter_by(id=session['user_id']).first()
            if Rating.query.filter_by(song_id=song_id, user_id=session['user_id']).first() is not None:
                old_rating = Rating.query.filter_by(song_id=song_id, user_id=session['user_id']).first()
                old_rating.rating_value = new_rating
                db.session.commit()
                flash('Song rated', 'info')
                return redirect(url_for('song_view', song_id=song_id, Admin=Admin))
            rating = Rating(song_id=song.id, user_id=user.id, rating_value=new_rating)
            db.session.add(rating)
            db.session.commit()
            flash('Song rated', 'info')
            return redirect(url_for('song_view', song_id=song_id, Admin=Admin))
        else:
            song = Song.query.filter_by(id=song_id).first()
            rating = Rating.query.filter_by(song_id=song_id, user_id=session['user_id']).first()
            return render_template('rate_song.html', song=song, rating=rating, Admin=Admin)

@app.route('/search', methods=['GET','POST'])
@is_blacklist
def search():
    if request.method == 'POST':
        search = request.form.get('search')
        session['search'] = search
        session['s_type'] = 'All'
        session['s_genre'] = 'All'
        songs = Song.query.filter(Song.name.like(f'%{search}%') ).all()
        albums = Album.query.filter(Album.name.like(f'%{search}%')).all()
        return render_template('search.html', songs=songs, albums=albums, Admin=Admin)
    else:
        return render_template('search.html')

@app.route('/search/filter', methods=['GET','POST'])
@is_blacklist
def filter():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if request.method == 'POST':
        search = session['search']

        type = request.form.get('type')
        session['s_type'] = type

        genre = request.form.get('genre')
        session['s_genre'] = genre

        if type == 'song':
            if genre == 'All':
                songs = Song.query.filter(Song.name.like(f'%{search}%')).all()
            else:
                songs = Song.query.filter(Song.name.like(f'%{search}%'), Song.genre.like(f'%{genre}%')).all()
            return render_template('search.html', songs=songs, albums=[], Admin=Admin)
        elif type == 'album':
            if genre == 'All':
                albums = Album.query.filter(Album.name.like(f'%{search}%')).all()
            else:
                albums = Album.query.filter(Album.name.like(f'%{search}%'), Album.genre.like(f'%{genre}%')).all()
            return render_template('search.html', songs=[], albums=albums, Admin=Admin)
        else:
            if genre == 'All':
                songs = Song.query.filter(Song.name.like(f'%{search}%')).all()
                albums = Album.query.filter(Album.name.like(f'%{search}%')).all()
            else:
                songs = Song.query.filter(Song.name.like(f'%{search}%'), Song.genre.like(f'%{genre}%')).all()
                albums = Album.query.filter(Album.name.like(f'%{search}%'), Album.genre.like(f'%{genre}%')).all()
            return render_template('search.html', songs=songs, albums=albums, Admin=Admin)
    else:
        return render_template('search.html', Admin=Admin)

@app.route('/admin_login', methods = ['POST','GET'])
def admin_login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    else:

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            admin = Admin.query.filter_by(name=username).first()

            if admin is None:
                flash('Username does not exist', 'error')
                return redirect(url_for('admin_login'))
            elif not admin.verify_password(password):
                flash('Incorrect password', 'error')
                return redirect(url_for('admin_login'))
            else:
                session['user_id'] = admin.id
                return redirect(url_for('admin', Admin=Admin))
        else:
            return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        songs = Song.query.all()
        albums = Album.query.all()
        users = User.query.all()

        top_songs = db.session.query(Song.name, db.func.avg(Rating.rating_value)).join(Rating,Song.id == Rating.song_id).group_by(Song.name).order_by(db.func.avg(Rating.rating_value).desc()).limit(5).all()

        song_names = [song[0] for song in top_songs]
        song_ratings = [song[1] for song in top_songs]

        plt.bar(song_names, song_ratings)
        plt.xlabel('Song Name')
        plt.ylabel('Average Rating')
        plt.title('Top 5 Songs by Rating')
        graph_folder = app.config['GRAPH_FOLDER']
        if not os.path.exists(graph_folder):
            os.makedirs(graph_folder)
        plt.savefig(os.path.join(graph_folder, 'top_songs.png'))
        plt.clf()

        top_creators = db.session.query(User.name, db.func.count(Song.id)).join(Song, User.id == Song.artist_id).group_by(User.name).order_by(db.func.count(Song.id).desc()).limit(5).all()

        creator_names = [creator[0] for creator in top_creators]
        creator_song_counts = [creator[1] for creator in top_creators]

        plt.bar(creator_names, creator_song_counts)
        plt.xlabel('Creator Name')
        plt.ylabel('Number of Songs')
        plt.title('Top 5 Creators by Number of Songs')
        plt.savefig(os.path.join(graph_folder, 'top_creators.png'))
        plt.clf()

        num_creators = sum(1 for user in users if user.role == 'Creator')
        num_non_creators = len(users) - num_creators

        plt.pie([num_creators, num_non_creators], labels=['Creators', 'Non-Creators'], autopct='%1.1f%%')
        plt.title('User Roles')
        plt.savefig(os.path.join(graph_folder, 'user_roles.png'))
        plt.clf()

        return render_template('admin.html', Admin=Admin, songs=songs, albums=albums, users=users)

@app.route('/admin/song_management', methods=['GET','POST'])
def song_management():
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        if request.method == 'POST':
            song_search = request.form.get('song_search')
            session['song_search_admin'] = song_search
            songs = Song.query.filter(Song.name.like(f'%{song_search}%')).all()

            return redirect(url_for('song_management', songs=songs, Admin=Admin))
        else:
            songs = Song.query.all()
            return render_template('song_management.html', songs=songs, Admin=Admin)

@app.route('/remove/song/<song_id>')
def remove_song(song_id):
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        song = Song.query.filter_by(id=song_id).first()
        os.remove(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], song.thumbnail))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], song.music_src))
        db.session.delete(song)
        db.session.commit()
        flash('Song deleted', 'info')
        return redirect(url_for('song_management'))

@app.route('/admin/album_management', methods=['GET','POST'])
def album_management():
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        if request.method == 'POST':
            album_search = request.form.get('album_search')
            session['album_search_admin'] = album_search
            albums = Album.query.filter(Album.name.like(f'%{album_search}%')).all()

            return render_template('album_management.html', albums=albums, Admin=Admin)
        else:
            albums = Album.query.all()
            return render_template('album_management.html', albums=albums, Admin=Admin)

@app.route('/remove/album/<album_id>')
def remove_album(album_id):
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        album = Album.query.filter_by(id=album_id).first()
        os.remove(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], album.thumbnail))
        album_songs = AlbumSong.query.filter_by(album_id=album_id).all()
        db.session.delete(album)
        for album_song in album_songs:
            db.session.delete(album_song)
        db.session.commit()
        flash('Album deleted', 'info')
        return redirect(url_for('album_management', Admin=Admin))

@app.route('/admin/user_management', methods=['GET','POST'])
def user_management():
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        if request.method == 'POST':
            user_search = request.form.get('user_search')
            session['user_search_admin'] = user_search
            users = User.query.filter(User.name.like(f'%{user_search}%')).all()
            final_users = []
            for user in users:
                if Admin.query.filter_by(id=user.id).first():
                    continue
                else:
                    final_users.append(user)

            return render_template('user_management.html', users=final_users, Admin=Admin)
        else:
            users = User.query.all()
            final_users = []
            for user in users:
                if Admin.query.filter_by(id=user.id).first():
                    continue
                else:
                    final_users.append(user)
            return render_template('user_management.html', users=final_users, Admin=Admin)

@app.route('/blacklist/user/<user_id>')
def blacklist(user_id):
    if 'user_id' not in session or (Admin.query.filter_by(id=session['user_id']).first() is None):
        flash('Please log in', 'info')
        return redirect(url_for('admin_login'))
    else:
        user = User.query.filter_by(id=user_id).first()
        user.blacklist = True
        db.session.commit()
        flash('User blacklisted', 'info')
        return redirect(url_for('user_management'))