import json
import copy
import six
import base64
import time

from hpo.utils.rest_client.restful_lib import Connection
from hpo.utils.logger import *
from hpo.connectors.proto import *

class RemoteJobConnector(RemoteConnectorPrototype):

    def __init__(self, url, **kwargs):
        self.wait_time = 3

        super(RemoteJobConnector, self).__init__(url, **kwargs)

    def get_profile(self):
        try:
            resp = self.conn.request_get("/", args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                profile = json.loads(resp['body'])
                return profile
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            debug("Getting profile failed: {}".format(ex))
            return None

    def get_config(self):
        try:
            resp = self.conn.request_get("/config", args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                config = json.loads(resp['body'])
                return config 
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting configuration failed: {}".format(ex))
            return None

    def get_all_jobs(self):
        resp = self.conn.request_get("/jobs", args={}, headers=self.headers)
        status = resp['headers']['status']

        if status == '200':
            jobs = json.loads(resp['body'])        
            return jobs
        else:
            raise ValueError("Connection error. worker status code: {}".format(status))   
    
    def get_job(self, job_id):
        retry_count = 0
        while True:
            resp = self.conn.request_get("/jobs/{}".format(job_id), args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                job = json.loads(resp['body'])        
                return job
            elif status == '204':
                return None # if job_id is active, no active job is available now
            elif status == '500':
                retry_count += 1
                if retry_count > self.num_retry:
                    raise ValueError("Connection error to {} job. status code: {}".format(job_id, status))
                else:
                    debug("Connection failed due to server error. retry {}/{}".format(retry_count, self.num_retry))
                    continue
            else:
                raise ValueError("Connection error to {} job. status code: {}".format(job_id, status))

    def create_job(self, job_desc):

        body = json.dumps(job_desc)
        resp = self.conn.request_post("/jobs", args={}, body=body, headers=self.headers)
        status = resp['headers']['status']
        
        if status == '201':
            js = json.loads(resp['body'])
            debug("Job {} is created remotely.".format(js['job_id']))
            return js['job_id'] 
        else:
            raise ValueError("Connection error. status code: {}".format(status))
        
        return None

    def start(self, job_id):
        retry_count = 0        
        try:
            while True:
                active_job = self.get_job("active")
                if active_job != None:
                    debug("Worker is busy. current working job: {}".format(active_job['job_id']))
                    retry_count += 1
                    if retry_count > self.num_retry:
                        warn("Starting {} job failed.".format(job_id))
                        return False
                    else:
                        time.sleep(self.wait_time)
                        debug("Retry {}/{} after waiting {}sec".format(retry_count, self.num_retry, self.wait_time))
                        continue
                else:
                    ctrl = {"control": "start"}
                    resp = self.conn.request_put("/jobs/{}".format(job_id), args=ctrl, headers=self.headers)
                    status = resp['headers']['status']
                    
                    if status == '202':
                        js = json.loads(resp['body'])
                        if 'hyperparams' in js:
                            debug("Current training item: {}".format(js['hyperparams']))
                        else:
                            debug("Current HPO item: {}".format(js))
                        return True
                    elif status == '500':
                        retry_count += 1
                        if retry_count > self.num_retry:
                            warn("Starting {} job failed.".format(job_id))
                            return False
                        else:
                            time.sleep(self.wait_time)
                            debug("Retry {}/{} after waiting {}sec".format(retry_count, self.num_retry, self.wait_time))
                            continue                        
                    else:
                        raise ValueError("Invalid worker status: {}".format(status))                
        except Exception as ex:
            warn("Starting job {} is failed".format(job_id))
            return False

    def pause(self, job_id):
        try:
            active_job = self.get_job("active")
            if active_job is None:
                warn("Job {} can not be paused.".format(active_job))
                return False 
            else:
                ctrl = {"control": "pause"}                
                resp = self.conn.request_put("/jobs/{}".format(job_id), args=ctrl, headers=self.headers)
                status = resp['headers']['status']
                
                if status == '202':
                    js = json.loads(resp['body'])
                    debug("paused job: {}".format(js))
                    return True
                else:
                    raise ValueError("Invalid worker status: {}".format(status))                
        except Exception as ex:
            warn("Pausing job {} is failed".format(job_id))
            return False

    def resume(self, job_id):
        try:
            active_job = self.get_job("active")
            if active_job is not None and active_job['job_id'] != job_id:
                warn("Job {} can not be resumed.".format(job_id))
                return False 
            else:
                ctrl = {"control": "resume"}
                resp = self.conn.request_put("/jobs/{}".format(job_id), args=ctrl, headers=self.headers)
                status = resp['headers']['status']
                
                if status == '202':
                    js = json.loads(resp['body'])
                    debug("resumed job: {}".format(js))
                    return True
                else:
                    raise ValueError("Invalid worker status: {}".format(status))                
        except Exception as ex:
            warn("Resuming job {} is failed".format(job_id))
            return False

    def stop(self, job_id):
        try:
            active_job = self.get_job("active")
            if active_job is not None and active_job['job_id'] != job_id:
                warn("Job {} can not be stopped.".format(job_id))
                return False 
            else:
                resp = self.conn.request_delete("/jobs/{}".format(job_id), args={}, headers=self.headers)
                status = resp['headers']['status']
                
                if status == '200':
                    js = json.loads(resp['body'])
                    debug("stopped job: {}".format(js))
                    return True
                else:
                    raise ValueError("Invalid worker status: {}".format(status))                
        except Exception as ex:
            warn("Stopping job {} is failed".format(job_id))
            return False        


class RemoteSampleSpaceConnector(RemoteConnectorPrototype):
    
    def __init__(self, url, **kwargs):
        
        super(RemoteSampleSpaceConnector, self).__init__(url, **kwargs)

        self.num_samples = None
        self.hp_config = None

        self.get_status()
        #self.get_candidates()
        #self.get_completes()

    def get_status(self):
        try:
            resp = self.conn.request_get("/space", args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                space = json.loads(resp['body'])
                
                self.num_samples = space['num_samples']
                self.hp_config = space["hp_config"]

                return space
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting space failed: {}".format(ex))
            return None

    def get_candidates(self):
        try:
            resp = self.conn.request_get("/space/candidates", args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                result = json.loads(resp['body'])
                
                return result["candidates"]
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting space failed: {}".format(ex))
            return None

    def get_completes(self):
        try:
            resp = self.conn.request_get("/space/completes", args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                result = json.loads(resp['body'])
                
                return result["completes"]
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting space failed: {}".format(ex))
            return None

    def validate(self, id,):
        if id == 'all':
            return True
        elif id == 'candidates':
            return True
        elif id == 'completes':
            return True
        elif id in self.get_candidates():
            return True            
        elif id in self.get_completes():
            return True
        else:
            return False

    def get_grid(self, id):
        try:
            if self.validate(id) == False:
                raise ValueError("Invalid id: {}".format(id))

            resp = self.conn.request_get("/space/grids/{}".format(id), args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                grid = json.loads(resp['body'])
                
                returns = []
                if type(grid) == list:
                    for g in grid:
                        returns.append(g['values'])
                else:
                    returns.append(grid['values'])
                #debug("grid of {}: {}".format(id, returns))
                return returns
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting grid failed: {}".format(ex))
            return None

    def get_vector(self, id):
        try:
            if self.validate(id) == False:
                raise ValueError("Invalid id: {}".format(id))

            resp = self.conn.request_get("/space/vectors/{}".format(id), args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                vec = json.loads(resp['body'])
                
                returns = []
                if type(vec) == list:
                    for v in vec:
                        returns.append(v['hparams'])
                else:
                    returns.append(vec['hparams'])
                #debug("vector of {}: {}".format(id, returns))
                return returns
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting vector failed: {}".format(ex))
            return None

    def get_error(self, id):
        try:
            if id != 'completes': 
                if not id in self.get_completes():
                    raise ValueError("Invalid id: {}".format(id))

            resp = self.conn.request_get("/space/errors/{}".format(id), args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                err = json.loads(resp['body'])
                returns = []
                if type(err) == list:
                    for e in err:
                        returns.append(e['error'])
                else:
                    returns.append(err['error'])
                #debug("error of {}: {}".format(id, returns))
                return returns
            else:
                raise ValueError("Connection failed: {}".format(status))

        except Exception as ex:
            warn("Getting error failed: {}".format(ex))
            return None

    def update_error(self, id, error):
        try:
            if self.validate(id) == False:
                raise ValueError("Invalid id: {}".format(id))
        
            args = {"error": error}
            resp = self.conn.request_put("/space/errors/{}".format(id), args=args, headers=self.headers)
            status = resp['headers']['status']
            
            if status == '202':
                err = json.loads(resp['body'])
                
                return True
            else:
                raise ValueError("Invalid worker status: {}".format(status))                
        except Exception as ex:
            warn("Updating error of {} is failed".format(id))
            return False          