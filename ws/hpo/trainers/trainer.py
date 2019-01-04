from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ws.shared.logger import *

def get_simulator(space, etr):
    
    from ws.hpo.trainers.etr_emul import TrainEmulator
    from ws.hpo.trainers.grad_etr_emul import GradientETRTrainer
    from ws.hpo.trainers.median_etr_emul import VizMedianETRTrainer
    from ws.hpo.trainers.barrier_etr_emul import BarrierETRTrainer
    from ws.hpo.trainers.interval_etr_emul import IntervalETRTrainer
    from ws.hpo.trainers.hybrid_etr_emul import IntervalBarrierETRTrainer

    try:
        if not hasattr(space, 'lookup'):
            raise ValueError("Invalid surrogate space")
        lookup = space.lookup
                
        if etr == None or etr == "No":
            return TrainEmulator(lookup)
        elif etr == 'Gradient':
            return GradientETRTrainer(lookup)
        elif etr == "VizMedian":
            return VizMedianETRTrainer(lookup)                
        elif etr == "Barrier":
            return BarrierETRTrainer(lookup)
        elif etr == "Interval":
            return IntervalETRTrainer(lookup)
        elif etr == "IntervalBarrier":
            return IntervalBarrierETRTrainer(lookup)
        else:
            debug("Invalid ETR: {}".format(etr))
            return TrainEmulator(lookup)

    except Exception as ex:
        warn("Early termination trainer creation failed: {}".format(ex))
        return TrainEmulator(lookup)


def get_remote_trainer(rtc, hpvs, etr):
    from ws.hpo.trainers.grad_etr_remote import GradientETRTrainer
    from ws.hpo.trainers.etr_remote import RemoteTrainer

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

