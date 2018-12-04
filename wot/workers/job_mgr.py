import os
import time
import json

from future.utils import iteritems

from wot.utils.logger import * 
import wot.utils.lookup as lookup
from wot.utils.database import JsonDBManager 

from wot.workers.surrogate import SurrogateEvaluator


class TrainingJobFactory(object):
    def __init__(self, worker, jobs):
        self.jobs = jobs
        self.worker = worker

    def create(self, dataset, model, hpv, cfg):
        job_id = "{}_{}-{}".format(self.worker.id, self.worker.device_id, len(self.jobs))

        job = {
            "job_id" : job_id, 
            "created" : time.time(),
            "status" : "not assigned",
            "cur_loss" : None,
            "losses" : [],
            "run_time" : None,
            "times" : [],
            "cur_epoch" : 0,
            "dataset" : dataset,
            "model": model,
            "config": cfg,
            "hyperparams" : hpv
        }
        return job        

class JobManager(object):
    def __init__(self, worker, use_surrogate=False):
        self.database = self.load_db()
        self.jobs =  self.database['jobs'] #[ dummy_item, ] # XXX:change to empty list in future
        self.credential = "Basic {}".format(self.database['credential'])
         
        self.worker = worker
        self.use_surrogate = use_surrogate
        
        self.to_dos = []

    def __del__(self):
        debug("All jobs will be terminated")
        # force to terminate all jobs
        for j in self.jobs:
            j["status"] = 'terminated'

        self.save_db()

    def save_db(self):
        # XXX: disabled for testing use
        self.database['jobs'] = [] #self.jobs
        if self.dbm:
            self.dbm.save(self.database)
        else:
            warn("database can not be updated because it does not loaded yet.")

    def load_db(self):
        self.dbm = JsonDBManager()
        return self.dbm.database

    def sync_db(self):
        debug('database will be updated')
        self.save_db()

    def get_config(self):
        if self.use_surrogate:
            return {"obj_func": "surrogate", "param_order": []}
        return self.worker.config
        
    def get_spec(self):
        id = {
            "job_type": "ML trainer",
            "id": self.worker.id,
            "device_type": self.worker.device_id }
        return id

    def add(self, dataset, model, hpv, cfg):
        job_id = None
        # TODO: validate parameters
        try:
            f = TrainingJobFactory(self.worker, self.jobs)
            job = f.create(dataset, model, hpv, cfg)
            
            self.jobs.append(job)
            debug("job appended properly.")
            
            worker = None
            if self.use_surrogate and "surrogate" in cfg:
                s = cfg['surrogate']
                l = lookup.load(s)
                ffr = None
                if "ffr" in cfg:
                    ffr = cfg['ffr']
                worker = SurrogateEvaluator(s, l, time_slip_rate=ffr)
            else:
                worker = self.worker

            max_epoch = None
            if "max_epoch" in cfg:
                max_epoch = cfg['max_epoch']
                worker.set_max_iters(max_epoch)
            
            cand_index = None
            if 'cand_index' in cfg:
                cand_index = cfg['cand_index']

            if worker.set_params(hpv, cand_index):
                job['status'] = 'assigned'
                self.to_dos.append({"worker": worker, "job_id": job['job_id']})
                debug("task created properly.")
            else:
                debug("invalid hyperparam vector: {}".format(hpv))
                raise ValueError("invalid hyperparameters")
            #self.sync_db()
            job_id = job['job_id']
        except:
            #debug("invalid arguments: {}, {}, {}, {}".format(dataset, model, hpv, cfg))
            warn("invalid job description: {}".format(job))
            raise ValueError("invalid job description")
        finally:
            return job_id
    
    def get_active_job_id(self):        
        for j in self.jobs:
            if j['status'] == 'processing':
                return j['job_id']
        return None

    def get(self, job_id):
                 
        for j in self.jobs:
            if j['job_id'] == job_id:
                return j
        debug("no such {} job is existed".format(job_id))
        return None        

    def get_all_jobs(self, n=10):
        
        if len(self.jobs) <= n: 
            return self.jobs
        else:
            selected_jobs = self.jobs[-n:]
            debug("number of jobs: {}".format(len(selected_jobs)))
            return selected_jobs

    def get_to_do(self, job_id):
        for w in self.to_dos:
            if w['job_id'] == job_id:
                return w
        
        return None        

    def sync_result(self):
        for w in self.to_dos:
            id = w['job_id']
            j = self.get(id)
            if j['status'] == 'processing':
                cur_result = w['worker'].get_cur_result()
                if cur_result is not None:
                    self.update(id, **cur_result)
                cur_status = w['worker'].get_cur_status()
                if cur_status == 'idle':
                    self.update(id, status='done')
                #self.sync_db()
                break

    def update_epoch_result(self, cur_epoch, cur_loss, run_time):
        for w in self.to_dos:
            if w['worker'].get_cur_status() == 'processing':
                job_id = w['job_id']
                w['worker'].add_result(cur_epoch, cur_loss, run_time)
                debug("{} epoch result of {} is updated".format(cur_epoch, job_id))
                break

    def control(self, job_id, cmd):
        aj = self.get_active_job_id()
        if cmd == 'start':
            if aj is not None:
                debug("{} is processing now.".format(aj))
                return False
            w = self.get_to_do(job_id)
            j = self.get(job_id)
            if w is not None:
                if w['job_id'] == job_id and j['status'] != 'processing':
                    self.update(job_id, status='processing')
                    w['worker'].start()
                    return True
                else:
                    debug("{} job is already {}.".format(job_id, j['status']))
                    return False
            debug("No {} job is assigned yet.".format(job_id))
            return False
                
        if cmd == 'pause':
                if aj == job_id:
                    w = self.get_to_do(job_id)
                    w['worker'].pause()
                    self.update(job_id, status='pending')
                    
                    return True
                else:
                    debug("Unable to pause inactive job: {}".format(job_id))
                    return False
        elif cmd == 'resume':
            w = self.get_to_do(job_id)
            j = self.get(job_id)
            if w is not None and j['status'] == 'pending':
                w['worker'].resume()            
                self.update(job_id, status='processing')
                return True
            else:
                debug('Unable to resume inactive job: {}'.format(job_id))
                return False
        else:
            debug("Unsupported command: {}".format(cmd))
            return False

    def update(self, job_id, **kwargs):
        for j in self.jobs:
            if j['job_id'] == job_id:
                for (k, v) in iteritems(kwargs):
                    if k in j:
                        j[k] = v
                        #debug("{} of {} is updated: {}".format(k, job_id, v))
                        #self.sync_db()
                    else:
                        debug("{} is invalid in {}".format(k, job_id))

    def remove(self, job_id):
        for j in self.jobs:
            if j['job_id'] == job_id and j['status'] != 'terminated':
                w = self.get_to_do(job_id)
                
                if w is not None:
                    debug("{} will be stopped".format(job_id))
                    w['worker'].stop()
                    self.update(job_id, status='terminated')                
                    return True
                else:
                    debug("No such {} in TO-DO list".format(job_id))
                    return False
        warn("No jobs available.")
        return False

    def stop_working_job(self):
        for w in self.to_dos:
            if w['worker'].get_cur_status() == 'processing':
                job_id = w['job_id']
                self.remove(job_id)                
                break

           