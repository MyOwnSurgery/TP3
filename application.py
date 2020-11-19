# -*- coding: utf-8 -*-
import json
import socket
import threading

import jsonschema

import messages
import model
import view
import game_object
import client_model
from jsonschema import validate, ValidationError, SchemaError
BUFFER_SIZE = 2 ** 10

schema = {
    "type" : "object",
    "properties" : {
    "day": {"type": "integer", "minimum": 0, "maximum": 5},
    "count": {"const": 0},
    "timetable": {"type": "integer", "minimum": 0, "maximum": 30},
    "first_client": {
        "type": "object",
        "properties": {
        "name": {"type": "string"},
        "points": {"type": "integer", "minimum": 0, "maximum": 5},
        "last_message": {"const": "None" }},
        "required": ["name", "points", "last_message"]},
     "second_client": {
        "type": "object",
        "properties": {
        "name": {"type": "string"},
        "points": {"type": "integer", "minimum": 0, "maximum": 5},
        "last_message": {"const": "None" }},
        "required": ["name", "points", "last_message"]}
    },
    "required": ["day", "count","timetable","first_client","second_client"]
    }

class Application(object):

    instance = None

    def __init__(self, args):
        self.args = args
        self.closing = False
        self.host = None
        self.port = None
        self.receive_worker = None
        self.sock = None
        self.username = None
        self.ui = view.EzChatUI(self)
        self.game = game_object.Game_obj()
        Application.instance = self

    def execute(self):
        if not self.ui.show():
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except (socket.error, OverflowError):
            self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
            return
        self.receive_worker = threading.Thread(target=self.receive)
        self.receive_worker.start()
        self.ui.loop()

    def receive(self):
        while True:
            try:
                data = self.receive_all()

                if (data.find('count') == -1):
                    message = model.Message(**json.loads(data))
                else:
                    self.game = game_object.Game_obj(**json.loads(data))
                    self.game.first_client = client_model.Client(**self.game.first_client)
                    self.game.second_client = client_model.Client(**self.game.second_client)
                    continue
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
                return
            self.ui.show_message(message)

    def receive_all(self):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += self.sock.recv(1).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def send(self, event=None):
        message = self.ui.message.get()
        self.ui.wait()
        self.ui.turn_label.pack_forget()
        if len(message) == 0:
            return
        self.ui.message.set("")
        message = model.Message(username=self.username, message=message, quit=False)
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)


    def send_game(self, fname):
        with open(fname, "r") as f:
            data = f.read()
        json_data = json.loads(data)
        flag = True
        print(json_data)
        try:
            validate(json_data, schema)
        except jsonschema.exceptions.ValidationError:
            flag = False
        except jsonschema.exceptions.SchemaErrorError:
            flag = False

        if flag is True:
            self.ui.error_label.pack_forget()
            self.sock.sendall((data+model.END_CHARACTER).encode())
        else:
            self.ui.error_label.pack()


    def exit(self):
        self.closing = True
        try:
            self.sock.sendall(model.Message(username=self.username, message="", quit=True).marshal())
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print(messages.CONNECTION_ERROR)
        finally:
            self.sock.close()