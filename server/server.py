from flask import Flask, Response, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import glob
import json
import os

os.chdir('server')

from stats import statsmgr

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

DATABASE_DIR = "database"

## Postgress Database Stuff
def init_db():
	""" initialize database """
	pass

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match = db.Column(db.String(6), unique=True)
    red1 = db.Column(db.Integer)
    red2 = db.Column(db.Integer)
    red3 = db.Column(db.Integer)
    blue1 = db.Column(db.Integer)
    blue2 = db.Column(db.Integer)
    blue3 = db.Column(db.Integer)


    def __init__(self, match, red1, red2, red3, blue1, blue2, blue3):
        self.match=match
        self.red1=red1
        self.red2=red2
        self.red3=red3
        self.blue1=blue1
        self.blue2=blue2
        self.blue3=blue3

    def __repr__(self):
        return '<Match %r>' % self.match

def _db_add_match(match, r1, r2, r3, b1, b2, b3):
	match = Match(match, r1, r2, r3, b1, b2, b3)
	db.session.add(match)
	db.session.commit()
	return match

def store_match(match, team, match_data):
	""" Store match data into DB """
	json.dump(match_data, open(os.path.join(DATABASE_DIR, '%s_%s.json' % (match, team)), 'w'), indent=2)

def _db_get_team_data(team):
	""" Fetch team's match datas from DB """
	return [json.load(open(match_file)) for match_file in glob.glob(os.path.join(DATABASE_DIR, '*_%s.json' % team))]

def _db_get_matchs():
	""" Fetch matche list """
	matches = {}
	for m in Match.query.all():
		matches[m.match] = {'red': [m.red1, m.red2, m.red3],
		                    'blue': [m.blue1, m.blue2, m.blue3]}
	return matches

def _db_get_match(match):
	""" Fetch specific match alliances  """
	matches = {}
	for m in Match.query.filter_by(match=match):
		return {'red': [m.red1, m.red2, m.red3],
		        'blue': [m.blue1, m.blue2, m.blue3]}

## Flask Server Routes
@app.route('/add/match', methods=['GET', 'POST'])
def add_match():
	if request.method == 'POST':
		r = request.json
		_db_add_match(r['match'], int(r['red1']), int(r['red2']), int(r['red3']), 
			          int(r['blue1']), int(r['blue2']), int(r['blue3']))
		return jsonify(status='OK', match=r['match'])
	else:
		return app.send_static_file('add_match.html')

@app.route('/matches')
def get_matches():
	""" returns the matches list """
	return jsonify(_db_get_matchs())

@app.route('/match/<match>')
def get_match(match):
	""" returns the matches list """
	match = _db_get_match(match)
	if not matche:
		return jsonify(status='ERROR', match=match,
			           msg=("Didn't find match %s." % match))

	return jsonify()

@app.route('/add/stats', methods=['GET', 'POST'])
def add_match_stats():
	""" handles and stores new match data """
	if request.method == 'POST':
		match = request.json['match']
		team = request.json['team']
		store_match(match, team, request.json)
		return jsonify(status='OK', match=match, team=team)
	else:
		return app.send_static_file('add_match_stats.html')

@app.route('/stats/team/<int:team_number>')
def get_team_stats(team_number):
	""" gets a team's statistics """
	matches = _db_get_team_data(team_number)
	if not matches:
		return jsonify(status='ERROR', team_number=team_number,
			           msg=("No matches for team %d." % team_number))

	stats = statsmgr.run_handlers(matches)
	return jsonify(status='OK', team=team_number, stats=stats)

@app.route('/stats/match/<match>/<alliance>')
def get_alliance_stats(match, alliance):
	""" gets a match alliance's statistics """
	match_alliances = _db_get_match(match)
	if match_alliances is None:
		return jsonify(status='ERROR', match=match, alliance=alliance,
					   msg=("Match %r does not exist." % match))

	alliance_teams = match_alliances.get(alliance)
	if alliance_teams is None:
		return jsonify(status='ERROR', match=match, alliance=alliance,
			           msg=("Alliance %r does not exist." % alliance))
	
	matches = []
	for team_number in alliance_teams:
		matches.extend(_db_get_team_data(team_number))
	if not matches:
		return jsonify(status='ERROR', match=match, alliance=alliance,
			           msg=("No matches for teams %d, %d, %d." % tuple(alliance_teams)))

	stats = statsmgr.run_handlers(matches)
	return jsonify(status='OK', match=match, alliance=alliance, stats=stats)

	
if __name__ == '__main__':
	app.debug = True
	init_db()
	app.run()
