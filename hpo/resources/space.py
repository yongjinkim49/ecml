import os
import time
import json

from commons.logger import * 

from flask import jsonify, request
from flask_restful import Resource, reqparse

class Space(Resource):
    def __init__(self, **kwargs):
        self.sm = kwargs['space_manager']
        
        super(Space, self).__init__()

    def get(self, space_id):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if not self.sm.authorize(args['Authorization']):
            return "Unauthorized", 401

        samples = self.sm.get_space(space_id)
        if samples == None:
            return "Sampling space {} is not available".format(space_id), 500

        space = {}
        if hasattr(samples, 'name'):
            space["name"] = samples.get_name()            
        space["num_samples"] = samples.num_samples
        space["hp_config"] = samples.get_hp_config().get_dict()

        return space, 200

    def put(self, space_id):
        parser = reqparse.RequestParser()        
        parser.add_argument("Authorization", location="headers") # for security reason
        parser.add_argument("status", location='args')
        args = parser.parse_args()

        if not self.sm.authorize(args['Authorization']):
            return "Unauthorized", 401

        samples = self.sm.get_space(space_id)
        if samples is None:
            return "Space {} not found".format(space_id), 404
        else:
            if "status" in args:           
                result = self.sm.set_space_status(space_id, args["status"])            
                if result is True:
                    return samples["status"], 202
                else:
                    return "Invalid request:{} of {}".format(args["status"], space_id), 400
            else:
                return "Invalid request:{} of {}".format(args, space_id), 400
    
    def delete(self, space_id):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason

        args = parser.parse_args()
        if not self.sm.authorize(args['Authorization']):
            return "Unauthorized", 401

        if self.sm.set_space_status(space_id, "finished"):
            deleted_job = { "id": space_id }
            return deleted_job, 200
        else:
            return "Job {} can not be terminated".format(space_id), 404
 