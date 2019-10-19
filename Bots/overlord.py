#!/usr/bin/python

from ServerMessageTypes import ServerMessageTypes
from ServerComms import ServerComms
import threading
import time
import argparse
import logging
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

class ThreadingTank(threading.Thread):
	
	def __init__(self, name, port=8052, hostname='127.0.0.1'):
		threading.Thread.__init__(self)
		
		self.server = ServerComms(hostname, port)
		self.name = name
		logging.info("Creating tank with name '{}'".format(name))
	
	def run(self):
		self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name': self.name, })
		while True:
		
			message = self.server.readMessage()
			#logging.info(message)
		return

logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)	
        

	
if __name__ == "__main__":
	TEAM = "TeamA"
	tanks = []
	for i in range(4):
		tanks.append(MultiProcessingTank(TEAM+":{}".format(i)))
		tanks[-1].start()
	
	
    




