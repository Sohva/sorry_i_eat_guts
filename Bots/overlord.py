#!/usr/bin/python

from ServerMessageTypes import ServerMessageTypes
from ServerComms import ServerComms
from UsefulFunctions import *
import threading
import time
import logging


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
        self.id = 0
        self.info = {}
        self.location = (0, 0)
        self.nb_kills_to_bank = 0
        self.ammo = 0
        self.isSeeker = False
        self.hasSnitch = False
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
            if message["Name"] == self.name:
                self.id = message["Id"]
                self.location = message["X"], message["Y"]
                self.ammo = message["Ammo"]
                self.info = message
        if message["messageType"] == 24:
            self.nb_kills_to_bank += 1
        if message["messageType"] == 23:
            self.nb_kills_to_bank = 0
        if message["messageType"] == 25:
            global snitch_appeared
            snitch_appeared = True
        if (message["messageType"] == 21) and (message["Id"] == self.id):
            self.hasSnitch = True


    def run(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name': self.name, })
        while True:
            self.message = self.server.readMessage()
            # logging.info(self.message)
            self.getItems(self.message)
        return


snitch_appeared = False

if __name__ == "__main__":
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)

    nb_tanks_to_spawn = 4
    TEAM = "TeamA"
    tanks = []
    shoot_range = 50
    # Initialise tanks
    for i in range(nb_tanks_to_spawn):
        tanks.append(ThreadingTank(TEAM + ":{}".format(i)))
        tanks[i].start()

    # Smash them
    while 5 - 3 + 2 == 4:
        for tank in tanks:
            time.sleep(0.05)
            if tank.hasSnitch:
                goToGoal(tank.location[0], tank.location[1], tank.server)
                continue
            elif tank.isSeeker:
                goToSnitch(tanks, tank.server)
                continue
            if tank.nb_kills_to_bank > 0:
                print("killed someone")
                goToGoal(tank.location[0], tank.location[1], tank.server)
            else:
                print("not killed someone")
                
                if snitch_appeared:
                    print("snitch appeared")
                    if seekerExists(tanks):
                        pass
                    else:
                        tank.isSeeker = True
                else:
                    print("snitch not appeared")
                    if tank.ammo > 0:
                        print("have ammo")
                        closest_enemy = findClosestEnemy(tanks, tank.location, TEAM)
                        if not closest_enemy:
                            print("no closest enemy")
                            turnRandomly(tank.server)
                        else:
                            moveToPoint(tank.location[0],
                                        tank.location[1],
                                        closest_enemy[0],
                                        closest_enemy[1],
                                        tank.server)
                            if distanceTo(tank.location, closest_enemy) < shoot_range:
                                print("shooting now")
                                turnTurretToFaceTarget(tank.location[0],
                                                   tank.location[1],
                                                   closest_enemy[0],
                                                   closest_enemy[1],
                                                   tank.server)
                                tank.server.sendMessage(ServerMessageTypes.FIRE)
                                
#get ammo
                    else:
                        print("no ammo :(")
                        closest_ammo = findClosestAmmo(tanks, tank.location)
                        if closest_ammo:
                            print("moving to ammo")
                            moveToPoint(tank.location[0],
                                        tank.location[1],
                                        closest_ammo[0],
                                        closest_ammo[1],
                                        tank.server)
                        else:
                            print("no ammo on map :((")
                            turnRandomly(tank.server)



