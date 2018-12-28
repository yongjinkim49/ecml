import os
import time
import json
import copy

import multiprocessing as mp

from commons.logger import * 
from commons.proto import ManagerPrototype 

from resources.billboard import Billboard
from resources.config import Config
from resources.jobs import Jobs
from resources.job import Job

from resources.space import Space
from resources.candidates import Candidates
from resources.completes import Completes
from resources.grid import Grid
from resources.hparams import HyperparamVector
from resources.error import ObservedError
from resources.spaces import Spaces
from resources.space import Space 
from resources.nodes import Nodes
from resources.node import Node

from flask import Flask
from flask_restful import Api


class WebServiceManager(ManagerPrototype):

    def __init__(self, job_mgr, hp_cfg):
        super(WebServiceManager, self).__init__(type(self).__name__)
        self.app = Flask(self.type)
        self.api = Api(self.app)
        self.job_mgr = job_mgr
        
        self.hp_cfg = hp_cfg        
        self.my_process = None
        
        self.initialize()

    def get_spec(self):
        my_spec = {
            "job_type": self.type
        }
        return my_spec

    def initialize(self):
        # For profile
        self.api.add_resource(Billboard, "/", # for profile and 
                        resource_class_kwargs={'resource_manager': self})
        
        self.api.add_resource(Config, "/config", # for run spec
                        resource_class_kwargs={'job_manager': self.job_mgr, "hp_config": self.hp_cfg})
        
        # For job handling
        self.api.add_resource(Jobs, "/jobs", 
                        resource_class_kwargs={'job_manager': self.job_mgr})
        self.api.add_resource(Job, "/jobs/<string:job_id>", 
                        resource_class_kwargs={'job_manager': self.job_mgr})

        if self.job_mgr.type == "ParallelHPOManager":
            # For managing HPO nodes
            self.api.add_resource(Nodes, "/nodes", 
                            resource_class_kwargs={'node_manager': self.job_mgr})
            self.api.add_resource(Node, "/nodes/<string:node_id>", 
                            resource_class_kwargs={'node_manager': self.job_mgr})                                

            space_mgr = self.job_mgr.get_space_manager()
            # For managing sampling space and history sharing
            self.api.add_resource(Spaces, "/spaces", 
                            resource_class_kwargs={'space_manager': space_mgr})    
            self.api.add_resource(Space, "/spaces/<string:space_id>", 
                            resource_class_kwargs={'space_manager': space_mgr})
            self.api.add_resource(Grid, "/spaces/<string:space_id>/grids/<string:sample_id>", 
                            resource_class_kwargs={'space_manager': space_mgr})
            self.api.add_resource(HyperparamVector, "/spaces/<string:space_id>/vectors/<string:sample_id>", 
                            resource_class_kwargs={'space_manager': space_mgr})
            self.api.add_resource(Completes, "/spaces/<string:space_id>/completes", 
                            resource_class_kwargs={'space_manager': space_mgr})
            self.api.add_resource(Candidates, "/spaces/<string:space_id>/candidates", 
                            resource_class_kwargs={'space_manager': space_mgr})                                         
            self.api.add_resource(ObservedError, "/spaces/<string:space_id>/errors/<string:sample_id>", 
                            resource_class_kwargs={'space_manager': space_mgr})                    


    def get_urls(self):
        urls = [
            {"/": {"method": ['GET']}},
            {"/config": {"method": ['GET']}}
        ]
        
        job_urls = [
            {"/jobs": {"method": ['GET', 'POST']}},
            {"/jobs/active": {"method": ['GET']}},
            {"/jobs/[job_id]": {"method": ['GET', 'PUT', 'DELETE']}}
        ] 

        space_urls = [ 
            {"/space": {"method": ['GET']}},
            {"/space/completes": {"method": ['GET']}},
            {"/space/candidates": {"method": ['GET']}},
            {"/space/grids/[id]": {"method": ['GET']}},
            {"/space/vectors/[id]": {"method": ['GET']}},
            {"/space/errors/[id]": {"method": ['GET', 'PUT']}}
        ]

        node_urls = [
            {"/nodes": {"method": ['GET', 'POST', 'PUT', 'DELETE']}},
            {"/nodes/[node_id]": {"method": ['GET', 'PUT', 'DELETE']}}
        ] 

        if self.job_mgr.type == "TrainingJobManager" or self.job_mgr.type == "HPOJobManager":
            return urls + job_urls
        elif self.job_mgr.type == "ParallelHPOManager":
            return urls + job_urls + space_urls + node_urls
        else:
            raise ValueError("Invalid type: {}".format(self.type))


    def run_service(self, port, debug_mode=False, threaded=False, with_process=False):
        if with_process == True:
            kwargs = { 
                        'host': '0.0.0.0', 
                        'port':port, 
                        'debug' :debug_mode
                    }
                    
            self.my_process = mp.Process(target=self.app.run, kwargs=kwargs)
            self.my_process.start()
            self.my_process.join()
        else:
            if debug_mode:
                set_log_level('debug')
            self.app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=threaded) 
    
    def stop_service(self):
        if self.my_process != None:
            self.my_process.terminate()
            self.my_process.join()
            debug("API server terminated properly.")            