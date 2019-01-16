from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ws.shared.logger import *

def get_simulator(space, run_config):
    
    etr = None
    if run_config and "early_term_rule" in run_config:
        etr = run_config["early_term_rule"]

    expired_time = None
    if run_config and "warm_up_time" in run_config:
        expired_time = run_config["warm_up_time"]

    from ws.hpo.trainers.emul.trainer import TrainEmulator
    from ws.hpo.trainers.emul.grad_etr import GradientETRTrainer
    from ws.hpo.trainers.emul.median_etr import VizMedianETRTrainer, VizPentaETRTrainer 
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
        elif etr == "VizMedian":
            return VizMedianETRTrainer(lookup)
        elif etr == "VizPenta":
            return VizPentaETRTrainer(lookup)
        elif etr == "VizPentaOpt":
            return VizPentaETRTrainer(lookup, eval_end=0.85, percentile=80)                           
        elif etr == "Knock":
            return KnockETRTrainer(lookup)
        elif etr == "Interval":
            return IntervalETRTrainer(lookup)
        elif etr == "IntervalKnock":
            return IntervalKnockETRTrainer(lookup)            
        elif etr == "KickStarter":
            return KickStarterETRTrainer(lookup, expired_time=expired_time)
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

