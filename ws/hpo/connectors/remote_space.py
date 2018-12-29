import json
import copy
import six
import base64
import time

from ws.rest_client.restful_lib import Connection
from ws.shared.logger import *
from ws.shared.proto import *


def connect_remote_space(space_url, cred):
    try:
        name = "grid-{}".format(space_url)
        connector = RemoteSampleSpaceConnector(space_url, credential=cred)
        return RemoteSamplingSpace(name, connector)
    except Exception as ex:
        warn("Fail to get remote samples: {}".format(ex))
        return None  


class RemoteSampleSpaceConnector(RemoteConnectorPrototype):
    
    def __init__(self, url, credential, **kwargs):
        
        super(RemoteSampleSpaceConnector, self).__init__(url, credential, **kwargs)

        self.num_samples = None
        self.hp_config = None
        
        self.get_status()

    def get_status(self):
        try:
            resp = self.conn.request_get("", args={}, headers=self.headers)
            status = resp['headers']['status']

            if status == '200':
                space = json.loads(resp['body'])
                
                self.num_samples = space['num_samples']
                self.hp_config = space["hp_config"]

                return space
            else:
                raise ValueError("Connection failed with code {}".format(status))

        except Exception as ex:
            debug("Getting remote space: {}".format(ex))
            return None

    def get_num_samples(self):
        if self.num_samples != None:
            return self.num_samples
        else:
            raise ValueError("Handshaking failed!")

    def get_candidates(self):
        resp = self.conn.request_get("/candidates", args={}, headers=self.headers)
        status = resp['headers']['status']

        if status == '200':
            result = json.loads(resp['body'])
            
            return result["candidates"]
        else:
            raise ValueError("Connection failed: {}".format(status))

    def get_completes(self):
        resp = self.conn.request_get("/completes", args={}, headers=self.headers)
        status = resp['headers']['status']

        if status == '200':
            result = json.loads(resp['body'])
            
            return result["completes"]
        else:
            raise ValueError("Connection failed: {}".format(status))

    def validate(self, id):
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

        if self.validate(id) == False:
            raise ValueError("Invalid id: {}".format(id))

        resp = self.conn.request_get("/grids/{}".format(id), args={}, headers=self.headers)
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


    def get_vector(self, id):
        if self.validate(id) == False:
            raise ValueError("Invalid id: {}".format(id))

        resp = self.conn.request_get("/vectors/{}".format(id), args={}, headers=self.headers)
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

    def get_error(self, id):
        if id != 'completes': 
            if not id in self.get_completes():
                raise ValueError("Invalid id: {}".format(id))

        resp = self.conn.request_get("/errors/{}".format(id), args={}, headers=self.headers)
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

    def update_error(self, id, error):

        if self.validate(id) == False:
            raise ValueError("Invalid id: {}".format(id))
    
        args = {"value": error}
        resp = self.conn.request_put("/errors/{}".format(id), args=args, headers=self.headers)
        status = resp['headers']['status']
        
        if status == '202':
            err = json.loads(resp['body'])
            
            return True
        else:
            raise ValueError("Invalid worker status: {}".format(status))                
     