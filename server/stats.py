class StatsManager(object):
	def __init__(self):
		self._handlers = {}
		
	def register_handler(self, handler):
		self._handlers[handler.__name__] = handler()
		return handler
	
	def run_handlers(self, match_data):
		return {handler_name: handler.filter(match_data) for handler_name, handler in self._handlers.items()}

		
statsmgr = StatsManager()


class StatsHandler(object):
	def filter(self, match_data):
		raise NotImplementedError()
		

@statsmgr.register_handler
class GoalsScored(StatsHandler):
	@staticmethod
	def _run_stats(success, failure):
		match_number = len(success)
		if match_number == 0:
			return dict(match_number=match_number)
			
		total_scored = float(sum(success))
		total_shots = float(sum(failure) + sum(success))
		if total_shots == 0:
			return dict(match_number=match_number,
			            total_scored=total_scored,
			            total_shots=total_shots)
			
		shooting_percentage = total_scored/total_shots
		average_scores_per_game = total_scored / match_number
		average_shots_per_game = total_shots / match_number
		
		return dict(match_number=match_number,
		            total_scored=total_scored,
					total_shots=total_shots,
					shooting_percentage=shooting_percentage,
					average_scores_per_game=average_scores_per_game,
					average_shots_per_game=average_shots_per_game)
		
	def filter(self, match_data):
		shooting_data = [match['shooting'] for match in match_data]
		
		low_far_success = [match['low']['far']['success'] for match in shooting_data]
		low_far_failure = [match['low']['far']['failure'] for match in shooting_data]
		low_far_stats = self._run_stats(low_far_success, low_far_failure)
		
		high_far_success = [match['high']['far']['success'] for match in shooting_data]
		high_far_failure = [match['high']['far']['failure'] for match in shooting_data]
		high_far_stats = self._run_stats(high_far_success, high_far_failure)
		
		far_stats = self._run_stats(map(sum, zip(low_far_success, high_far_success)),
									map(sum, zip(low_far_failure, high_far_failure)))
		
		low_close_success = [match['low']['close']['success'] for match in shooting_data]
		low_close_failure = [match['low']['close']['failure'] for match in shooting_data]
		low_close_stats = self._run_stats(low_close_success, low_close_failure)
		
		high_close_success = [match['high']['close']['success'] for match in shooting_data]
		high_close_failure = [match['high']['close']['failure'] for match in shooting_data]
		high_close_stats = self._run_stats(high_close_success, high_close_failure)
		
		close_stats = self._run_stats(map(sum, zip(low_close_success, high_close_success)),
									  map(sum, zip(low_close_failure, high_close_failure)))
		
		low_stats = self._run_stats(map(sum, zip(low_close_success, low_far_success)),
									map(sum, zip(low_close_failure, low_far_failure)))
		high_stats = self._run_stats(map(sum, zip(high_close_success, high_far_success)),
									 map(sum, zip(high_close_failure, high_far_failure)))
		
		total_stats = self._run_stats(map(sum, zip(low_close_success, low_far_success, high_close_success, high_far_success)),
									 map(sum, zip(low_close_failure, low_far_failure, high_close_failure, high_far_failure)))
		
		return dict(low_far_stats=low_far_stats,
		            high_far_stats=high_far_stats,
					low_close_stats=low_close_stats,
					high_close_stats=high_close_stats,
					far_stats=far_stats,
					close_stats=close_stats,
					low_stats=low_stats,
					high_stats=high_stats,
					total_stats=total_stats)
		
		             
		
