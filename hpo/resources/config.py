import os
import time
import json

from hpo.utils.logger import * 

from flask import jsonify, request
from flask_restful import Resource, reqparse

class Config(Resource):
    def __init__(self, **kwargs):
        self.jm = kwargs['job_manager']
        super(Config, self).__init__()

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if args['Authorization'] != self.jm.credential:
            return "Unauthorized", 401

        return self.jm.get_config(), 200 
