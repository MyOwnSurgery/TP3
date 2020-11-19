import client_model
import random

import json
END_CHARACTER = "\0"

TARGET_ENCODING = "utf-8"
class Game_obj(object):

    def __init__(self, **kwargs):
        self.day = 1
        self.count = 0
        self.timetable = self.rand()
        self.first_client = client_model.Client()
        self.second_client = client_model.Client()
        self.__dict__.update(kwargs)

    def new_game(self):
        self.first_client = client_model.Client()
        self.second_client = client_model.Client()
        self.day = 1
        self.count = 0
        self.timetable = self.rand()

    def new_day(self):
        self.first_client.last_message = None
        self.second_client.last_message = None
        self.count = 0
        self.day += 1
        self.timetable = self.rand()

    def rand(self):
        return random.randint(0, 30)

    def marshal(self):
        return (str(self.__dict__).replace("'", '"') + END_CHARACTER).encode(TARGET_ENCODING)



