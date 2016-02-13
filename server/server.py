from flask import Flask, Response, request, jsonify
import glob
import json
import os

from stats import statsmgr

app = Flask(__name__)

DATABASE_DIR = "database"

## Temporary Database Mock
def init_db():
	""" initialize database """
	if not os.path.isdir(DATABASE_DIR):
		os.mkdir(DATABASE_DIR)
	
def store_match(match, team, match_data):
	""" Store match data into DB """
	json.dump(match_data, open(os.path.join(DATABASE_DIR, '%s_%s.json' % (match, team)), 'w'), indent=2)

def _db_get_team_data(team):
	""" Fetch team's match datas from DB """
	return [json.load(open(match_file)) for match_file in glob.glob(os.path.join(DATABASE_DIR, '*_%s.json' % team))]

def _db_get_match_list():
	""" Fetch matche list """
	return json.load(open(os.path.join("static", "matches.json")))

def _db_get_match(match):
	""" Fetch specific match alliances  """
	matches = _db_get_match_list()
	return matches.get(match)

## Flask Server Routes
@app.route('/')
def get_add_match_page():
	""" returns the match data addition page """
	return app.send_static_file('add_match.html')

@app.route('/matches')
def get_match_list():
	""" returns the matches list """
	return jsonify(_db_get_match_list())

@app.route('/addmatch', methods=['POST'])
def add_match_stats():
	""" handles and stores new match data """
	match = request.json['match']
	team = request.json['team']
	store_match(match, team, request.json)
	return jsonify(status='OK', match=match, team=team)

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