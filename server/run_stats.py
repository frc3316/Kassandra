import glob
import json
import os
from flask import jsonify

from stats import statsmgr

DATABASE_DIR = "database"


def _db_get_team_data(team):
    """ Fetch team's match datas from DB """
    return [json.load(open(match_file)) for match_file in glob.glob(os.path.join(DATABASE_DIR, '*_%s.json' % team))]


def get_team_stats(team_number):
    """ gets a team's statistics """
    matches = _db_get_team_data(team_number)
    if not matches:
        return dict(status='ERROR', team_number=team_number,
                    msg=("No matches for team %d." % team_number))

    stats = statsmgr.run_handlers(matches)
    return dict(status='OK', team=team_number, stats=stats)


print (get_team_stats(15))
