#!/usr/bin/python

from ServerMessageTypes import ServerMessageTypes
from ServerComms import ServerComms
from UsefulFunctions import *
import threading
import time
import logging

msTime = lambda: int(round(time.time() * 1000))

class DictOfThings(threading.Thread):

    def __init__(self, window_size=40):
        threading.Thread.__init__(self)
        self.messages = {}
        self.windowSize = window_size

    def addMessage(self, message):
        print("all the messages", self.messages)
        print("adding message", message)
        message["msTime"] = msTime()

        self.messages[message["Id"]] = message

    def deleteMessage(self, id):
        self.messages.pop(id, None)
        print("deleting message with id ", id)

    def run(self):
        while True:
            time.sleep(1)
            print("debedababidebadabo ",self.messages)
            keys = self.messages.keys().copy()
            for object_id in keys:
                if (msTime() - self.messages[object_id]["msTime"]) > 3000:
                    self.deleteMessage(object_id)




class MessageDigest:

    def __init__(self, messageType):
        self.messages = []
        self.windowSize = 40
        self.messageType = messageType

    def addMessage(self, message):

        message["msTime"] = msTime()

        if message["messagetype"] == self.messageType:
            self.messages.append(message)
            while (len(self.messages) > self.windowSize):
                self.messages.pop(0)


class ThreadingTank(threading.Thread):


    def __init__(self, name, dictOfThings, port=8052, hostname='127.0.0.1', danger_health=1,
                 zigzagging = False):

        threading.Thread.__init__(self)

        self.dictOfThings = dictOfThings

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
        self.danger_health = danger_health
        self.zigzagging = zigzagging

        logging.info("Creating tank with name '{}'".format(name))

    """
	Sends any message given to the server :)
	"""

    def messageServer(self, newMessage, params={}):
        self.server.sendMessage(newMessage, params)

    # logging.info("Attempted to " + ServerMessageTypes.toString(newMessage))

    def getItems(self, message):
        if message["messageType"] == 18: #an item in view
            self.dictOfThings.addMessage(message)
            if message["Name"] == self.name:
                self.id = message["Id"]
                self.location = message["X"], message["Y"]
                self.ammo = message["Ammo"]
                self.info = message

        if message["messageType"] == 24: #killed someone
            self.nb_kills_to_bank += 1

        if message["messageType"] == 23: #got to goal
            self.nb_kills_to_bank = 0

        if message["messageType"] == 25: #snitch appeared on pitch
            global snitch_appeared
            snitch_appeared = True

        if (message["messageType"] == 21) and (message["Id"] == self.id): #got the snitch!
            self.hasSnitch = True

        if message["messageType"] == 19: #health pack pick up
            healthPack = findClosestHealth(self)
            if healthPack:
                self.dictOfThings.deleteMessage(healthPack[2])

        if message["messageType"] == 20: #ammo pick up
            ammoPack = findClosestAmmo(self)
            if ammoPack:
                self.dictOfThings.deleteMessage(ammoPack[2])


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
    globalDictOfThings = DictOfThings()
    globalDictOfThings.start()
    for i in range(nb_tanks_to_spawn):
        tanks.append(ThreadingTank(TEAM + ":{}".format(i), globalDictOfThings))
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
                if not tank.zigzagging and -70 < tank.info['Y'] < 70 and\
                    (((60 < tank.info['Heading'] <= 90 or 300 > tank.info['Heading'] >= 270)\
                    and tank.info['X'] <= 0) or \
                    ((90 < tank.info['Heading'] < 120 or 240 < tank.info['Heading'] < 270)
                    and tank.info['X'] > 0)):
                    print("ZIGZAG\n\n\n")
                    zigzag(tank, tank.server)
            else:
                print("not killed someone")
                if snitch_appeared:
                    print("snitch appeared")
                    if seekerExists(tanks):
                        pass
                    else: #there is no seeker
                        if closestToSnitch(tanks, tank):
                            tank.isSeeker = True
                            continue
                if tank.info.get("Health", 1000) <= tank.danger_health:
                    print("low health :(")
                    closest_health = findClosestHealth(tank)
                    if closest_health:
                        print("moving to health")
                        moveToPoint(tank.location[0],
                                    tank.location[1],
                                    closest_health[0],
                                    closest_health[1],
                                    tank.server)
                    else:
                        print("no health on map :((")
                        turnRandomly(tank.server)
                else:
                    print("snitch not appeared")
                    if tank.ammo > 0:
                        print("have ammo")
                        closest_enemy = findClosestEnemy(tank, TEAM)
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
                                fire_direction = turnTurretToFaceTarget(tank.location[0],
                                                                        tank.location[1],
                                                                        closest_enemy[0],
                                                                        closest_enemy[1],
                                                                        tank.server)
                                if abs(fire_direction - tank.info['Heading']) < 2:
                                    tank.server.sendMessage(ServerMessageTypes.FIRE)
                                
#get ammo
                    else:
                        print("no ammo :(")
                        closest_ammo = findClosestAmmo(tank)
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



