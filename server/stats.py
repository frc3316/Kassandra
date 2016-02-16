SIZE_LIST = ['3', '2', '1']
COLOR_LIST = ['success', 'warning', 'danger']

class Granulator(object):
	def __init__(self, thershold_list, ret_list):
		self._thresholds = thershold_list
		self._rets = ret_list

	def get(self, value):
		for thresh, ret in zip(self._thresholds, self._rets):
			if value >= thresh:
				return ret
		return ret[-1]
			

class StatsManager(object):
	def __init__(self):
		self._handlers = {}
		
	def register_handler(self, handler):
		self._handlers[handler.KEY] = handler()
		return handler
	
	def run_handlers(self, match_data):
		return {handler_name: handler.filter(match_data) for handler_name, handler in self._handlers.items()}

		
statsmgr = StatsManager()


class StatsHandler(object):
	def filter(self, match_data):
		raise NotImplementedError()
		

@statsmgr.register_handler
class GoalsScored(StatsHandler):
	KEY = "shooting"
	HIGH_AMOUNT_OF_SHOTS = 20
	MED_AMOUNT_OF_SHOTS = 10
	AMOUNT_GRANULATOR = Granulator([HIGH_AMOUNT_OF_SHOTS, MED_AMOUNT_OF_SHOTS], SIZE_LIST)
	HIGH_PERCENTAGE = 0.75
	MED_PERCENTAGE = 0.25
	PERCENTAGE_GRANULATOR = Granulator([HIGH_PERCENTAGE, MED_PERCENTAGE], COLOR_LIST)
	HIGH_VARIANCE = 3

	STATS_STRUCT = dict(successful='0',
			            attempted='0',
			            size=SIZE_LIST[-1],
			            color=COLOR_LIST[-1],
			            variant=False,
			            teams=[])

	@staticmethod
	def _variance(values):
		average = sum(values) / en(values)
		return sum(map(lambda v: (v - average) ** 2, values)) / 2

	@staticmethod
	def _run_stats(success, failure):
		stats = STATS_STRUCT.copy()

		amount = len(success)
		total_scored = float(sum(success))
		total_shots = float(sum(failure) + sum(success))
		if amount == 0 or total_shots == 0:
			return stats
			
		stats['successful'] = '%.2f' % (total_scored / amount)
		stats['attempted'] = '%.2f' % (total_shots / amount)
		stats['size'] = self.AMOUNT_GRANULATOR.get(total_shots)
		stats['color'] = self.PERCENTAGE_GRANULATOR.get(total_scored / total_shots)
		stats['variant'] = self.HIGH_VARIANCE < GoalsScored._variance([float(s) / (s + f) for (s, f) in zip(success, failure)])
		
		return stats
		
	def filter(self, match_data):
		shooting_data = [match['shooting'] for match in match_data]
		
		low_far_success = [match['low']['far']['success'] for match in shooting_data]
		low_far_failure = [match['low']['far']['failure'] for match in shooting_data]
		high_far_success = [match['high']['far']['success'] for match in shooting_data]
		high_far_failure = [match['high']['far']['failure'] for match in shooting_data]
		low_close_success = [match['low']['close']['success'] for match in shooting_data]
		low_close_failure = [match['low']['close']['failure'] for match in shooting_data]
		high_close_success = [match['high']['close']['success'] for match in shooting_data]
		high_close_failure = [match['high']['close']['failure'] for match in shooting_data]
		
		return dict(low=dict(far=GoalsScored._run_stats(low_far_success, low_far_failure),
			                 close=GoalsScored._run_stats(low_close_success, low_close_failure)),
		            high=dict(far=GoalsScored._run_stats(high_far_success, high_far_failure),
		            	      close=GoalsScored._run_stats(high_close_success, high_close_failure)))
