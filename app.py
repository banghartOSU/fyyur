#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500), default="Add a nice description to attract artists to your venue!")

    genres = db.Column(db.String(120))
    show = db.relationship('Show', cascade='all, delete-orphan', backref='venue', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    show = db.relationship('Show', cascade='all, delete-orphan', backref='artist', lazy=True)
   
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  
  start_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  locations = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
  db.session.commit()
  for location in locations:
    newLocation = {}
    newLocation['city'] = location.city
    newLocation['state'] = location.state
    venues = Venue.query.with_entities(Venue.id, Venue.name).filter_by(city=location.city, state=location.state).all()
    venuesInCity = []
    for venue in venues:
      venueToAdd = {
        "id": venue.id,  
        "name" : venue.name,
        "num_upcoming_shows" : Show.query.filter_by(venue_id=venue.id).count()
        }
      venuesInCity.append(venueToAdd)
    newLocation['venues'] = venuesInCity
    data.append(newLocation)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  response = {}
  searchTerm = request.form['search_term']
  searchResults = Venue.query.filter(Venue.name.ilike('%' + searchTerm + '%')).distinct().all()
  response['count'] = len(searchResults)
  response['data'] = []
  for result in searchResults:
    toAdd = {}
    toAdd['id'] = result.id
    toAdd['name'] = result.name
    toAdd['num_upcoming_shows'] = Show.query.filter_by(venue_id=result.id).count()
    response['data'].append(toAdd)
 
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  print(venue)
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows" : [],
    "upcoming_shows" : [],
    "past_show_count" : 0,
    "upcoming_show_count": 0
  }
  shows = Show.query.filter_by(venue_id=venue_id)
  for show in shows:
    artist = Artist.query.get(show.artist_id)
    showToAdd = {
      "artist_id" : artist.id,
      "artist_name" : artist.name,
      "artist_image_link" : artist.image_link,
      "start_time" : str(show.start_time)
    }
    now = datetime.now()
    if show.start_time <= now:
      data['past_shows'].append(showToAdd)
    else:
      data['upcoming_shows'].append(showToAdd)
  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error=False
  try:
    print(request.form['image_link'])
    data = {
      "name":   request.form['name'],
      "city":   request.form['city'],
      "state":  request.form['state'],
      "address":request.form['address'],
      "phone":  request.form['phone'],
      "genres": ','.join(request.form.getlist('genres')),  #Use request.form.getlist for genre incase more than one selected, store as string becuase Postgres arrays are slightly annoying.
      "facebook_link": request.form['facebook_link'],
      "image_link" : request.form['image_link']
    }    
    venue = Venue(name=data['name'], city=data['city'], state=data['state'], address=data['address'], 
                    phone=data['phone'], genres=data['genres'], facebook_link=data['facebook_link'], image_link=data['image_link'])
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()   
  if error:
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = Artist.query.with_entities(Artist.id, Artist.name).order_by(Artist.name.asc()).distinct().all()
  for artist in artists:
    artistToAdd = {}
    artistToAdd['id'] = artist.id
    artistToAdd['name'] = artist.name
    data.append(artistToAdd)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  response = {}
  searchTerm = request.form['search_term']
  searchResults = Artist.query.filter(Artist.name.ilike('%' + searchTerm + '%')).distinct().all()
  response['count'] = len(searchResults)
  response['data'] = []
  for result in searchResults:
    toAdd = {}
    toAdd['id'] = result.id
    toAdd['name'] = result.name
    print(Show.query.filter_by(artist_id=result.id).count())
    toAdd['num_upcoming_shows'] = Show.query.filter_by(artist_id=result.id).count()
    response['data'].append(toAdd)
 
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "seeking_venue": artist.seeking_venue,
    "seeking_description" : artist.seeking_description,
    "facebook_link" : artist.facebook_link,
    "website" : artist.website,
    "image_link": artist.image_link,
    "past_shows": [],
    "upcoming_shows" : [],
    "past_show_count" : 0,
    "upcoming_show_count" : 0
  }
  shows = Show.query.filter_by(artist_id=artist_id)
  for show in shows:
    venue = Venue.query.get(show.venue_id)
    showToAdd = {
      "venue_id" : venue.id,
      "venue_name" : venue.name,
      "venue_image_link" : venue.image_link,
      "start_time" : str(show.start_time)
    }
    now = datetime.now()
    if show.start_time <= now:
      data['past_shows'].append(showToAdd)
    else:
      data['upcoming_shows'].append(showToAdd)
  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  result = Artist.query.get(artist_id)
  artist={
    "id": result.id,
    "name": result.name,
    "genres": result.genres.split(','),
    "city": result.city,
    "state": result.city,
    "phone": result.phone,
    "facebook_link": result.facebook_link,
    "website" : result.website,
    "seeking_venue": result.seeking_venue,
    "seeking_description": result.seeking_description,
    "image_link": result.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error=False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = ','.join(request.form.getlist('genres'))
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.image_link = request.form['image_link'],
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    error=True
    db.session.rollback
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error has occurred. Could not update Venue ' + artist_id + '.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated')
  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  result = Venue.query.get(venue_id)
  venue={
    "id": result.id,
    "name": result.name,
    "genres": result.genres.split(','),
    "address": result.address,
    "city": result.city,
    "state": result.state,
    "phone": result.phone,
    "website": result.website,
    "facebook_link": result.facebook_link,
    "seeking_talent": result.seeking_talent,
    "seeking_description": result.seeking_description,
    "image_link": result.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):  
  error=False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.website = request.form['website']
    venue.genres = ','.join(request.form.getlist('genres'))
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    error=True
    db.session.rollback
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error has occurred. Could not update Venue ' + venue_id + '.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error=False
  try:
    data = {
      "name":   request.form['name'],
      "city":   request.form['city'],
      "state":  request.form['state'],
      "phone":  request.form['phone'],
      "genres": ','.join(request.form.getlist('genres')),  #Use request.form.getlist for genre incase more than one selected
      "facebook_link": request.form['facebook_link'],
      "website" : request.form['website'],
      "image_link" : request.form['image_link']
    }    
    artist = Artist(name=data['name'], city=data['city'], state=data['state'],  
                    phone=data['phone'], genres=data['genres'], facebook_link=data['facebook_link'], image_link=data['image_link'],
                    website=data['website'])
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()   
  if error:
    flash('An error occurred. Artist ' + data.name + ' could not be added.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  error=False
  data=[]
  try:
    shows = Show.query.order_by(Show.start_time.desc()).distinct().all()
    for show in shows:
      artist = Artist.query.get(show.artist_id)
      venue = Venue.query.get(show.venue_id)
      showToAdd = {
        'venue_id' : show.venue_id,
        'venue_name':venue.name,
        'artist_id': show.artist_id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.start_time)
        }
      data.append(showToAdd)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()   
  if error:
    flash('An error occurred. Shows could not be listed.')
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error=False
  try:
    show = Show(start_time=request.form['start_time'], venue_id=request.form['venue_id'], artist_id=request.form['artist_id'])
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()   
  if error:
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show was successfully listed!')
  return render_template('pages/home.html')
 
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
