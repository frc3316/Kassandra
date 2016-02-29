# Kassandra
D-Bug 3316's Strategy Dashboard for the 2016 Stronghold Game

## Name
from https://en.wikipedia.org/wiki/Cassandra
> Cassandra (Greek: Κασσάνδρα, pronounced [kas̚sándra͜a], also Κασάνδρα), also known as Alexandra or Kassandra, was the daughter of King Priam and Queen Hecuba of Troy.

> A common version of her story is that, in an effort to seduce her, Apollo gave her the power of prophecy—but when she refused him, he spat into her mouth to inflict a curse that nobody would ever believe her prophecies.

## Usage
1. Deploy the system (see Deployment segment)
2. Login using the ```/login``` page
3. Import your event matches using ```/setup/event/[tba event code]```
4. Add match statistics using ```/add/stats```
5. Review collection progress and statistics via ```/view``` and ```/view/team/[team number]```
6. Add additional matches (Elimination) manually using ```/add/match```


## Deployment
Kassandra was designed to work over [Heroku] with gunicorn and Postgress server but will ofcourse with any Python server and DB with appropriate adjustments.

### With Heroku
1. Clone Kassandra and create your Heroku application (see Heroku tutorial)
2. Register a Postgress DB (see Heroku tutorial)
3. Modify the `SECRET_KEY` app configuration to some secret key
4. Pick a password and set in `SECRET` - this will be the login password
5. Push application to Heroku

### Custom Deployment
If you're deploying manually, here are a few pointers you should check.
* If you are using a different DB than Postgress - check [SQLAlchemy]'s support and DB Models' format is valid
* Pip install the requirements.txt
* You can run the server in debug mode by setting the `DEBUG` environment variable
* Make sure to read the 'Quick Structure Rundown' segmemnt

If you fix some bug or add any feature, you're more than welcome to fork and submit a pull request! We love our contributors

## Quick Rundown
Here's a quick explination of all the files and features of Kassandra.

### Packages Used
* [Flask] - Web Framework
* [SQLAlchemy] - Database Toolkit
* [gunicorn] - WSGI HTTP Server
* [requests] - HTTP for Humans

### Files
* `server.py` - The main server logic with all DB methods and Backend Flask Endpoints etc.
* `stats.py` - The statistics generating codes. They are pretty aweful. We're sorry.
* `setup.py` - Should have all the setup code, has only the TBA fetch code. Again, we're sorry.
* `static/` - All static HTML pages used:
  * `add_match.html` - Add a single match to the Match table
  * `add_match_stats.html` - Add scouting data for a single team in a single match to the MatchStats table
  * `login.html` - Login page
  * `view_match_stats.html` - View the statistics of collected scouting data for a specific team
  * `view_stats.html` - View all collected scouting data by match and team
* `img/` - All static images used:
  * `img/defences/` - Pictures of the defences
* `requirements.txt` - PIP requirements for this application
* `Procfile` - Used by Heroku for deployment
* `LICENSE.txt` - yes.
* `CONTRIBUTORS.txt` - They are awesome!

## Notes
We hope you find this useful either by using it or simply creating your own using this as a reference or building block.
Again, we do appologize for the god aweful code and design in some places. This was a quick "Haltora" (side-job) for all of us - and we wanted it done for Week 1.

**Cheers!**

Kassandra Dev Team<br />
D-Bug - FRC # 3316<br />
Tel-Aviv, ISRAEL

  [Heroku]: <https://heroku.com/>
  [Flask]: <http://flask.pocoo.org/>
  [SQLAlchemy]: <http://www.sqlalchemy.org/>
  [gunicorn]: <http://gunicorn.org/>
  [requests]: <http://docs.python-requests.org/en/master/>
