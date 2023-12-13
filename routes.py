from flask import render_template, request, redirect, url_for, flash, session
from models import User, Album, AlbumSong, Song, Playlist, PlaylistSong, Rating, db
from app import app
import os
from datetime import datetime
from werkzeug.utils import secure_filename

MAX_FILE_SIZE = 10 * 1024 * 1024

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        return render_template('index.html')

@app.route('/signup', methods = ['POST','GET'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
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
        return redirect(url_for('index'))
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
                return redirect(url_for('index'))
        else:
            return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('profile.html', user=user)

@app.route('/change_password', methods = ['GET','POST'])
def change_password():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        old_password = request.form.get('old_password')

        if not user.verify_password(old_password):
            flash('Incorrect password', 'error')
            return redirect(url_for('profile'))

        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('profile'))

        user.password = new_password
        db.session.commit()
        flash('Password changed', 'info')
        return redirect(url_for('profile'))

@app.route('/become_creator', methods=['GET','POST'])
def become_creator():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        user.role = 'Creator'
        db.session.commit()
        flash('You are now a creator', 'info')
        return redirect(url_for('profile'))

@app.route('/my_songs')
def my_songs():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        songs = Song.query.filter_by(artist_id=user.id).all()
        return render_template('my_songs.html', user=user, songs=songs)

@app.route('/my_albums')
def my_albums():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        albums = Album.query.filter_by(artist_id=user.id).all()
        return render_template('my_albums.html', user=user, albums=albums)

@app.route('/my_playlists')
def my_playlists():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        playlists = Playlist.query.filter_by(user_id=user.id).all()
        return render_template('my_playlists.html', user=user, playlists=playlists)

@app.route('/my_songs/upload', methods=['GET','POST'])
def upload_song():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    elif User.query.filter_by(id=session['user_id']).first().role != 'Creator':
        flash('You must be a creator to upload songs', 'info')
        return redirect(url_for('index'))
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
                return redirect(url_for('upload_song'))

            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('upload_song'))

            if audio.filename.split('.')[-1] not in ['mp3']:
                flash('Audio must be a mp3 file', 'info')
                return redirect(url_for('upload_song'))

            if not os.path.exists(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL']):
                os.makedirs(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'])

            if not os.path.exists(app.config['UPLOAD_FOLDER_AUDIO']):
                os.makedirs(app.config['UPLOAD_FOLDER_AUDIO'])

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('upload_song'))

            if audio.content_length > MAX_FILE_SIZE:
                flash('Audio must be less than 10 MB', 'info')
                return redirect(url_for('upload_song'))

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
            return redirect(url_for('my_songs'))
        else:
            return render_template('upload_song.html')

@app.route('/my_songs/edit/<song_id>', methods=['GET','POST'])
def edit_song(song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Song.query.filter_by(id=song_id).first().artist_id:
        flash('You are not authorized to edit this song', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        genre = request.form.get('genre')
        lyrics = request.form.get('lyrics')
        thumbnail = request.files['thumbnail']
        audio = request.files['audio']

        if title == '' or genre == '':
            flash("Title and Genre can't be empty", 'info')
            return redirect(url_for('edit_song', song_id=song_id))

        song = Song.query.filter_by(id=song_id).first()
        song.name = title
        song.genre = genre
        song.lyrics = lyrics
        db.session.commit()

        if thumbnail.filename != '':
            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('edit_song', song_id=song_id))

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('edit_song', song_id=song_id))


            os.remove(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], song.thumbnail))

            thumbnail_filename = secure_filename(thumbnail.filename)
            thumbnail_filename = f"{song.id}.{thumbnail_filename.split('.')[-1]}"
            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], thumbnail_filename))
            song.thumbnail = thumbnail_filename
            db.session.commit()

        if audio.filename != '':
            if audio.filename.split('.')[-1] not in ['mp3']:
                flash('Audio must be a mp3 file', 'info')
                return redirect(url_for('edit_song', song_id=song_id))

            if audio.content_length > MAX_FILE_SIZE:
                flash('Audio must be less than 10 MB', 'info')
                return redirect(url_for('edit_song', song_id=song_id))

            os.remove(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], song.music_src))

            audio_filename = secure_filename(audio.filename)
            audio_filename = f"{song.id}.{audio_filename.split('.')[-1]}"
            audio.save(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], audio_filename))
            song.music_src = audio_filename
            db.session.commit()

        flash('Song updated', 'info')
        return redirect(url_for('my_songs'))

    else:
        song = Song.query.filter_by(id=song_id).first()
        return render_template('edit_song.html', song=song)

@app.route('/my_songs/delete/<song_id>')
def delete_song(song_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Song.query.filter_by(id=song_id).first().artist_id:
        flash('You are not authorized to delete this song', 'info')
        return redirect(url_for('index'))

    song = Song.query.filter_by(id=song_id).first()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER_SONG_THUMBNAIL'], song.thumbnail))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], song.music_src))
    db.session.delete(song)
    db.session.commit()
    flash('Song deleted', 'info')
    return redirect(url_for('my_songs'))

@app.route('/my_albums/create', methods=['GET','POST'])
def create_album():
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    if User.query.filter_by(id=session['user_id']).first().role != 'Creator':
        flash('You must be a creator to create albums', 'info')
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            user = User.query.filter_by(id=session['user_id']).first()
            album_name = request.form.get('album_name')
            genre = request.form.get('genre')

            thumbnail = request.files['thumbnail']

            if album_name == '' or genre == '' or thumbnail.filename == '':
                flash('Please fill out all fields', 'info')
                return redirect(url_for('create_album'))

            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('upload_album'))

            if not os.path.exists(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL']):
                os.makedirs(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'])

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('upload_album'))

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

            return redirect(url_for('add_song_to_album', album_id=album_id))

        else:
            return render_template('create_album.html')

@app.route('/my_albums/create/<album_id>', methods=['GET','POST'])
def add_song_to_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))
    if User.query.filter_by(id=session['user_id']).first().role != 'Creator':
        flash('You must be a creator to add songs to albums', 'info')
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            album_songs = request.form.getlist('song')
            for song in album_songs:
                song = Song.query.filter_by(id=song).first()
                album_song = AlbumSong(album_id=album_id, song_id=song.id)
                db.session.add(album_song)
            db.session.commit()

            flash('Song added to album', 'info')
            return redirect(url_for('my_albums'))
        else:
            user = User.query.filter_by(id=session['user_id']).first()
            songs = Song.query.filter_by(artist_id=user.id).all()
            return render_template('add_song_to_album.html',album_id=album_id, songs=songs)

@app.route('/my_albums/edit/<album_id>', methods=['GET','POST'])
def edit_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to edit this album', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        album_name = request.form.get('title')
        genre = request.form.get('genre')
        thumbnail = request.files['thumbnail']

        if album_name == '' or genre == '':
            flash("Title and Genre can't be empty", 'info')
            return redirect(url_for('edit_album', album_id=album_id))

        album = Album.query.filter_by(id=album_id).first()
        album.name = album_name
        album.genre = genre
        db.session.commit()

        if thumbnail.filename != '':
            if thumbnail.filename.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                flash('Thumbnail must be a jpg, jpeg, or png file', 'info')
                return redirect(url_for('edit_album', album_id=album_id))

            if thumbnail.content_length > MAX_FILE_SIZE:
                flash('Thumbnail must be less than 10 MB', 'info')
                return redirect(url_for('edit_album', album_id=album_id))

            os.remove(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], album.thumbnail))

            thumbnail_filename = secure_filename(thumbnail.filename)
            thumbnail_filename = f"{album.id}.{thumbnail_filename.split('.')[-1]}"
            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], thumbnail_filename))
            album.thumbnail = thumbnail_filename
            db.session.commit()

        flash('Album updated', 'info')
        return redirect(url_for('my_albums'))

    else:
        album = Album.query.filter_by(id=album_id).first()
        return render_template('edit_album.html', album=album)

@app.route('/my_albums/edit/<album_id>/add_song', methods=['GET','POST'])
def edit_add_to_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to edit this album', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        album_songs = request.form.getlist('song')
        for song in album_songs:
            song = Song.query.filter_by(id=song).first()
            album_song = AlbumSong(album_id=album_id, song_id=song.id)
            db.session.add(album_song)
        db.session.commit()

        flash('Songs added to album', 'info')
        return redirect(url_for('my_albums'))

    else:
        user = User.query.filter_by(id=session['user_id']).first()
        songs = Song.query.filter_by(artist_id=user.id).all()
        song_list = []
        for song in songs:
            album_song = AlbumSong.query.filter_by(album_id=album_id, song_id=song.id).first()
            if album_song is None:
                song_list.append(song)
        return render_template('edit_add_to_album.html',album_id=album_id, songs=song_list)

@app.route('/my_albums/delete/<album_id>')
def delete_album(album_id):
    if 'user_id' not in session:
        flash('Please log in', 'info')
        return redirect(url_for('login'))

    if session['user_id'] != Album.query.filter_by(id=album_id).first().artist_id:
        flash('You are not authorized to delete this album', 'info')
        return redirect(url_for('index'))

    album = Album.query.filter_by(id=album_id).first()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER_ALBUM_THUMBNAIL'], album.thumbnail))
    album_songs = AlbumSong.query.filter_by(album_id=album_id).all()
    db.session.delete(album)
    for album_song in album_songs:
        db.session.delete(album_song)
    db.session.commit()
    flash('Album deleted', 'info')
    return redirect(url_for('my_albums'))