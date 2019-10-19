#!/usr/bin/python

from ServerMessageTypes import ServerMessageTypes
from ServerComms import ServerComms
import threading
import time
import logging

class ThreadingTank(threading.Thread):
	
	def __init__(self, name, port=8052, hostname='127.0.0.1'):
		threading.Thread.__init__(self)
		self.ids_to_messages = {}
		self.items_to_ids = {"Tank":[], 
		"HealthPickup": [], 
		"AmmoPickup": [],
		"SnitchPickup": []}
		self.status = {}
		self.server = ServerComms(hostname, port)
		self.name = name
		logging.info("Creating tank with name '{}'".format(name))
	
	
	
	"""
	Sends any message given to the server :)
	"""
	def messageServer(self, newMessage, params = {}):
		self.server.sendMessage(newMessage, params )
		#logging.info("Attempted to " + ServerMessageTypes.toString(newMessage))
	
	def getItems(self, message):
		if not "Id" in message:
			return
			
		id = message["Id"]
		type = message["Type"]
		self.ids_to_messages[id] = message
		if (id not in self.items_to_ids[type]):
			self.items_to_ids[type].append(id)
			
	def run(self):
		self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name': self.name, })
		while True:
			self.message = self.server.readMessage()
			#logging.info(self.message)
			self.getItems(self.message)
			print(self.items_to_ids)
		return
		
	
	

	
	

        

	
if __name__ == "__main__":
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)	
	
	TEAM = "TeamA"
	tanks = []
	for i in range(4):
		tanks.append(ThreadingTank(TEAM+":{}".format(i)))
		tanks[-1].start()
		
	
	
    




