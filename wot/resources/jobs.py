import os
import time
import json

from flask import jsonify, request
from flask_restful import Resource, reqparse

from commons.logger import * 

class Jobs(Resource):
    def __init__(self, **kwargs):
        self.jm = kwargs['job_manager']
        super(Jobs, self).__init__()

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("Authorization", location="headers") # for security reason
            args = parser.parse_args()
            if args['Authorization'] != self.jm.credential:
                return "Unauthorized", 401
            
            job_req = request.get_json(force=True)
            
            dataset = job_req['dataset'] # e.g. MNIST, CIFAR-10, 
            model = job_req['model']  # LeNet, VGG, LSTM, ... 
            hpv = job_req['hyperparams'] # refer to data*.json for keys
            cfg = job_req['config'] # max_iter, ...
            debug("request: {}".format(job_req))
            job_id = self.jm.add(dataset, model, hpv, cfg) 

            if job_id is None:
                return "invalid job request: {}".format(job_req), 400
            else:                
                return {"job_id": job_id}, 201

        except Exception as ex:
            debug("Exception: {}".format(ex))
            return "invalid job request: {}".format(job_req), 400

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if args['Authorization'] != self.jm.credential:
            return "Unauthorized", 401
        self.jm.sync_result()
        return self.jm.get_all_jobs(n=10), 200