#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from os import abort
import sys
from sqlalchemy import func

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
from models import *



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
	# https://stackoverflow.com/questions/63269150/typeerror-parser-must-be-a-string-or-character-stream-not-datetime
	if isinstance(value, str):
		date = dateutil.parser.parse(value)
	else:
		date = value

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
  # replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

	data = []
	cities_state_list = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
	
	for city_state_item in cities_state_list:
		venues = Venue.query.filter(Venue.state == city_state_item.state).filter(Venue.city == city_state_item.city).all()
		venue_list = []
		for venue in venues:
			venue_list.append({
				"id": venue.id,
				"name": venue.name, 
				"num_upcoming_shows": len(db.session.query(Show).filter(Show.start_time>datetime.now()).all())
			})
		data.append({
			"city": city_state_item.city,
			"state": city_state_item.state,
			"venues": venue_list
    })
	
	return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
	search_term = request.form.get('search_term', '')
	search_result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
	
	data = []
	for result in search_result:
		# upcoming shows for each venue id:
		numShows = len(db.session.query(Show).filter(Show.start_time > datetime.now()).filter(result.id == Show.venue_id).all());
		data.append({
			"id": result.id,
			"name": result.name,
			"num_upcoming_shows": numShows,
			})
	
	response={
		"count": len(search_result),
		"data": data
	}
	
	return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id

	venue = Venue.query.get(venue_id)
	
	past_shows_list = []
	past_shows = db.session.query(Show).join(Artist).filter(venue_id == Show.venue_id).filter(Show.start_time < datetime.now()).all()
	
	for show in past_shows:
		past_shows_list.append({
			"artist_id": show.artist_id,
			"artist_name": show.artist.name,
			"artist_image_link": show.artist.image_link,
			"start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
		})

	upcoming_shows_list = []
	upcoming_shows = db.session.query(Show).join(Artist).filter(venue_id == Show.venue_id).filter(Show.start_time > datetime.now()).all()
	
	for show in upcoming_shows:
		upcoming_shows_list.append({
			"artist_id": show.artist_id,
			"artist_name": show.artist.name,
			"artist_image_link": show.artist.image_link,
			"start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
		})
	
	data = {
		"id": venue.id,
		"name": venue.name,
		"genres": venue.genres,
		"address": venue.address,
		"city": venue.city,
		"state": venue.state,
		"phone": venue.phone,
		"website": venue.website,
		"facebook_link": venue.facebook_link,
		"seeking_talent": venue.seeking_talent,
		"seeking_description": venue.seeking_description,
		"image_link": venue.image_link,
		"past_shows": past_shows_list,
		"upcoming_shows": upcoming_shows_list,
		"past_shows_count": len(past_shows_list),
		"upcoming_shows_count": len(upcoming_shows_list),
	}
	
	
	return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion
  form = VenueForm(request.form)

  error = False
  try:
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website = form.website_link.data
    seeking_description = form.seeking_description.data
    genres = form.genres.data
    seeking_talent = True if form.seeking_talent.data else False
		
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
    
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')


  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
  # replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
	search_term = request.form.get('search_term', '')
	search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
	
	data = []
	for result in search_result:
		# upcoming shows for each Artist id:
		numShows = len(db.session.query(Show).filter(Show.start_time > datetime.now()).filter(result.id == Show.artist_id).all());
		data.append({
			"id": result.id,
			"name": result.name,
			"num_upcoming_shows": numShows,
			})
	
	response={
		"count": len(search_result),
		"data": data
	}
	
	return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
	artist = db.session.query(Artist).get(artist_id)
	
	
	past_shows_list = []
	past_shows = db.session.query(Show).join(Venue).filter(artist_id == Show.artist_id).filter(Show.start_time < datetime.now()).all()
	
	for show in past_shows:
		past_shows_list.append({
			"venue_id": show.venue_id,
			"venue_name": show.venue.name,
			"artist_image_link": show.artist.image_link,
			"start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
		})

	upcoming_shows_list = []
	upcoming_shows = db.session.query(Show).join(Venue).filter(artist_id == Show.artist_id).filter(Show.start_time > datetime.now()).all()
	
	for show in upcoming_shows:
		upcoming_shows_list.append({
			"venue_id": show.venue_id,
			"venue_name": show.venue_name,
			"artist_image_link": show.artist.image_link,
			"start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
		})
	
	data = {
		"id": artist.id,
		"name": artist.name,
		"genres": artist.genres,
		"city": artist.city,
		"state": artist.state,
		"phone": artist.phone,
		"website": artist.website,
		"facebook_link": artist.facebook_link,
		"seeking_venue": artist.seeking_venue,
		"seeking_description": artist.seeking_description,
		"image_link": artist.image_link,
		"past_shows": past_shows_list,
		"upcoming_shows": upcoming_shows_list,
		"past_shows_count": len(past_shows_list),
		"upcoming_shows_count": len(upcoming_shows_list),
	}
	
	return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
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
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion
	form = ArtistForm(request.form)
	
	error = False
	try:
		name = form.name.data
		city = form.city.data
		state = form.state.data
		phone = form.phone.data
		image_link = form.image_link.data
		facebook_link = form.facebook_link.data
		website = form.website_link.data
		seeking_description = form.seeking_description.data
		genres = form.genres.data
		seeking_venue = True if form.seeking_venue.data else False

		artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)
		db.session.add(artist)
		db.session.commit()
	except:
		error = True
		db.session.rollback()
		print(sys.exc_info())
	finally:
		db.session.close()
	if error:
		flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
	else:
		flash('Artist ' + request.form['name'] + ' was successfully listed!')


  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
	return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # replace with real venues data.
	data = []

	shows_join = db.session.query(Show).join(Artist).join(Venue).all()
	for show in shows_join:
		startTimeFormat = show.start_time.strftime('%Y-%m-%d %H:%M:%S')
		data.append({
			"venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": startTimeFormat
		})
	
	return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # insert form data as a new Show record in the db, instead
	form = ShowForm(request.form)
	
	error = False
	try:
		artist_id = form.artist_id.data
		venue_id = form.venue_id.data
		start_time = form.start_time.data

		show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
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

  # on successful db insert, flash success
	# flash('Show was successfully listed!')
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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

