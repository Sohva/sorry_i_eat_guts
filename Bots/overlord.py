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
		self.items_to_ids =
		{
                "Tank":[], 
		"HealthPickup": [], 
		"AmmoPickup": [],
		"SnitchPickup": []
                }
		self.status = {}
		self.server = ServerComms(hostname, port)
		self.name = name
		self.id = 0
		self.location = (0, 0)
		self.nb_kills_to_bank = 0
		logging.info("Creating tank with name '{}'".format(name))
	
	
	
	"""
	Sends any message given to the server :)
	"""
	def messageServer(self, newMessage, params = {}):
		self.server.sendMessage(newMessage, params )
		#logging.info("Attempted to " + ServerMessageTypes.toString(newMessage))
	
	def getItems(self, message):
		if "Id" in message:
                        id = message["Id"]
                        type = message["Type"]
                        self.ids_to_messages[id] = message
                        if (id not in self.items_to_ids[type]):
                                self.items_to_ids[type].append(id)
                        if message["name"] == self.name:
                                self.id = message["Id"]
                                self.location = message["X"], message["Y"]
                if message["messageType"] == 24:
                        self.nb_kills_to_bank += 1
                if message["messageType"] == 23:
                        self.nb_kills_to_bank = 0
			
	def run(self):
		self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name': self.name, })
		while True:
			self.message = self.server.readMessage()
			#logging.info(self.message)
			self.getItems(self.message)
			print(self.items_to_ids)
		return
        
def distance2(loc1, loc2):
        return ((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)**(0.5)
	
if __name__ == "__main__":
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)	
	
	TEAM = "TeamA"
	tanks = []
	shoot_range = 50
	# Initialise tanks
	for i in range(4):
		tanks.append(ThreadingTank(TEAM+":{}".format(i)))
		tanks[i].start()
		
        # Smash them
        while 5-3+2==4:
                for tank in tanks:
                        if tank.nb_kills_to_bank > 0:
                                goToGoal(*tank.location, tank.server)
                        else:
                                # TODO(is there snitch?)
                                if False:
                                        pass
                                else:
                                        # TODO(do we have ammo)
                                        if True:
                                                closest_enemy = FindClosestEnemy(tank.location)
                                                if distance2(tank.location, closest_enemy) < shoot_range:
                                                        turnTurretToFaceTarget(tank.location[0],
                                                                               tank.location[1],
                                                                               closest_enemy[0],
                                                                               closest_enemy[1],
                                                                               tank.server)
                                                        tank.server.sendMessage(ServerMessageTypes.FIRE)
                                                else:
                                                        moveToPoint(tank.location[0],
                                                                    tank.location[1],
                                                                    closest_enemy[0],
                                                                    closest_enemy[1],
                                                                    tank.server)
                                                        
                                        else:
                                                pass
                                                
                                
                        
        
        
	
	
    




