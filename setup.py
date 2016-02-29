from requests import get

TBA_API_MATCHES_URL = "http://www.thebluealliance.com/api/v2/event/%s/matches"
REQUEST_HEADERS = {'X-TBA-App-Id': 'frc3316:Kassandra:v0.9'}

def fetch_tba_match_list(event_key):
	def parse_teams(teams):
		for team in teams:
			if not team.startswith('frc'):
				raise ValueError('Bad team key %s' % team)
			yield int(team[3:])

	result = get(TBA_API_MATCHES_URL % event_key, headers=REQUEST_HEADERS)
	if result.status_code != 200:
		raise ValueError('Failed fetching match from TBA')

	for match in result.json():
		if not match['key'].startswith(event_key + '_'):  # format: yyyy[EVENT_CODE]_[COMP_LEVEL]m[MATCH_NUMBER]
			raise ValueError('Bad match key %s' % match['key'])

		match_key = match['key'].split('_', 1)[1].upper()

		red1, red2, red3 = parse_teams(match['alliances']['red']['teams'])
		blue1, blue2, blue3 = parse_teams(match['alliances']['blue']['teams'])

		yield match_key, dict(red1=red1, red2=red2, red3=red3, blue1=blue1, blue2=blue2, blue3=blue3)
	