# -*- coding: utf-8 -*-
import json
import socket
import sys
import threading
import model
import random
import client_model
import messages
import game_object
import pickle


BUFFER_SIZE = 2 ** 10
CLOSING = "Application closing..."
CONNECTION_ABORTED = "Connection aborted"
CONNECTED_PATTERN = "Client connected: {}:{}"
ERROR_ARGUMENTS = "Provide port number as the first command line argument"
ERROR_OCCURRED = "Error Occurred"
EXIT = "exit"
JOIN_PATTERN = "{username} has joined"
RUNNING = "Server is running..."
SERVER = "SERVER"
SHUTDOWN_MESSAGE = "shutdown"
TYPE_EXIT = "Type 'exit' to exit>"


##Идти - 30 минут, ехать - 15
class Server(object):

    def __init__(self):
        self.clients = set()
        self.listen_thread = None
        self.port = 8081
        self.sock = None
        self.message = model.Message()
        self.message.username = "Server"
        self.game = game_object.Game_obj()


    def decide(self):
        if self.game.first_client.last_message == self.game.second_client.last_message:
            return
        if self.game.timetable == 15:
            return
        elif self.game.timetable < 15:
            if self.game.first_client.last_message == "By bus":
                self.game.first_client.points += 1
            else:
                self.game.second_client.points += 1
        else:
            if self.game.first_client.last_message == "On foot":
                self.game.first_client.points += 1
            else:
                self.game.second_client.points += 1

    def start_new(self):
        self.game.new_game()

    def finish(self):
        if self.game.first_client.points > self.game.second_client.points:
            self.message.message = self.game.first_client.name + " is a winner!"
        elif self.game.first_client.points < self.game.second_client.points:
            self.message.message = self.game.second_client.name + " is a winner!"
        else:
            self.message.message = "It`s a draw!"
        self.message.message += messages.FIRST_DAY
        self.broadcast(self.message)
        self.start_new()

    def listen(self):
        a = True
        self.sock.listen(1)
        while True:
            try:
                client, address = self.sock.accept()
            except OSError:
                print(CONNECTION_ABORTED)
                return
            print(CONNECTED_PATTERN.format(*address))
            print(self.clients)
            if len(self.clients) < 2:
                self.clients.add(client)
            if a and len(self.clients) == 2:
                self.message.message = messages.FIRST_DAY
                self.broadcast(self.message)
                a = False
            threading.Thread(target=self.handle, args=(client,)).start()

    def handle(self, client):
        while True:
            if self.game.count == 0:
                self.broadcast(self.game)
            try:
                data = self.receive(client)

                if (data.find('count')==-1):
                    message = model.Message(**json.loads(data))
                else:
                    old_name_1 = self.game.first_client.name
                    old_name_2 = self.game.first_client.name
                    self.game = game_object.Game_obj(**json.loads(data))
                    self.game.first_client = client_model.Client(**self.game.first_client)
                    self.game.second_client = client_model.Client(**self.game.second_client)
                    self.game.first_client.name = old_name_1
                    self.game.first_client.name = old_name_2
                    self.message.message = "Game has been loaded It`s day "+str(self.game.day)
                    self.broadcast(self.message)
                    continue

            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                return

            if message.quit:
                client.close()
                self.clients.remove(client)
                return

            if SHUTDOWN_MESSAGE.lower() == message.message.lower():
                self.exit()
                return
            self.check(message)
            if self.game.first_client.name == message.username:
                self.game.first_client.last_message = message.message
            else:
                self.game.second_client.last_message = message.message
            
            self.broadcast(message)


            self.game.count += 1

            if self.game.count == 2:
                self.decide()

                print(self.game.first_client.points)
                print(self.game.second_client.points)
                if self.game.day != 5:
                    self.start_new_day()
                else:
                    self.finish()

    def check(self, message):
        if self.game.first_client.name is None:
            self.game.first_client.name = message.username
        elif self.game.second_client.name is None:
            self.game.second_client.name = message.username

    def start_new_day(self):
        self.game.new_day()
        self.message.message = "Day " + str(self.game.day) + ", 9:00 AM"
        self.broadcast(self.message)


    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.marshal())



    def receive(self, client):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def run(self):
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("", self.port))
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def exit(self):
        self.sock.close()
        for client in self.clients:
            client.close()
        print(CLOSING)






if __name__ == "__main__":
    try:
        Server().run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))
