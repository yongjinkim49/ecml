from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ws.shared.logger import *

def get_simulator(space, etr, start_up_time=None):
    
    from ws.hpo.trainers.emul.trainer import TrainEmulator
    from ws.hpo.trainers.emul.grad_etr import GradientETRTrainer
    from ws.hpo.trainers.emul.median_etr import VizMedianETRTrainer
    from ws.hpo.trainers.emul.knock_etr import KnockETRTrainer
    from ws.hpo.trainers.emul.interval_etr import IntervalETRTrainer
    from ws.hpo.trainers.emul.hybrid_etr import IntervalKnockETRTrainer
    from ws.hpo.trainers.emul.kickstart_etr import KickStarterETRTrainer

    try:
        if not hasattr(space, 'lookup'):
            raise ValueError("Invalid surrogate space")
        lookup = space.lookup
                
        if etr == None or etr == "None":
            return TrainEmulator(lookup)
        elif etr == 'Gradient':
            return GradientETRTrainer(lookup)
        elif etr == "VizMedian":
            return VizMedianETRTrainer(lookup)                
        elif etr == "Knock":
            return KnockETRTrainer(lookup)
        elif etr == "Interval":
            return IntervalETRTrainer(lookup)
        elif etr == "IntervalKnock":
            return IntervalKnockETRTrainer(lookup)            
        elif etr == "KickStarter":
            return KickStarterETRTrainer(lookup, expired_time=start_up_time)
        else:
            debug("Invalid ETR: {}".format(etr))
            return TrainEmulator(lookup)

    except Exception as ex:
        warn("Early termination trainer creation failed: {}".format(ex))
        return TrainEmulator(lookup)


def get_remote_trainer(rtc, hpvs, etr):
    from ws.hpo.trainers.remote.trainer import RemoteTrainer    
    from ws.hpo.trainers.remote.grad_etr import GradientETRTrainer

    try:
        if etr == None:
            return RemoteTrainer(rtc, hpvs)
        elif etr == 'Gradient':
            return GradientETRTrainer(rtc, hpvs)        
        else:
            debug("Invalid ETR: {}".format(etr))
            return RemoteTrainer(rtc, hpvs)

    except Exception as ex:
        warn("Remote trainer creation failed: {}".format(ex))
        raise ValueError("Invalid trainer implementation")

