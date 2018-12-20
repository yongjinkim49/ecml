import os
import time
import json

from commons.logger import * 

from flask import jsonify, request
from flask_restful import Resource, reqparse

class Billboard(Resource):
    def __init__(self, **kwargs):
        self.jm = kwargs['job_manager']
        super(Billboard, self).__init__()

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if self.jm.authorize(args['Authorization']):
            return "Unauthorized", 401
        
        # TODO:to be added dynamically
        urls = [
            {"/": {"method": ['GET']}},
            {"/config": {"method": ['GET']}}, 

            {"/jobs": {"method": ['GET', 'POST']}},
            {"/jobs/active": {"method": ['GET']}},
            {"/jobs/[job_id]": {"method": ['GET', 'PUT', 'DELETE'], "job_id" : ["active"]}},

            {"/space": {"method": ['GET']}},
            {"/space/completes": {"method": ['GET']}},
            {"/space/candidates": {"method": ['GET']}},
            {"/space/grids/[id]": {"method": ['GET']}},
            {"/space/vectors/[id]": {"method": ['GET']}},
            {"/space/errors/[id]": {"method": ['GET', 'PUT']}}
        ] 
        
        return {"spec" : self.jm.get_spec(), "urls": urls }, 200 