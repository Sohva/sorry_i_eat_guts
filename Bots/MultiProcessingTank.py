#!/usr/bin/python

from ServerMessageTypes import ServerMessageTypes
from ServerComms import ServerComms
import multiprocessing

class MultiProcessingTank(multiprocessing.Process):
	
	def __init__(self, name, port=8052, hostname='127.0.0.1'):
		multiprocessing.Process.__init__(self)
		
		self.server = ServerComms(hostname, port)
		self.name = name
		logging.info("Creating tank with name '{}'".format(name))
	
	def run(self):
		self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name': self.name, })
		while True:
		
			message = self.server.readMessage()
			#logging.info(message)
		return