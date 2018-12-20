import os
import time
import json

from commons.loggerr import * 

from flask import jsonify, request
from flask_restful import Resource, reqparse

class HyperparamVector(Resource):
    def __init__(self, **kwargs):
        self.worker = kwargs['worker']
        self.credential = kwargs['credential']
        super(HyperparamVector, self).__init__()

    def get(self, id):
        
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        
        if args['Authorization'] != self.credential:
            return "Unauthorized", 401

        samples = self.worker.get_sampling_space()
        if samples == None:
            return "Sampling space is not initialized", 500

        if id == 'all':
            all_items =[]
            for c_id in range(samples.num_samples):
                grid = {"id": c_id}
                grid["hparams"] = samples.get_hpv(int(c_id))
                all_items.append(grid)
            
            return all_items, 200                
        
        elif id == 'candidates':
            candidates = []
            for c_id in samples.get_candidates():
                hpv = {"id": c_id}
                hpv["hparams"] = samples.get_hpv(int(c_id))
                candidates.append(hpv)
            
            return candidates, 200

        elif id == 'completes':
            completes = []
            for c_id in samples.get_completes():
                hpv = {"id": c_id}
                hpv["hparams"] = samples.get_hpv(int(c_id))
                completes.append(hpv)
            
            return completes, 200
        else:
            try:
                hpv = {"id": id}
                hpv["hparams"] = samples.get_hpv(int(id))
                return hpv, 200

            except Exception as ex:
                return "Getting grid failed: {}".format(ex), 404
