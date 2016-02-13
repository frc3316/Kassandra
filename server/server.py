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

def get_team_data(team):
	""" Fetch team's match datas from DB """
	return [json.load(open(match_file)) for match_file in glob.glob(os.path.join(DATABASE_DIR, '*_%s.json' % team))]

## Flask Server Routes
@app.route('/')
def get_add_match_page():
	""" returns the match data addition page """
	return app.send_static_file('add_match.html')

@app.route('/matches')
def get_matches():
	""" returns the matches list """
	data = open('static\\matches.json').read()
	resp = Response(response=data, status=200, mimetype="application/json")
	return resp

@app.route('/addmatch', methods=['POST'])
def add_match():
	""" handles and stores new match data """
	match = request.json['match']
	team = request.json['team']
	store_match(match, team, request.json)
	return jsonify(status='OK', match=match, team=team)

@app.route('/team/<int:team_number>')
def get_team_stats(team_number):
	""" handles and stores new match data """
	matches = get_team_data(team_number)
	stats = statsmgr.run_handlers(team_number, matches)
	#resp = Response(response='test', status=200, mimetype="application/json")
	return jsonify(status='OK', team=team_number, stats=stats) #resp

	
if __name__ == '__main__':
	app.debug = True
	init_db()
	app.run()