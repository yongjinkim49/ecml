import os
import time
import json

from flask import jsonify, request
from flask_restful import Resource, reqparse

from hpo.utils.logger import * 

class ObservedError(Resource):
    def __init__(self, **kwargs):
        self.worker = kwargs['worker']
        self.credential = kwargs['credential']
        super(ObservedError, self).__init__()

    def get(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        
        args = parser.parse_args()
        if args['Authorization'] != self.credential:
            return "Unauthorized", 401
        samples = self.worker.get_sampling_space()
        if samples == None:
            return "Sampling space is not initialized", 500

        if id == 'completes':
            errors = []
            for c_id in samples.get_completes():
                err = {"id" : c_id}
                err["error"] = samples.get_errors(int(c_id))
                errors.append(err)
            return errors, 200
        else:
            error = {"id": id}
            error["error"] = samples.get_errors(int(id))

            return error, 200 
    
    def put(self, id):
        parser = reqparse.RequestParser()        
        parser.add_argument("Authorization", location="headers") # for security reason
        parser.add_argument("value", location='args')
        args = parser.parse_args()

        if args['Authorization'] != self.credential:
            return "Unauthorized", 401

        samples = self.worker.get_sampling_space()
        if samples is None:
            return "Sampling space is not initialized", 500
        else:
            try:
                samples.update(int(id), float(args["value"]))
                error = {"id": id}
                error["error"] = samples.get_errors(int(id))
                
                return error, 202

            except Exception as ex:
                return "Invalid request:{}".format(ex), 400         

