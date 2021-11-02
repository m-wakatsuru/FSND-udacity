#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import *
from model import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  venues = Venue.query.order_by(Venue.state, Venue.city).all()
  data = []
  tmp={}
  prev_city = None
  prev_state = None
  for venue in venues:
    venue_data = {
      'id': venue.id,
      'name': venue.name,
    }
    if venue.city == prev_city and venue.state == prev_state:
      tmp['venues'].append(venue_data)
    else:
      if prev_city is not None:
        data.append(tmp)
      tmp = {}
      tmp['city'] = venue.city
      tmp['state'] = venue.state
      tmp['venues'] = [venue_data]
    prev_city = venue.city
    prev_state = venue.state

  data.append(tmp)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_str = request.form.get('search_term')
  venue_query = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_str)))
  print(venue_query.count()) 
  response = {
	  "count":venue_query.count(),
	  "data":[]
    }
  
  for venue in venue_query:
    temp = {
      "id": venue.id,
      "name": venue.name
    }
    response['data'].append(temp)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try:
    data = Venue.query.get(venue_id)
    q = db.session.query(Show).join(Show.artist).filter(Show.venue_id == venue_id).all()
    shows_before = []
    shows_after = []
    past_shows_count = 0
    upcoming_shows_count = 0

    for show in q:
      temp = {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
      }
      if show.start_time <= datetime.now():
        shows_before.append(temp)
        past_shows_count += 1
      else:
        shows_after.append(temp)
        upcoming_shows_count += 1
    data.past_shows = shows_before
    data.upcoming_shows = shows_after
    data.past_shows_count = past_shows_count
    data.upcoming_shows_count = upcoming_shows_count

    temp = data.genres
    temp = temp.replace('{','').replace('}','')
    temp = temp.split(',')
    data.genres = temp

  except Exception as e:
    print(e)
    pass
  
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    if request.form.get('seeking_talent') == 'y':
      seeking_val = True
    else:
      seeking_val = False

    venue = Venue(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres=request.form.getlist('genres'),
      website_link = request.form['website_link'],
      seeking_talent = seeking_val,
      seeking_description = request.form['seeking_description']
    )

    db.session.add(venue)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
    pass
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
    flash('Venue was successfully deleted!')    
  return None
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  return render_template('pages/artists.html', artists=Artist.query.order_by(Artist.id).all()
)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_str = request.form.get('search_term')
  artist_query = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_str)))
  response = {
	  "count":artist_query.count(),
	  "data":[]
    }
  
  for artist in artist_query:
    temp = {
      "id": artist.id,
      "name": artist.name
    }
    response['data'].append(temp)
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  try:
    data = Artist.query.get(artist_id)
    q = db.session.query(Show).join(Show.venue).filter(Show.artist_id == artist_id).all()
    shows_before = []
    shows_after = []
    past_shows_count = 0
    upcoming_shows_count = 0

    for show in q:
      temp = {
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
      }
      if show.start_time <= datetime.now():
        shows_before.append(temp)
        past_shows_count += 1
      else:
        shows_after.append(temp)
        upcoming_shows_count += 1
    data.past_shows = shows_before
    data.upcoming_shows = shows_after
    data.past_shows_count = past_shows_count
    data.upcoming_shows_count = upcoming_shows_count

    temp = data.genres
    temp = temp.replace('{','').replace('}','')
    temp = temp.split(',')
    data.genres = temp

  except Exception as e:
    print(e)
    pass
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  try:
    if request.form.get('seeking_venue') == 'y':
      seeking_val = True
    else:
      seeking_val = False
    
    print(request.form['genres'])


    artist = Artist.query.get(artist_id)

    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres=request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = seeking_val
    artist.seeking_description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()

  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    print()
  finally:
    db.session.close()
  if error:
    abort (400)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return render_template('pages/home.html')


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.genres.data = venue.genres
  form.website_link.data = venue.website_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  try:
    if request.form.get('seeking_talent') == 'y':
      seeking_val = True
    else:
      seeking_val = False
    
    venue = Venue.query.get(venue_id)

    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')
    venue.website_link = request.form['website_link']
    venue.seeking_talent = seeking_val
    venue.seeking_description = request.form['seeking_description']

    db.session.add(venue)
    db.session.commit()

  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  if error:
    abort (400)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    if request.form.get('seeking_venue') == 'y':
      seeking_val = True
    else:
      seeking_val = False

    artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      genres = request.form.getlist('genres'),
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_venue = seeking_val,
      seeking_description = request.form['seeking_description']
    )

    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    pass
  finally:
    db.session.close()
  if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.(DONE)
  data = []
  try:
    all_shows = db.session.query(Show).all()
    for show in all_shows:
      artist = Artist.query.filter_by(id=show.artist_id).first()
      venue = Venue.query.filter_by(id=show.venue_id).first()
      data.append({
          "venue_id": show.venue_id,
          "venue_name": venue.name,
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
      })
  except Exception as e:
    print(e)
    pass
  return render_template("pages/shows.html", shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:

    show = Show(
        venue_id = request.form['venue_id'],
        artist_id = request.form['artist_id'],
        start_time = request.form['start_time']
      )

    db.session.add(show)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show ' + request.form['start_time'] + ' could not be listed.')
  else:
    flash('Show ' + request.form['start_time'] + ' was successfully listed!')
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
