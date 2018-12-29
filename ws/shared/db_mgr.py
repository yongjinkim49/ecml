import json

from ws.shared.logger import * 

JSON_DB_FILE = 'db.json'

def get_database_manager(db_type="JSON"):
    if db_type == "JSON":
        return JsonDBManager()
    else:
        raise NotImplementedError("No such DB type implemented: {}".format(db_type))


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
            with open(self.file_name, 'w') as json_db:
                json.dump(self.database, json_db)             

    def get_db(self):
        return self.database
    
        