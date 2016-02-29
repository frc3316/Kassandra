from flask import Flask, Response, request, jsonify, url_for, send_from_directory, make_response, flash, redirect
from flask.ext.login import login_required, login_user, UserMixin, LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from collections import defaultdict
from setup import *

import traceback
import zlib
import json
import sys
import os

from stats import statsmgr

is_debug_mode = ('DEBUG' in os.environ) or ('DEBUG' in sys.argv)

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = False

##############################################################################
## Database Stuff
##############################################################################
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if is_debug_mode:
    # Sqlite for debug mode
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

db = SQLAlchemy(app)

class Match(db.Model):
    """
    DB Model for match and alliances
    """
    id = db.Column(db.Integer, primary_key=True)
    match = db.Column(db.String(6), unique=True)
    red1 = db.Column(db.Integer, nullable=False)
    red2 = db.Column(db.Integer, nullable=False)
    red3 = db.Column(db.Integer, nullable=False)
    blue1 = db.Column(db.Integer, nullable=False)
    blue2 = db.Column(db.Integer, nullable=False)
    blue3 = db.Column(db.Integer, nullable=False)


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
    """
    DB Model for match defence tactic
    """
    id = db.Column(db.Integer, primary_key=True)
    defender = db.Column(db.Integer, nullable=False)
    attacker = db.Column(db.Integer, nullable=False)
    match = db.Column(db.String(6), nullable=False)
    tactic = db.Column(db.String(64), nullable=False)
    
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
    """
    DB Model for match statistics, including: breaching, scoring, collection, end game and defense.
    """
    id = db.Column(db.Integer, primary_key=True)
    match = db.Column(db.String(6), nullable=False)
    team = db.Column(db.Integer, nullable=False)

    # Breaching
    a1_success = db.Column(db.Integer, default=0)
    a1_failure = db.Column(db.Integer, default=0)
    a2_success = db.Column(db.Integer, default=0)
    a2_failure = db.Column(db.Integer, default=0)
    b1_success = db.Column(db.Integer, default=0)
    b1_failure = db.Column(db.Integer, default=0)
    b2_success = db.Column(db.Integer, default=0)
    b2_failure = db.Column(db.Integer, default=0)
    c1_success = db.Column(db.Integer, default=0)
    c1_failure = db.Column(db.Integer, default=0)
    c2_success = db.Column(db.Integer, default=0)
    c2_failure = db.Column(db.Integer, default=0)
    c1_assist_success = db.Column(db.Integer, default=0)
    c1_assist_failure = db.Column(db.Integer, default=0)
    c2_assist_success = db.Column(db.Integer, default=0)
    c2_assist_failure = db.Column(db.Integer, default=0)
    d1_success = db.Column(db.Integer, default=0)
    d1_failure = db.Column(db.Integer, default=0)
    d2_success = db.Column(db.Integer, default=0)
    d2_failure = db.Column(db.Integer, default=0)
    lb_success = db.Column(db.Integer, default=0)
    lb_failure = db.Column(db.Integer, default=0)

    # Shooting
    low_far_success = db.Column(db.Integer, default=0)
    low_far_failure = db.Column(db.Integer, default=0)
    low_close_success = db.Column(db.Integer, default=0)
    low_close_failure = db.Column(db.Integer, default=0)

    high_far_success = db.Column(db.Integer, default=0)
    high_far_failure = db.Column(db.Integer, default=0)
    high_close_success = db.Column(db.Integer, default=0)
    high_close_failure = db.Column(db.Integer, default=0)

    # Collection
    hp = db.Column(db.Integer, default=0)
    floor = db.Column(db.Integer, default=0)

    # End Game
    challenge = db.Column(db.Boolean, default=False)
    scale = db.Column(db.Boolean, default=False)

    # Defence
    if is_debug_mode:
        defences = db.Column(db.String(250))  # SQLITE doesn't support arrays
    else:
        defences = db.Column(postgresql.ARRAY(db.Integer))

    def __init__(self, match, team, breaching_dict, shooting_dict, collection_dict, end_game_dict, defences_list):
        self.match = match
        self.team = team
        
        # TODO: This doesn't verify structure. which is slightly bad.
        for key, breach_data in breaching_dict.items():
            for result in ('success', 'failure'):
                setattr(self, '%s_%s' % (key, result), int(breach_data.get(result, 0)))

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

        if is_debug_mode:
            self.defences = ",".join(map(str, defences))
        else:
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
        if self.defences:
            query = MatchDefence.query
            if is_debug_mode:
                query = query.filter(MatchDefence.id.in_(map(int, self.defences.split(","))))
            else:
                query = query.filter(MatchDefence.id.in_(self.defences))

            for defence in query.all():
                defences_list.append({'team': defence.attacker, 'tactic': defence.tactic, 'match': defence.match})

        return {'team': self.team,
                'match': self.match,
                'breaching': breaching_dict,
                'shooting': shooting_dict,
                'collection': collection_dict,
                'end_game': end_game_dict,
                'defences': defences_list}
        

    def __repr__(self):
        return '<MatchStats [Team: %d] [Match: %s]>' % (self.team, self.match)

if is_debug_mode:
    # Create all Models in memory DB for tests
    db.create_all()

##############################################################################
## User Manager stuff
##############################################################################
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'  # Be sure to change this before deplyment!
SECRET = 'password'  # Be sure to change this before deplyment!

class User(UserMixin):
    def __init__(self, id):
        self._id = id
        super(User, self).__init__()

    def get_id(self):
        return self._id

USER = User(0)  # Currently only supports a single user.

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def user_loader(user_id):
    if user_id == 0:
        return USER

##############################################################################
## DB Query Methods
##############################################################################
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


##############################################################################
## Flask Server Routes
##############################################################################
## Redirects and Directories ENDPOINTS
@app.route('/img/<path:path>')
def send_img(path):
    """ returns images from the img directory """
    return send_from_directory('img', path)


@app.route('/favicon.ico')
def get_favicon():
    """ returns redirect to favicon """
    return redirect(url_for('static', filename='favicon.ico'))


@app.route('/')
def home():
    """ returns redirect from home to stats view """
    return redirect(url_for('view_stats'))


## Get Data ENDPOINTS
@app.route('/view/team/<int:team_number>')
def view_team_stats(team_number):
    """
    static return: team match statistics viewing HTML
    fetches stats using: /stats/team/<team_number>
    """ 
    return app.send_static_file('view_match_stats.html')

@app.route('/view')
def view_stats():
    """
    static return: collected statistics viewing HTML
    fetches stats using: /stats
    """ 
    return app.send_static_file('view_stats.html')

@app.route('/matches')
def get_matches():
    """ returns the matches list with alliance info """
    try:
        return jsonify(_db_get_matchs())
    except Exception, ex:
        return jsonify(status='ERROR', msg=traceback.format_exc())

@app.route('/match/<match>')
def get_match(match):
    """ returns the single match alliance info """
    try:
        match_data = _db_get_match(match)
    except Exception, ex:
        return jsonify(status='ERROR', match=match, msg=traceback.format_exc())

    if not match_data:
        return jsonify(status='ERROR', match=match,
                       msg=("Didn't find match %s." % match))

    return jsonify(match_data)

@app.route('/stats')
def get_team_stats_list():
    """ return list of teams and matches and how much information was collected on them """
    try:
        collected_stats = _db_get_match_stats()
        match_list = _db_get_matchs()
    except Exception, ex:
        return jsonify(status='ERROR', msg=traceback.format_exc())

    # Populate base dicts
    stats_by_team = {}
    stats_by_match = {}
    for match, alliances in match_list.items():
        stats_by_match[match] = {}
        for alliance, teams in alliances.items():
            stats_by_match[match][alliance] = 0
            for team in teams:
                stats_by_team[team] = 0

    # Populate dicts with actual data
    for match_stats in collected_stats:
        team = match_stats['team']
        match = match_stats['match']
        if match not in match_list:
            continue   # Illegal match stats entry...

        if team in match_list[match]['red']:
            stats_by_match[match]['red'] += 1
        elif team in match_list[match]['blue']:
            stats_by_match[match]['blue'] += 1
        else:
            continue  # Illegal match stats entry...

        stats_by_team[team] += 1
        
    teams = sorted(stats_by_team.items())
    matches = sorted(stats_by_match.items())

    return jsonify(status='OK', teams=teams, matches=matches)

@app.route('/stats/team/<int:team_number>')
def get_team_stats(team_number):
    """ gets a team's statistics """
    try:
        matches = _db_get_match_stats(team=team_number)
    except Exception, ex:
        return jsonify(status='ERROR', msg=traceback.format_exc())

    if not matches:
        return jsonify(status='ERROR', team_number=team_number,
                       msg=("No matches for team %d." % team_number))

    try:
        stats = statsmgr.run_handlers(matches)
    except Exception, ex:
        return jsonify(status='ERROR', msg=traceback.format_exc())

    return jsonify(status='OK', team=team_number, stats=stats)


## Add Data ENDPOINTS
@app.route('/add/match', methods=['GET', 'POST'])
@login_required
def add_match():
    """ Adds match to match db """
    if request.method == 'POST':
        try:
            match = _db_add_match(request.json)
        except Exception, ex:
            return jsonify(status='ERROR', msg=traceback.format_exc())

        return jsonify(status='OK', match=match.match)
    else:
        # static return: team match add HTML
        # sends info using: /add/match
        return app.send_static_file('add_match.html')

@app.route('/add/stats', methods=['GET', 'POST'])
@login_required
def add_match_stats():
    """ handles and stores new match data """
    if request.method == 'POST':
        try:
            match_stats = _db_add_match_stats(request.json)
        except Exception, ex:
            return jsonify(status='ERROR', msg=traceback.format_exc())

        return jsonify(status='OK', match=match_stats.match, team=match_stats.team)
    else:
        # static return: team match statistics add HTML
        # sends info using: /add/stats
        return app.send_static_file('add_match_stats.html')


# Setup ENDPOINTS
@app.route('/setup/event/<event_key>')
@login_required
def setup_event(event_key):
    """ lookup event match list from TheBlueAlliance and load into DB """
    try:
        count = 0
        for match, teams_dict in fetch_tba_match_list(event_key):
            # This adds matches without overwriting them, duplicates are possible.
            match_object = Match(match=match, teams_dict=teams_dict)
            db.session.add(match_object)
            count += 1

        db.session.commit()
    except ValueError, ex:
        return jsonify(status='ERROR', msg=ex.message)
    except Exception, ex:
        return jsonify(status='ERROR', msg=traceback.format_exc())

    return jsonify(status='OK', event_key=event_key, count=count)

@app.route('/setup/export')
def setup_export():
    """ Exportes Match Statistics objects as compressed JSON """
    stats = []
    try:
        matches = _db_get_match_stats()
    except Exception, ex:
        return jsonify(status='ERROR', msg=traceback.format_exc())

    # To json and compress
    json_stats = json.dumps(matches)
    response = make_response(zlib.compress(json_stats))
    
    # Makes the browser recognize this is a download
    response.headers["Content-Disposition"] = "attachment; filename=kassandra_export.gz"
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Login page """
    if request.method == 'POST':
        if request.json.get('password', None) != SECRET:
            return jsonify(status='ERROR', msg="Bad password!") 

        login_user(USER)  # Only single user support

        return jsonify(status='OK', next='/add/stats')  # redirects to Add Match Statistics page
    else:
        # Static return: login HTML uses
        #  - /login - to send password
        return app.send_static_file('login.html')



##############################################################################
## Main
##############################################################################
if __name__ == '__main__':
    app.run(debug=is_debug_mode)
