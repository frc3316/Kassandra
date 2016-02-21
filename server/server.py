from flask import Flask, Response, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import traceback
import glob
import json
import sys
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


    def __init__(self, match, teams_dict):
        self.match=match
        for key, value in teams_dict.items():
            setattr(self, value, int(key))

    def __repr__(self):
        return '<Match %r>' % self.match

class MatchDefence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    defender = db.Column(db.Integer)
    attacker = db.Column(db.Integer)
    match = db.Column(db.String(6))
    tactic = db.Column(db.String(64))
    
    def __init__(self, defender, attacker, match, tactic):
        self.defender = defender
        self.attacker = attacker
        self.match = match
        self.tactic = tactic

    def __repr__(self):
        return "<MatchDefence [%d on %d] [Match: %s]>" % (self.defender, self.attacker, self.match)


class MatchStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match = db.Column(db.String(6))
    team = db.Column(db.Integer)

    # Breaching
    a1_success = db.Column(db.Integer)
    a1_failure = db.Column(db.Integer)
    a2_success = db.Column(db.Integer)
    a2_failure = db.Column(db.Integer)
    b1_success = db.Column(db.Integer)
    b1_failure = db.Column(db.Integer)
    b2_success = db.Column(db.Integer)
    b2_failure = db.Column(db.Integer)
    c1_success = db.Column(db.Integer)
    c1_failure = db.Column(db.Integer)
    c2_success = db.Column(db.Integer)
    c2_failure = db.Column(db.Integer)
    c1_assist_success = db.Column(db.Integer)
    c1_assist_failure = db.Column(db.Integer)
    c2_assist_success = db.Column(db.Integer)
    c2_assist_failure = db.Column(db.Integer)
    d1_success = db.Column(db.Integer)
    d1_failure = db.Column(db.Integer)
    d2_success = db.Column(db.Integer)
    d2_failure = db.Column(db.Integer)
    lb_success = db.Column(db.Integer)
    lb_failure = db.Column(db.Integer)

    # Shooting
    low_far_success = db.Column(db.Integer)
    low_far_failure = db.Column(db.Integer)
    low_close_success = db.Column(db.Integer)
    low_close_failure = db.Column(db.Integer)

    high_far_success = db.Column(db.Integer)
    high_far_failure = db.Column(db.Integer)
    high_close_success = db.Column(db.Integer)
    high_close_failure = db.Column(db.Integer)

    # Collection
    hp = db.Column(db.Integer)
    floor = db.Column(db.Integer)

    # End Game
    challenge = db.Column(db.Boolean)
    scale = db.Column(db.Boolean)

    # Defence
    defences = db.Column(db.ARRAY(db.Integer))

    def __init__(self, match, team, breaching_dict, shooting_dict, collection_dict, end_game_dict, defences_list):
        self.match = match
        self.team = team
        
        for key, value in breaching_dict.items():
            for result, value in distance_data.items():
                setattr(self, '%s_%s' % (key, result), int(value))

        for goal, goal_data in shooting_dict.items():
            for distance, distance_data in goal_data.items():
                for result, value in distance_data.items():
                    setattr(self, '%s_%s_%s' % (goal, distance, result), int(value))

        for key, value in collection_dict.items():
            setattr(self, key, int(value))

        for key, value in end_game_dict.items():
            setattr(self, key, bool(value))

        defences = []
        for defence in defences_list:
            match_defence = MatchDefence(defender=team, match=match, attacker=defence['team'], tactic=defence['tactic'])
            db.session.add(match_defence)
            db.session.commit()
            defences.append(match_defence.id)

        self.defences = defences
        

    def __repr__(self):
        return '<MatchStats [Team: %d] [Match: %s]>' % (self.team, self.match)

def _db_add_match(match_data):
    match = match_data.pop('match')
    match_object = Match(match=match, teams_dict=match_data)
    db.session.add(match_object)
    db.session.commit()
    return match_object

def _db_add_match_stats(match_stats_data):
    """ Store match data into DB """
    match = match_data.pop('match')
    team = match_data.pop('team')
    breaching = match_data.pop('breaching')
    shooting = match_data.pop('shooting')
    collection = match_data.pop('collection')
    end_game = match_data.pop('end_game')
    defences = match_data.pop('defences')
    
    match_stats_object = MatchStats(match=match, team=team, breaching_dict=breaching, shooting_dict=shooting,
                                    collection_dict=collection, end_game_dict=end_game, defences_list=defeces)
    db.session.add(match_stats_object)
    db.session.commit()
    return match_stats_object

def _db_get_team_data(team):
    """ Fetch team's match datas from DB """
    return [json.load(open(match_file)) for match_file in glob.glob(os.path.join(DATABASE_DIR, '*_%s.json' % team))]

def _db_get_matchs():
    """ Fetch match list """
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
    try:
        if request.method == 'POST':
            match = _db_add_match(request.json)
            return jsonify(status='OK', match=match.match)
        else:
            return app.send_static_file('add_match.html')
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

@app.route('/matches')
def get_matches():
    """ returns the matches list """
    try:
        return jsonify(_db_get_matchs())
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

@app.route('/match/<match>')
def get_match(match):
    """ returns the matches list """
    try:
        match = _db_get_match(match)
        if not match:
            return jsonify(status='ERROR', match=match,
                           msg=("Didn't find match %s." % match))

        return jsonify()
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

@app.route('/add/stats', methods=['GET', 'POST'])
def add_match_stats():
    """ handles and stores new match data """
    try:
        if request.method == 'POST':
            match_stats = _db_add_match_stats(request.json)
            return jsonify(status='OK', match=match_stats.match, team=match_stats.team)
        else:
            return app.send_static_file('add_match_stats.html')
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

@app.route('/stats/team/<int:team_number>')
def get_team_stats(team_number):
    """ gets a team's statistics """
    try:
        matches = _db_get_team_data(team_number)
        if not matches:
            return jsonify(status='ERROR', team_number=team_number,
                           msg=("No matches for team %d." % team_number))

        stats = statsmgr.run_handlers(matches)
        return jsonify(status='OK', team=team_number, stats=stats)
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

@app.route('/stats/match/<match>/<alliance>')
def get_alliance_stats(match, alliance):
    """ gets a match alliance's statistics """
    try:
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
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

    
if __name__ == '__main__':
    app.debug = True
    init_db()
    app.run()
