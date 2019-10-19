#!/usr/bin/python

from ServerMessageTypes import ServerMessageTypes
from ServerComms import ServerComms
import threading
import time
import logging
from UsefulFunctions import *


class ThreadingTank(threading.Thread):

    def __init__(self, name, port=8052, hostname='127.0.0.1'):
        threading.Thread.__init__(self)
        self.ids_to_messages = {}
        self.items_to_ids = {
            "Tank": [],
            "HealthPickup": [],
            "AmmoPickup": [],
            "SnitchPickup": []
        }
        self.status = {}
        self.server = ServerComms(hostname, port)
        self.name = name
        self.nb_kills_to_bank = 0
        logging.info("Creating tank with name '{}'".format(name))

    """
    Sends any message given to the server :)
    """

    def messageServer(self, newMessage, params={}):
        self.server.sendMessage(newMessage, params)

    # logging.info("Attempted to " + ServerMessageTypes.toString(newMessage))

    def getItems(self, message):
        if "Id" in message:
            id = message["Id"]
            type = message["Type"]
            self.ids_to_messages[id] = message
            if (id not in self.items_to_ids[type]):
                self.items_to_ids[type].append(id)
        if message["messageType"] == 24:
            self.nb_kills_to_bank += 1
        if message["messageType"] == 23:
            self.nb_kills_to_bank = 0

    def run(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name': self.name, })
        while True:
            self.message = self.server.readMessage()
            # logging.info(self.message)
            self.getItems(self.message)
            print(self.items_to_ids)
        return


if __name__ == "__main__":
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)

    TEAM = "TeamA"
    tanks = []
    # Initialise tanks
    for i in range(4):
        tanks.append(ThreadingTank(TEAM + ":{}".format(i)))
        tanks[i].start()

    # Smash them
    while 5 - 3 + 2 == 4:
        for tank in tanks:

            goToGoal()









