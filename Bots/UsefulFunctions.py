#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import random
import math
import time
import datetime as dt


class ServerMessageTypes(object):
	TEST = 0
	CREATETANK = 1
	DESPAWNTANK = 2
	FIRE = 3
	TOGGLEFORWARD = 4
	TOGGLEREVERSE = 5
	TOGGLELEFT = 6
	TOGGLERIGHT = 7
	TOGGLETURRETLEFT = 8
	TOGGLETURRETRIGHT = 9
	TURNTURRETTOHEADING = 10
	TURNTOHEADING = 11
	MOVEFORWARDDISTANCE = 12
	MOVEBACKWARSDISTANCE = 13
	STOPALL = 14
	STOPTURN = 15
	STOPMOVE = 16
	STOPTURRET = 17
	OBJECTUPDATE = 18
	HEALTHPICKUP = 19
	AMMOPICKUP = 20
	SNITCHPICKUP = 21
	DESTROYED = 22
	ENTEREDGOAL = 23
	KILL = 24
	SNITCHAPPEARED = 25
	GAMETIMEUPDATE = 26
	HITDETECTED = 27
	SUCCESSFULLHIT = 28
    
	strings = {
		TEST: "TEST",
		CREATETANK: "CREATETANK",
		DESPAWNTANK: "DESPAWNTANK",
		FIRE: "FIRE",
		TOGGLEFORWARD: "TOGGLEFORWARD",
		TOGGLEREVERSE: "TOGGLEREVERSE",
		TOGGLELEFT: "TOGGLELEFT",
		TOGGLERIGHT: "TOGGLERIGHT",
		TOGGLETURRETLEFT: "TOGGLETURRETLEFT",
		TOGGLETURRETRIGHT: "TOGGLETURRENTRIGHT",
		TURNTURRETTOHEADING: "TURNTURRETTOHEADING",
		TURNTOHEADING: "TURNTOHEADING",
		MOVEFORWARDDISTANCE: "MOVEFORWARDDISTANCE",
		MOVEBACKWARSDISTANCE: "MOVEBACKWARDSDISTANCE",
		STOPALL: "STOPALL",
		STOPTURN: "STOPTURN",
		STOPMOVE: "STOPMOVE",
		STOPTURRET: "STOPTURRET",
		OBJECTUPDATE: "OBJECTUPDATE",
		HEALTHPICKUP: "HEALTHPICKUP",
		AMMOPICKUP: "AMMOPICKUP",
		SNITCHPICKUP: "SNITCHPICKUP",
		DESTROYED: "DESTROYED",
		ENTEREDGOAL: "ENTEREDGOAL",
		KILL: "KILL",
		SNITCHAPPEARED: "SNITCHAPPEARED",
		GAMETIMEUPDATE: "GAMETIMEUPDATE",
		HITDETECTED: "HITDETECTED",
		SUCCESSFULLHIT: "SUCCESSFULLHIT"
	}
    
	def toString(self, id):
		if id in self.strings.keys():
			return self.strings[id]
		else:
			return "??UNKNOWN??"


class ServerComms(object):
	'''
	TCP comms handler
	
	Server protocol is simple:
	
	* 1st byte is the message type - see ServerMessageTypes
	* 2nd byte is the length in bytes of the payload (so max 255 byte payload)
	* 3rd byte onwards is the payload encoded in JSON
	'''
	ServerSocket = None
	MessageTypes = ServerMessageTypes()
	
	
	def __init__(self, hostname, port):
		self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ServerSocket.connect((hostname, port))

	def readTolength(self, length):
		messageData = self.ServerSocket.recv(length)
		while len(messageData) < length:
			buffData = self.ServerSocket.recv(length - len(messageData))
			if buffData:
				messageData += buffData
		return messageData

	def readMessage(self):
		'''
		Read a message from the server
		'''
		messageTypeRaw = self.ServerSocket.recv(1)
		messageLenRaw = self.ServerSocket.recv(1)
		messageType = struct.unpack('>B', messageTypeRaw)[0]
		messageLen = struct.unpack('>B', messageLenRaw)[0]
		
		if messageLen == 0:
			messageData = bytearray()
			messagePayload = {'messageType': messageType}
		else:
			messageData = self.readTolength(messageLen)
			logging.debug("*** {}".format(messageData))
			messagePayload = json.loads(messageData.decode('utf-8'))
			messagePayload['messageType'] = messageType
			
		logging.debug('Turned message {} into type {} payload {}'.format(
			binascii.hexlify(messageData),
			self.MessageTypes.toString(messageType),
			messagePayload))
		return messagePayload
		
	def sendMessage(self, messageType=None, messagePayload=None):
		'''
		Send a message to the server
		'''
		message = bytearray()
		
		if messageType is not None:
			message.append(messageType)
		else:
			message.append(0)
		
		if messagePayload is not None:
			messageString = json.dumps(messagePayload)
			message.append(len(messageString))
			message.extend(str.encode(messageString))
			    
		else:
			message.append(0)
		
		logging.debug('Turned message type {} payload {} into {}'.format(
			self.MessageTypes.toString(messageType),
			messagePayload,
			binascii.hexlify(message)))
		return self.ServerSocket.send(message)


# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='TeamA:RandomBot', help='Name of bot')
args = parser.parse_args()

# Set up console logging
if args.debug:
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)


def turnTurretToFaceTarget(x_tank, y_tank, x_target, y_target, server):
	x_diff = x_target - x_tank
	y_diff = y_target - y_tank

	if x_diff >= 0:
		if y_diff >= 0:
			turn_angle = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
		else:
			turn_angle = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)
	else:
		if y_diff >= 0:
			turn_angle = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
		else:
			turn_angle = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)

	server.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": turn_angle})


def turnTankToFaceTarget(x_tank, y_tank, x_target, y_target, server):
	x_diff = x_target - x_tank
	y_diff = y_target - y_tank

	if x_diff >= 0:
		if y_diff >= 0:
			turn_angle = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
		else:
			turn_angle = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)
	else:
		if y_diff >= 0:
			turn_angle = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
		else:
			turn_angle = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)

	server.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": turn_angle})


def moveToPoint(x_tank, y_tank, x_target, y_target, server):
	turnTankToFaceTarget(x_tank, y_tank, x_target, y_target, server)
	distance = math.sqrt(math.pow(x_target - x_tank, 2) + math.pow(y_target - y_tank, 2))
	print("distance is ", distance)
	server.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': distance})

def goToGoal(x_tank, y_tank, server):
	if y_tank >= 0:
		moveToPoint(x_tank, y_tank, 0, 100, server)
	else:
		moveToPoint(x_tank, y_tank, 0, -100, server)

def findClosestAmmo(our_tanks, location):
	closest_distance = 10000
	closest_location = None
	for our_tank in our_tanks:
		for object in our_tank.ids_to_messages.values():
			if object["Type"].split(":")[0] == "AmmoPickup":
				distance = math.sqrt((location[0] - object['X']) ** 2 + (location[1] - object['Y']) ** 2)
				if distance < closest_distance:
					closest_distance = distance
					closest_location = (object['X'], object['Y'])
	return closest_location

def findClosestEnemy(our_tanks, location, our_team):
	closest_distance = 100000
	closest_location = None
	for our_tank in our_tanks:
		for object in our_tank.ids_to_messages.values():
			if object['Type'] == "Tank" and object["Name"].split(":")[0] != our_team:
				distance = math.sqrt((location[0] - object['X'])**2 + (location[1] - object['Y'])**2)
				if distance < closest_distance:
					closest_distance = distance
					closest_location = (object['X'],object['Y'])
	return closest_location

def getShotHeading(tank, target):

	time_interval = 0.01
	tank_pos = (0,0)
	target_pos = (0,0)
	#tank_v = getVelocity(tank, (tank['X'], tank['Y']), time_interval)
	target_v = getVelocity(target, (target['X'], target['Y']), time_interval)

	y_diff = (target_pos[1] + target_v[1] * time_interval) - tank_pos[1]
	x_diff = (target_pos[0] + target_v[0] * time_interval) - tank_pos[0]

	shot_heading = math.atan2(y_diff, x_diff)

	return shot_heading

def getVelocity(tank, position, time_interval):
	time.sleep(time_interval)
	vx = (tank['X'] - position[0]) / time_interval
	vy = (tank['Y'] - position[0]) / time_interval
	return tuple(vx,vy)

def moveRandomly(server):
	logging.info("Turning randomly")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)})
	logging.info("Moving randomly")
	server.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': random.randint(0, 10)})

def seekerExists(our_tanks):
	for tank in our_tanks:
		if tank.isSeeker:
			return True
	return False

def goToSnitch(our_tanks, server):
	for tank in our_tanks:
		for object in tank.ids_to_messages.values():
			if object['Name'] == "Snitch":
				target_distance = math.sqrt((tank['X'] - object['X']) ** 2 + (tank['Y'] - object['Y']) ** 2)
				turnTankToFaceTarget(tank['X'], tank['Y'], object['X'], object['Y'])
				server.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,
				                   {'Amount': target_distance})

def turnRandomly(server):
	logging.info("Turning randomly")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)})


def distanceTo(loc1, loc2):
    return ((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2) ** (0.5)

