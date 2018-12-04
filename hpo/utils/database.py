import json

from hpo.utils.logger import * 

JSON_DB_FILE = 'db.json'

class JsonDBManager(object):
    def __init__(self, file_name=JSON_DB_FILE):
        self.file_name = file_name
        self.database = self.load(file_name)

    def load(self, file_name):
        try:
            self.file = open(file_name)
            return json.load(self.file)
        except Exception as ex:
            warn("{} not found".format(file_name))        

    def save(self, database):
        if self.file:
            with open(self.file_name, 'w') as json_jobs:
                json.dump(self.database, json_jobs)             
        