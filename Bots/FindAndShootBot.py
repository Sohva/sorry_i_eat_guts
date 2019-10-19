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


def turnTurretToFaceTarget(x_tank, y_tank, x_target, y_target):
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

	GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": turn_angle})


def turnTankToFaceTarget(x_tank, y_tank, x_target, y_target):
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

	GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": turn_angle})


def moveToPoint(x_tank, y_tank, x_target, y_target):
	turnTankToFaceTarget(x_tank, y_tank, x_target, y_target)
	distance = math.sqrt(math.pow(x_target - x_tank, 2) + math.pow(y_target - y_tank, 2))
	#GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': distance})


# Connect to game server
GameServer = ServerComms(args.hostname, args.port)

# Spawn our tank
myName = "TeamB:SBot"
myXCoord = 0
myYCoord = 0
allowedTurn = True
lastTurnTime = None
logging.info("Creating tank with name '{}'".format("TeamB:SBot"))
GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': myName})

print("today seconds is ", time.time())

lastTurnTime = time.time()
# Main loop
while True:
	message = GameServer.readMessage()
	print(message)

	# GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {"Amount": 90})
	# GameServer.sendMessage(ServerMessageTypes.MOVEBACKWARSDISTANCE, {"Amount": 90})
	# GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": 90})
	# GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": 100})
	# GameServer.sendMessage(ServerMessageTypes.FIRE)

	if 'Name' not in message:
		continue

	if message['Name'] == myName:
		myXCoord = message['X']
		myYCoord = message['Y']
		logging.info("my X position is: %d"% message['X'])
		logging.info("my Y position is: %d"% message['Y'])
		logging.info("my heading is: %d"% message['Heading'])
		logging.info("my turret heading is: %d" % message['TurretHeading'])

	if message['Name'] == "ManualTank":
		logging.info("Found target")

		now = time.time()
		print("now minus lastTurnTime seconds is ", now - lastTurnTime)
		if now - lastTurnTime > 0.1:
			turnTurretToFaceTarget(myXCoord, myYCoord, message["X"], message["Y"])
			lastTurnTime = time.time()

		moveToPoint(myXCoord, myYCoord, message["X"], message["Y"])
		logging.info("Firing")
		GameServer.sendMessage(ServerMessageTypes.FIRE)



