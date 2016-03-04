import traceback
import itertools

SIZE_LIST = ['4', '5', '6']
COLOR_LIST = ['success', 'warning', 'danger']


class Granulator(object):
    def __init__(self, thershold_list, ret_list):
        self._thresholds = thershold_list
        self._rets = ret_list

    def get(self, value):
        for thresh, ret in zip(self._thresholds, self._rets):
            if value >= thresh:
                return ret
        return self._rets[-1]
            

class StatsManager(object):
    def __init__(self):
        self._handlers = {}
        
    def register_handler(self, handler):
        self._handlers[handler.KEY] = handler()
        return handler
    
    def run_handlers(self, match_data):
    	stats = {}
    	for handler_name, handler in self._handlers.items():
    		try:
    			stats[handler_name] = handler.filter(match_data)
    		except Exception, ex:
    			stats[handler_name] = {'status': 'ERROR', 'msg': traceback.format_exc()}

        return stats


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
        average = sum(values) / len(values)
        return sum(map(lambda v: (v - average) ** 2, values)) / 2

    @staticmethod
    def _run_stats(success, failure):
        stats = GoalsScored.STATS_STRUCT.copy()

        amount = len(success)
        total_scored = float(sum(success))
        total_shots = float(sum(failure) + sum(success))
        if amount == 0 or total_shots == 0:
            return stats
            
        stats['successful'] = '%.2f' % (total_scored / amount)
        stats['attempted'] = '%.2f' % (total_shots / amount)
        stats['size'] = GoalsScored.AMOUNT_GRANULATOR.get(total_shots)
        stats['color'] = GoalsScored.PERCENTAGE_GRANULATOR.get(total_scored / total_shots)
        stats['variant'] = GoalsScored.HIGH_VARIANCE < GoalsScored._variance([float(s) / (s + f) if (s + f) else 0 for (s, f) in zip(success, failure)])
        
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
@statsmgr.register_handler        
class DefencesCrossed(StatsHandler):
    KEY = "breaching"
    HIGH_AMOUNT_OF_BREACHES = 6
    MED_AMOUNT_OF_BREACHES = 3
    AMOUNT_GRANULATOR = Granulator([HIGH_AMOUNT_OF_BREACHES, MED_AMOUNT_OF_BREACHES], SIZE_LIST)
    HIGH_PERCENTAGE = 0.75
    MED_PERCENTAGE = 0.25
    PERCENTAGE_GRANULATOR = Granulator([HIGH_PERCENTAGE, MED_PERCENTAGE], COLOR_LIST)
    HIGH_VARIANCE = 1

    STATS_STRUCT = dict(successful='0',
	                    attempted='0',
	                    size=SIZE_LIST[-1],
	                    color=COLOR_LIST[-1],
	                    variant=False,
	                    teams=[])

    @staticmethod
    def _variance(values):
        average = sum(values) / len(values)
        return sum(map(lambda v: (v - average) ** 2, values)) / 2

    @staticmethod
    def _run_stats(success, failure):
        stats = DefencesCrossed.STATS_STRUCT.copy()

        amount = len(success)
        total_crossed = float(sum(success))
        total_breaches = float(sum(failure) + sum(success))
        if amount == 0 or total_breaches == 0:
            return None
            
        stats['successful'] = '%.2f' % (total_crossed/ amount)
        stats['attempted'] = '%.2f' % (total_breaches / amount)
        stats['size'] = DefencesCrossed.AMOUNT_GRANULATOR.get(total_breaches)
        stats['color'] = DefencesCrossed.PERCENTAGE_GRANULATOR.get(total_crossed / total_breaches)
        stats['variant'] = DefencesCrossed.HIGH_VARIANCE < DefencesCrossed._variance([float(s) / (s + f) if (s + f) else 0 for (s, f) in zip(success, failure)])
        
        return stats
        
    def filter(self, match_data):
        breaching_data = [match['breaching'] for match in match_data]
        DEFENCES = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'c1_assist', 'c2_assist', 'd1', 'd2', 'lb']
        NAMES = ['Portcullis', 'Cheval de Frise', 'Ramparts', 'Moat', 'Draw Bridge', 'Sally Port', 'Draw Bridge Assist', 'Sally Port Assist', 'Rock Wall', 'Rough Terrain', 'Low Bar']
        breaching_success={defence:[match[defence]['success'] for match in breaching_data] for defence in DEFENCES}
        breaching_failure={defence:[match[defence]['failure'] for match in breaching_data] for defence in DEFENCES}
        
        full_stats = []
        for defence, name in zip(DEFENCES, NAMES):
            stats = DefencesCrossed._run_stats(breaching_success[defence],
                                               breaching_failure[defence])
            if stats is None:
                continue  # Filter defences which weren't attempted

            stats['type'] = defence
            stats['name'] = name
            full_stats.append(stats)

        return sorted(full_stats, key=lambda x: x['successful'], reverse=True)


@statsmgr.register_handler
class CollectionHandler(object):
    KEY = "collection"

    HIGH_AMOUNT_OF_COLLECTIONS = 20
    MED_AMOUNT_OF_COLLECTIONS = 10
    AMOUNT_GRANULATOR = Granulator([HIGH_AMOUNT_OF_COLLECTIONS, MED_AMOUNT_OF_COLLECTIONS], SIZE_LIST)

    HIGH_AMOUNT_OF_COLLECTIONS_PER_GAME = 6
    MED_AMOUNT_OF_COLLECTIONS_PER_GAME = 3
    AMOUNT_PER_GAME_GRANULATOR = Granulator([HIGH_AMOUNT_OF_COLLECTIONS_PER_GAME,
                                             MED_AMOUNT_OF_COLLECTIONS_PER_GAME], COLOR_LIST)

    def filter(self, match_data):
        floor_data = [match['collection']['floor'] for match in match_data]
        hp_data = [match['collection']['hp'] for match in match_data]

        amount = len(match_data)
        total_floor = float(sum(floor_data))
        per_game_floor = total_floor / amount
        total_hp = float(sum(hp_data))
        per_game_hp = total_hp / amount

        stats = {'floor': {}, 'hp': {}}
        stats['floor']['color'] = self.AMOUNT_PER_GAME_GRANULATOR.get(per_game_floor)
        stats['floor']['amount'] = '%.2f' % per_game_floor
        stats['floor']['size'] = self.AMOUNT_GRANULATOR.get(total_floor)

        stats['hp']['color'] = self.AMOUNT_PER_GAME_GRANULATOR.get(per_game_hp)
        stats['hp']['amount'] = '%.2f' % per_game_hp
        stats['hp']['size'] = self.AMOUNT_GRANULATOR.get(total_hp)

        return stats


@statsmgr.register_handler
class AutonHandler(object):
    KEY = "auton"

    HIGH_AMOUNT = 4
    MED_AMOUNT = 2
    AMOUNT_GRANULATOR = Granulator([HIGH_AMOUNT, MED_AMOUNT], SIZE_LIST)

    HIGH_PERCENTAGE = 0.66
    MED_PERCENTAGE = 0.34
    PERCENTAGE_GRANULATOR = Granulator([HIGH_PERCENTAGE,
                                        MED_PERCENTAGE], COLOR_LIST)

    def filter(self, match_data):
        reach_data = [match['auton']['reach'] for match in match_data]
        cross_data = [match['auton']['cross'] for match in match_data]
        score_data = [match['auton']['score'] for match in match_data]
        
        amount = len(match_data)
        total_reach = float(sum(reach_data))
        reach_percentage = total_reach / amount
        total_cross = float(sum(cross_data))
        cross_percentage = total_cross / amount
        total_score = float(sum(score_data))
        score_percentage = total_score / amount

        stats = {'reach': {}, 'cross': {}, 'score': {}}
        stats['reach']['color'] = self.PERCENTAGE_GRANULATOR.get(reach_percentage)
        stats['reach']['percentage'] = '%.0f%%' % (reach_percentage * 100)
        stats['reach']['size'] = self.AMOUNT_GRANULATOR.get(total_reach)

        stats['cross']['color'] = self.PERCENTAGE_GRANULATOR.get(cross_percentage)
        stats['cross']['percentage'] = '%.0f%%' % (cross_percentage * 100)
        stats['cross']['size'] = self.AMOUNT_GRANULATOR.get(total_cross)

        stats['score']['color'] = self.PERCENTAGE_GRANULATOR.get(score_percentage)
        stats['score']['percentage'] = '%.0f%%' % (score_percentage * 100)
        stats['score']['size'] = self.AMOUNT_GRANULATOR.get(total_score)

        return stats


@statsmgr.register_handler
class EndGameHandler(object):
    KEY = "end_game"

    HIGH_AMOUNT = 4
    MED_AMOUNT = 2
    AMOUNT_GRANULATOR = Granulator([HIGH_AMOUNT, MED_AMOUNT], SIZE_LIST)

    HIGH_PERCENTAGE = 0.66
    MED_PERCENTAGE = 0.34
    PERCENTAGE_GRANULATOR = Granulator([HIGH_PERCENTAGE,
                                        MED_PERCENTAGE], COLOR_LIST)

    def filter(self, match_data):
        challenge_data = [match['end_game']['challenge'] for match in match_data]
        scale_data = [match['end_game']['scale'] for match in match_data]

        amount = len(match_data)
        total_challenge = float(sum(challenge_data))
        challenge_percentage = total_challenge / amount
        total_scale = float(sum(scale_data))
        scale_percentage = total_scale / amount

        stats = {'challenge': {}, 'scale': {}}
        stats['challenge']['color'] = self.PERCENTAGE_GRANULATOR.get(challenge_percentage)
        stats['challenge']['percentage'] = '%.0f%%' % (challenge_percentage * 100)
        stats['challenge']['size'] = self.AMOUNT_GRANULATOR.get(total_challenge)

        stats['scale']['color'] = self.PERCENTAGE_GRANULATOR.get(scale_percentage)
        stats['scale']['percentage'] = '%.0f%%' % (scale_percentage * 100)
        stats['scale']['size'] = self.AMOUNT_GRANULATOR.get(total_scale)

        return stats


@statsmgr.register_handler
class DefenceHandler(object):
    KEY = "defences"
    def filter(self, match_data):
        return list(itertools.chain(*[match['defences'] for match in match_data]))


@statsmgr.register_handler
class GeneralHandler(object):
    KEY = "general"
    def filter(self, match_data):
        return {'total_matches': len(match_data)}
