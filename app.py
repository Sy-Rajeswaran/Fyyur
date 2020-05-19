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
from flask_wtf import Form, CsrfProtect
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database

migrate=Migrate(app,db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    facebook_link = db.Column(db.String(120))
    website=db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120), nullable=False)
    


    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    genres = db.Column(db.ARRAY(db.String()),nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue= db.Column(db.Boolean, nullable=False, default=False)
    website=db.Column(db.String(120))
    seeking_talent=db.Column(db.String(120))
    
    
    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    venue = db.relationship('Venue', backref=db.backref('shows', lazy=True))
    artist = db.relationship('Artist', backref=db.backref('shows', lazy=True))

    def __repr__(self):
      return f'<Show {self.id, self.start_time, self.artist}>'

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

def get_value(field_name):
  if field_name=='genres':
    return request.form.getlist(field_name)
  elif (field_name=='seeking_venue' or field_name=='seeking_talent') and  request.form[field_name]=='y':
    return True
  elif (field_name=='seeking_venue' or field_name=='seeking_talent') and  request.form[field_name]!='y':
    return False
  else:
    return request.form[field_name]
  

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
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venues= Venue.query.all()
  data=[]
  #creating a dictionary to sort the different venues based on city and state 
  venues_dict={}
  for venue in venues:
    key= f'{venue.city}, {venue.state}'
    venues_dict.setdefault(key,[]).append({
      'id':venue.id,
      'name':venue.name,
      'num_upcoming_shows': len(venue.shows),
      'city':venue.city,
      'state':venue.state
    })

  for val in venues_dict.values():
    data.append({
      'city':val[0]['city'],
      'state':val[0]['state'],
      'venues':val
    })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=get_value('search_term')
  venue_response=Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response={
    "count": len(venue_response),
    "data": []
  }

  for venue in venue_response:
    response["data"].append({
      'id': venue.id,
      'name':venue.name,
      'num_upcomin_shows':len(venue.shows)
    })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venues=Venue.query.get(venue_id)
  past_shows=[]
  upcoming_shows=[]
  show_attributes=None
  for show in venues.shows:
    show_attributes={
      'artist_id':show.artist.id,
      'artist_name':show.artist.name,
      'artist_image_link':show.artist.image_link,
      'start_time':show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
    }
    if show.start_time <= datetime.now():
      past_shows.append(show_attributes)
    else:
      upcoming_shows.append(show_attributes)
  
  venue_dict={
    'id':venues.id,
    'name':venues.name,
    'genres':venues.genres,
    'address':venues.address,
    'city':venues.city,
    'state':venues.state,
    'phone':venues.phone,
    'website':venues.website,
    'facebook':venues.facebook_link,
    'seeking_talent':venues.seeking_talent,
    'seeking_description':venues.seeking_description,
    'image_link':venues.image_link,
    'past_shows':past_shows,
    'upcoming_shows':upcoming_shows,
    'past_show_count':len(past_shows),
    'upcoming_show_count':len(upcoming_shows)

  }

  return render_template('pages/show_venue.html', venue=venue_dict)

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
  new_venue = Venue(
    name = get_value('name'),
    genres = get_value('genres'),
    address = get_value('address'),
    city = get_value('city'),
    state = get_value('state'),
    phone = get_value('phone'),
    website = get_value('website_link'),
    seeking_talent = get_value('seeking_talent'),
    seeking_description = get_value('seeking_description'),
    facebook_link = get_value('facebook_link'),
    image_link = get_value('image_link')
  )

  try:
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except:
    flash('An error occurred. Venue ' + new_venue.name + ' could not be listed.', category='error')
    print('exc_info()', exc_info())
    db.session.rollback()

  finally:
    db.session.close()
    return redirect(url_for('venues'))
  
  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  status=False
  try:
    venue=Venue.query.get(venue_id)
    db.session.delete(venue)
    status=True
    flash('Venue was successfully deleted')

  except:
    db.session.rollback()
    flash('Venue was not successfully deleted')
  finally:
    db.session.commit()
    return render_template('pages/home.html')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists=Artist.query.all()
  data=[]
  #creating a dictionary to store each artist in the table and to retrive them by id and name 
  artist_dict={}
  for artist in artists:
    artist_dict={
      'id': artist.id,
      'name': artist.name
    }
    data.append(artist_dict)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=get_value('search_term')
  artist_response=Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response={
    "count": len(artist_response),
    "data": []
  }

  for artist in artist_response:
    response["data"].append({
      'id': artist.id,
      'name':artist.name,
      'num_upcomin_shows':len(artist.shows)
    })

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artists=Artist.query.get(artist_id)
  past_shows=[]
  upcoming_shows=[]
  show_attributes=None
  for show in artists.shows:
    show_attributes={
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
    }
    if show.start_time <= datetime.now():
      past_shows.append(show_attributes)
    else:
      upcoming_shows.append(show_attributes)
  
  artist_dict={
    'id':artists.id,
    'name':artists.name,
    'genres':list(artists.genres),
    'city':artists.city,
    'state':artists.state,
    'phone':artists.phone,
    'website':artists.website,
    'facebook':artists.facebook_link,
    'seeking_venue':artists.seeking_venue,
    'seeking_description':artists.seeking_talent,
    'image_link':artists.image_link,
    'past_shows':past_shows,
    'upcoming_shows':upcoming_shows,
    'past_show_count':len(past_shows),
    'upcoming_show_count':len(upcoming_shows)

  }
  return render_template('pages/show_artist.html', artist=artist_dict)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=Artist.query.get(artist_id)
  # TODO: populate form with fields from artist with ID <artist_id>
  form.name.default = artist.name
  form.city.default = artist.city
  form.state.default = artist.state
  form.phone.default = artist.phone
  form.genres.default = artist.genres
  form.seeking_venue.default = artist.seeking_venue
  form.seeking_description.default = artist.seeking_talent
  form.facebook_link.default = artist.facebook_link
  form.image_link.default = artist.image_link
  form.website_link.default = artist.website
  form.process()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form= ArtistForm()
  form.validate_on_submit()
  artist=Artist.query.get(artist_id)
  try:
    artist.name=get_value('name')
    artist.genres=get_value('genres')
    artist.address=get_value('address')
    artist.city=get_value('city')
    artist.state=get_value('state')
    artist.phone=get_value('phone')
    artist.seeking_venue=get_value('seeking_venue')
    artist.seeking_talent=get_value('seeking_talent')
    artist.facebook_link=get_value('facebook_link')
    artist.image_link=get_value('image_link')
    artist.website=get_value('website')
    db.session.commit()
    flash('Artist was updated!!')
  except:
    db.session.rollback()
    flash('Artist was not updated!!')
  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue=Venue.query.get(venue_id)
  form.name.default = venue.name
  form.city.default = venue.city
  form.state.default = venue.state
  form.phone.default = venue.phone
  form.genres.default = venue.genres
  form.seeking_talent.default = venue.seeking_talent
  form.seeking_description.default = venue.seeking_description
  form.facebook_link.default = venue.facebook_link
  form.image_link.default = venue.image_link
  form.website_link.default = venue.website
  form.process()
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form= VenueForm()
  form.validate_on_submit()
  venue=Venue.query.get(venue_id)
  try:
    venue.name = get_value('name')
    venue.genres = get_value('genres')
    venue.address = get_value('address')
    venue.city = get_value('city')
    venue.state = get_value('state')
    venue.phone = get_value('phone')
    venue.website = get_value('website_link')
    venue.seeking_talent = get_value('seeking_talent')
    venue.seeking_description = get_value('seeking_description')
    venue.facebook_link = get_value('facebook_link')
    venue.image_link = get_value('image_link')

    db.session.commit()
    flash('Venue was successfully updated!!')
  except:
    db.session.rollback()
    flash('Venue was not updated!!')

  finally:
    db.session.close()
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
  new_artist=Artist(
    name=get_value('name'),
    genres=get_value('genres'),
    city=get_value('city'),
    state=get_value('state'),
    phone=get_value('phone'),
    seeking_venue=get_value('seeking_venue'),
    seeking_talent=get_value('seeking_description'),
    facebook_link=get_value('facebook_link'),
    image_link=get_value('image_link'),
    website=get_value('website_link')
  )
  try:
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except :
    db.session.rollback()
    flash('An error occurred. Artist ' + new_artist.name + ' could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/artists.html')

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #  
  #     num_shows should be aggregated based on number of upcoming shows per venue.

  shows_query = db.session.query(Show).join(Artist).join(Venue).all()

  data = []
  for show in shows_query: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
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
  # TODO: insert form data as a new Show record in the db, instead
  new_show=Show(
    venue_id=get_value('venue_id'),
    artist_id =get_value('artist_id'),
    start_time=get_value('start_time')
  )
  try:
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

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
