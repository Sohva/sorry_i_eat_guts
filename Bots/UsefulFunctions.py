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

	return turn_angle

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
	print(turn_angle)
	server.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": turn_angle})

	return turn_angle

def friendlyFire(this_tank, tanks, closest_enemy, fire_direction, team):
	friend_in_way = False
	danger_angle = 25

	for tank in tanks:
		for object in tank.dictOfThings.messages.values():
			if object['Id'] != this_tank.info['Id'] and object['Name'].split(':')[0] == team:
				x_diff = object['X'] - tank.info['X']
				y_diff = object['Y'] - tank.info['Y']

				if x_diff >= 0:
					if y_diff >= 0:
						friend_angle = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
					else:
						friend_angle = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)
				else:
					if y_diff >= 0:
						friend_angle = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
					else:
						friend_angle = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)

				if abs(friend_angle - fire_direction) < danger_angle:
					if math.sqrt(x_diff**2 + y_diff**2) <= math.sqrt((tank.info['X'] - closest_enemy[0])**2 +
					                                                 (tank.info['Y'] - closest_enemy[1])**2):
						friend_in_way = True

	return friend_in_way

def maintainDistance(tank, server):
	too_close_angle = 10
	too_close_distance = 10
	adjustment_angle = 10
	for object in tank.dictOfThings.messages.values():
		if object['Id'] != tank.info['Id'] and object['Type'] == "Tank" and\
			abs(tank.info['Heading'] - object['Heading']) < too_close_angle and\
			math.sqrt((tank.info['X'] - object['X'])**2 + (tank.info['Y'] - object['Y'])**2) < too_close_distance:
				if tank.info['Heading'] >= object['Heading']:
					server.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': tank.info['Heading'] - adjustment_angle})
				else:
					server.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': tank.info['Heading'] + adjustment_angle})
				zigzag(tank, server)

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

def findClosestAmmo(tank):
	closest_distance = 100000
	result = None
	location = tank.location
	for object in tank.dictOfThings.messages.values():
		if object["Type"].split(":")[0] == "AmmoPickup":
			distance = math.sqrt((location[0] - object['X']) ** 2 + (location[1] - object['Y']) ** 2)
			if distance < closest_distance:
				closest_distance = distance
				result = (object['X'], object['Y'], object['Id'])
	return result

def findClosestHealth(tank):
	closest_distance = 100000
	result = None
	location = tank.location
	for object in tank.dictOfThings.messages.values():
		if object["Type"].split(":")[0] == "HealthPickup":
			distance = math.sqrt((location[0] - object['X']) ** 2 + (location[1] - object['Y']) ** 2)
			if distance < closest_distance:
				closest_distance = distance
				result = (object['X'], object['Y'], object['Id'])
	return result

def findClosestEnemy(tank, our_team):
	closest_distance = 100000
	result = None
	location = tank.location
	for object in tank.dictOfThings.messages.values():
		if object['Type'] == "Tank" and object["Name"].split(":")[0] != our_team:
			if object.get("has_snitch", False):
				return (object['X'], object['Y'], object['Id'])
			distance = math.sqrt((location[0] - object['X'])**2 + (location[1] - object['Y'])**2)
			if distance < closest_distance:
				closest_distance = distance
				result = (object['X'], object['Y'], object['Id'])
	return result

def getShotHeading(tank, target):
	time_interval = 0.1
	tank_pos = (tank['X'], tank['Y'])
	target_pos_init = (target['X'], target['Y'])
	#tank_v = getVelocity(tank, (tank['X'], tank['Y']), time_interval)
	target_v = getVelocity(target, target_pos_init, time_interval)

	y_diff = (target_pos_init[1] + target_v[1] * time_interval) - tank_pos[1]
	x_diff = (target_pos_init[0] + target_v[0] * time_interval) - tank_pos[0]

	if x_diff >= 0:
		if y_diff >= 0:
			shot_heading = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
		else:
			shot_heading = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)
	else:
		if y_diff >= 0:
			shot_heading = 360 - (math.atan2(y_diff, x_diff) * 360 / (2 * math.pi))
		else:
			shot_heading = -math.atan2(y_diff, x_diff) * 360 / (2 * math.pi)

	return shot_heading

def getVelocity(tank, init_position, time_interval):
	time.sleep(time_interval)
	vx = (tank['X'] - init_position[0]) / time_interval
	vy = (tank['Y'] - init_position[0]) / time_interval
	return tuple((vx,vy))

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

def goToSnitch(tank, server):
	for object in tank.dictOfThings.messages.values():
		if object['Name'] == "Snitch":
			target_distance = math.sqrt((tank['X'] - object['X']) ** 2 + (tank['Y'] - object['Y']) ** 2)
			turnTankToFaceTarget(tank['X'], tank['Y'], object['X'], object['Y'])
			server.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,
							   {'Amount': target_distance})
			return
	print("snitch not found")
	tank.isSeeker = False

def turnRandomly(server):
	logging.info("Turning randomly")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)})


def distanceTo(loc1, loc2):
    return ((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2) ** (0.5)

def shoot_with_predictive_aiming(tank, target, server):
	# shoot_with_predictive_aiming(tank.ids_to_messages[tank.id], tank.ids_to_messages[closest_enemy[2]], tank.server)
	print("shooting with predictive aiming")
	shoot_angle = getShotHeading(tank, target)
	print("angle to shoot at is ", shoot_angle)
	server.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': shoot_angle})
	server.sendMessage(ServerMessageTypes.FIRE)


def zigzag(tank, server):
	heading = float(tank.info['Heading'])

	start_time = dt.datetime.now()

	tank.zigzagging = True
	print("TURNING")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING,
	                   {'Amount': heading + 30})
	while (dt.datetime.now() - start_time).seconds < 2:
		pass
	print("TURNING")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING,
		                   {'Amount': heading - 60})
	while (dt.datetime.now() - start_time).seconds < 3:
		pass
	print("TURNING")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING,
		                   {'Amount': heading + 60})
	while (dt.datetime.now() - start_time).seconds < 4:
		pass
	print("TURNING")
	server.sendMessage(ServerMessageTypes.TURNTOHEADING,
	                   {'Amount': heading - 30})
	tank.zigzagging = False


def shoot(server):
	server.sendMessage(ServerMessageTypes.FIRE)

def setSeeker(tanks):
	dictOfThings = tanks[0].dictOfThings
	snitch_location = None

	for object in dictOfThings.messages.values():
		if object["Type"] == "Snitch":
			snitch_location = (object["X"], object["Y"])

	if not snitch_location:
		return False

	closest_dist = 100000
	closest_tank = tanks[0]
	for tank in tanks:
		distance = math.sqrt((tank.info['X'] - snitch_location[0]) ** 2 + (tank.info['Y'] - snitch_location[1]) ** 2)
		if distance < closest_dist:
			closest_dist = distance
			closest_tank = tank
	closest_tank.isSeeker = True
	return True



def closestToSnitch(objects, tank):
	snitch_pos = None
	for object in objects.dictOfThings.messages.values():
		if object['Name'] == "Snitch":
			snitch_pos = (object['X'], object['Y'])

	if snitch_pos == None:
		return None

	closest_distance = math.sqrt((tank.info['X'] - snitch_pos[0]) ** 2 +
			                (tank.info['Y'] - snitch_pos[1]) ** 2)
	this_tank_closest = True
	for object in objects:
		if object.info['Id'] != tank.info['Id'] and object.info['Type'] == "Tank":
			if math.sqrt((tank.info['X'] - object.info['X']) ** 2 +
			        (tank.info['Y'] - object.info['Y']) ** 2) < closest_distance:
				this_tank_closest = False

	return this_tank_closest
