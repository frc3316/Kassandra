from flask import Flask, Response, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from collections import defaultdict
import traceback
import glob
import json
import sys
import os

os.chdir('server')

from stats import statsmgr

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
            setattr(self, key, int(value))

    def to_dict(self):
        return {self.match: {'red': [self.red1, self.red2, self.red3],
                             'blue': [self.blue1, self.blue2, self.blue3]}}

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

    def to_dict(self):
        return {'defender': self.defender,
                'attacker': self.attacker,
                'match': self.match,
                'tactic': self.tactic}

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
    defences = db.Column(postgresql.ARRAY(db.Integer))

    def __init__(self, match, team, breaching_dict, shooting_dict, collection_dict, end_game_dict, defences_list):
        self.match = match
        self.team = team
        
        # TODO: This doesn't verify structure. which is slightly bad.
        for key, breach_data in breaching_dict.items():
            for result, value in breach_data.items():
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
            match_defence = MatchDefence(defender=team, match=match, attacker=int(defence['team']), tactic=defence['tactic'])
            db.session.add(match_defence)
            db.session.commit()
            defences.append(match_defence.id)

        self.defences = defences

    def to_dict(self):
        breaching_dict = {}
        for key in ('a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'c1_assist', 'c2_assist', 'd1', 'd2', 'lb'):
            breaching_dict[key] = {}
            for result in ('success', 'failure'):
                breaching_dict[key][result] = getattr(self, '%s_%s' % (key, result))

        shooting_dict = {}
        for goal in ('low', 'high'):
            shooting_dict[goal] = {}
            for distance in ('far', 'close'):
                shooting_dict[goal][distance] = {}
                for result in ('success', 'failure'):
                    shooting_dict[goal][distance][result] = getattr(self, '%s_%s_%s' % (goal, distance, result))

        collection_dict = {}
        for key in ('floor', 'hp'):
            collection_dict[key] = getattr(self, key)

        end_game_dict = {}
        for key in ('challenge', 'scale'):
            end_game_dict[key] = getattr(self, key)

        defences_list = []
        for defence in MatchDefence.query.filter(MatchDefence.id.in_(self.defences)).all():
            defences_list.append({'team': defence.attacker, 'tactic': defence.tactic})

        return {'team': self.team,
                'match': self.match,
                'breaching': breaching_dict,
                'shooting': shooting_dict,
                'collection': collection_dict,
                'end_game': end_game_dict,
                'defences': defences_list}
        

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
    match = match_stats_data.pop('match')
    team = int(match_stats_data.pop('team'))
    breaching = match_stats_data.pop('breaching')
    shooting = match_stats_data.pop('shooting')
    collection = match_stats_data.pop('collection')
    end_game = match_stats_data.pop('end_game')
    defences = match_stats_data.pop('defences')
    
    match_stats_object = MatchStats(match=match, team=team, breaching_dict=breaching, shooting_dict=shooting,
                                    collection_dict=collection, end_game_dict=end_game, defences_list=defences)
    db.session.add(match_stats_object)
    db.session.commit()
    return match_stats_object

def _db_get_match_stats(team=None, match=None):
    """ Fetch team's match datas from DB """
    query = MatchStats.query
    if team is not None:
        query = query.filter(MatchStats.team == team)
    if match is not None:
        query = query.filter(MatchStats.match == match)
    return [stats.to_dict() for stats in query.all()]

def _db_get_matchs():
    """ Fetch match list """
    matches = {}
    for m in Match.query.all():
        matches.update(m.to_dict())

    return matches

def _db_get_match(match):
    """ Fetch specific match alliances  """
    matches = {}
    for m in Match.query.filter_by(match=match):
        return m.to_dict().get(match)

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

@app.route('/stats')
def get_team_stats_list():
    """ return list of teams and matches and how much information was collected on them """
    try:
        collected_stats = _db_get_match_stats()
        match_list = _db_get_matchs()
        stats_by_team = defaultdict(int)
        stats_by_match = defaultdict(lambda: {'red': 0, 'blue': 0})
        for match_stats in collection_dict:
            team = match_stats.team
            match = match_stats.match
            alliance = 'red' if team in match_list[match]['red'] else 'blue'

            stats_by_team[team] += 1
            stats_by_match[match][alliance] += 1

        teams = sorted(stats_by_team.items())
        matches = sorted(stats_by_match.items())

        return jsonify(status='OK', teams=teams, matches=matches)
    except:
        sys.stderr.write(traceback.format_exc() + "\n")

@app.route('/stats/team/<int:team_number>')
def get_team_stats(team_number):
    """ gets a team's statistics """
    try:
        matches = _db_get_match_stats(team=team_number)
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
            matches.extend(_db_get_match_stats(team=team_number))
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
