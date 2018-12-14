import os
import time
import json
import copy

from future.utils import iteritems

from hpo.utils.logger import * 
import hpo.utils.lookup as lookup
from hpo.utils.database import JsonDBManager 


class JobFactory(object):
    def __init__(self, worker, n_jobs):
        self.n_jobs = n_jobs
        self.worker = worker

    def create(self, jr):
        job = {}
        job['job_id'] = "{}_{}-{}".format(self.worker.id, self.worker.device_id, self.n_jobs)
        job['created'] = time.time()
        job['status'] = "not assigned"
        job['result'] = None
        for key in jr.keys():
            job[key] = jr[key]
        
        return job  


class JobManager(object):
    def __init__(self, worker, use_surrogate=False):
        self.database = self.load_db()
        self.jobs = [] # self.database['jobs'] # XXX:for debug only
        self.credential = "Basic {}".format(self.database['credential'])
         
        self.worker = worker
        self.prefix = worker.id
        self.device_id = worker.device_id
        
        self.use_surrogate = use_surrogate
        
        self.to_dos = []

    def __del__(self):
        debug("All jobs will be terminated")
        # force to terminate all jobs
        for j in self.jobs:
            j["status"] = 'terminated'

        self.save_db()

    def save_db(self):
        if 'jobs' in self.database: 
            self.database['jobs'] = self.jobs
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
        # This returns run config
        if self.use_surrogate:
            return {"target_func": "surrogate", "param_order": []}
        return self.worker.config 

    def get_spec(self):
        id = {
            "job_type": "HPO runner",
            "id": self.worker.id,
            "device_type": self.worker.device_id }
        return id

    def add(self, args):
        job_id = None
        # TODO: validate parameters
        try:
            f = JobFactory(self.worker, len(self.jobs))
            job = f.create(args)
            self.jobs.append(job)
            debug("Job {} added properly.".format(job['job_id']))

            if self.worker.set_params(args):
                args['status'] = 'assigned'
                self.to_dos.append({"worker": self.worker, "job_id": job['job_id']})
                debug("Job {} assigned properly.".format(job['job_id']))
            else:
                debug("invalid hyperparam vector: {}".format(args))
                raise ValueError("invalid hyperparameters")

        except:
            warn("invalid job description: {}".format(args))
            raise ValueError("invalid job description")
            #pass

        #self.sync_db()
        return job['job_id']
    
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
            if j['status'] == 'processing' or j['status'] == 'terminated':
                cur_result = w['worker'].get_cur_result()
                if cur_result is not None:
                    self.update(id, **cur_result)
                cur_status = w['worker'].get_cur_status()
                if cur_status == 'idle':
                    self.update(id, status='done')
                #self.sync_db()
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
                    # XXX:waiting required until being paused
                    while w['worker'].paused == False:
                        time.sleep(1)

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
                while w['worker'].paused == True:
                    time.sleep(1)            
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



           