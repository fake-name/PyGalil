


import time
import threading
import traceback

try:
	import globalConf
except ImportError:
	globalConf = type('', (), {})  # Empty, extensible object.
	globalConf.fakeGalil = False

if not globalConf.fakeGalil:
	import socket
	print "Using real socket at start"
else:
	import fakeSocket as socket
	print "Using fake socket at start"

import sys

import math
try:
	import PyGalil.drParse as drParse
except ImportError:
	import drParse


import os.path



# Enables and disables logging of timestamps for analysis
LOG_TIMESTAMPS = True

CONF_TIMEOUT = 0.5


class GalilInterface():

	numAxis		=	2		# the DMC-2120 has two axes
	running		=	True

	pos			= [0,0,0,0,0,0,0,0,0]
	vel			= [0,0,0,0,0,0,0,0,0]
	inMot		= [0,0,0,0,0,0,0,0,0]
	motOn		= [0,0,0,0,0,0,0,0,0]

	udpPackets = 0
	doUDPFileLog = False
	oldTime = 0

	udpInBuffer = ""

	threads = []
	haveGpsLock = False
	gpsMsTow = False
	gpsMsTowErr = False

	def __axisIntToLetter(self, axis):
		return chr(65+axis)

	def __axisLetterToInt(self, axis):
		return ord(axis[-1])-65


	# Whoo getters!
	@property
	def haveLock(self):
		return self.haveGpsLock

	@property
	def gpsTime(self):
		return self.gpsMsTow

	@property
	def gpsDelTime(self):
		return self.gpsMsTowErr






	def __init__(self,
					ip,                   # Remote IP of the galil
					port       = 23,      # Port to use when talking to the galil
					                      # (they normally listen on all ports, using telnet's
					                      # port makes it so wireshark decodes any com traffic nicely)
					poll       = False,   # Poll for system state using a TCP socket. Processor intensive.
					resetGalil = False,   # Reset galil on connect.
					download   = True,    # Download galilCode from `stageCode.dmc` on connect
					unsol      = True,    # Open a secondary TCP socket for unsolicited messages.
					dr         = True,    # Enable and activate Data-Record outputs.
					debug      = False):  # Debug- Debug printing

		if debug:
			self.debug = True
		else:
			self.debug = False


		self.port = port
		self.ip = ip

		print "Starting Interface"


		self.con = socket.create_connection((self.ip, self.port ), CONF_TIMEOUT)
		self.con.settimeout(CONF_TIMEOUT)


		if resetGalil:
			print "Resetting Galil"
			self.resetGalil(download)



		# Close ALL THE (other) SOCKETS
		# This is a (somewhat) undocumented function call.
		# It closes ALL the sockets on the galil, not just the one
		# the message is received on.
		self.sendOnly("IHT=-3;")


		if poll:
			print "Beginning Solicited TCP Polling"
			self.__startPolling()

		if unsol:
			print "Opening Unsolicited messages socket."
			self.__initUnsolicitedMessageSocket()

		if dr:
			print "Setting up data-record transfers"
			self.__initUDPMessageSocket()

		if self.doUDPFileLog:
			self.fileH = open("posvelDR.txt", "a")

	def __del__(self):
		self.close()

	def __initUnsolicitedMessageSocket(self):
		# The reccomended way for handling both solicited and unsolicited messages from the galil is to use two sockets. One socket is for normal
		# comms, and the other is configured for handling the unsolicited messages (e.g. interrupt messages, etc...)


		self.unsolCon = socket.create_connection((self.ip, self.port+1 ), CONF_TIMEOUT)

		self.unsolCon.sendall("CF I;\r\n")
		self.receiveOnly(self.unsolCon)

		# I *think* the response garbling I was seeing was CW being set. This causes the MSB of all ascii characters in unsolicited
		# messages to be set. I don't know what the default setting is, though.
		self.unsolCon.sendall("CW 2;\r\n")
		self.receiveOnly(self.unsolCon)

		self.startPollingUnsol()


	def startPollingUnsol(self):

			self.pollUnsolTh = threading.Thread(target = self.pollUnsol, name = "galilUnsolicitedPollThread")
			self.pollUnsolTh.start()
			self.threads.append(self.pollUnsolTh)


	def pollUnsol(self):

		retString = ""
		while self.running:


			try:
				retString += self.unsolCon.recv(1)

			except socket.timeout:					# Exit on timeout
				pass

			except socket.error:					# I've Seen socket.error errors a few times. They seem to not break anything.
										# Therefore, we just ignore them
				print "socket.error - wut"

			if retString.find("\r\n")+1:				#
				message, retString = retString.split("\r\n", 1)
				print "Received message - ", message

				if LOG_TIMESTAMPS:
					if message.find("Input Timestamp") + 1:
						# for some bizarre reason, the galil returns timestamps with four trailing zeros (e.g. xxx.0000)
						# The timestamps are ALWAYS just an integer
						# Anyways, the python int() function can't handle strings with a decimal, so we split off the
						# empty fractional digits
						sampleTime = int(message.split()[-1].split(".")[0])
						delta = sampleTime - self.oldTime
						self.oldTime = sampleTime
						print "Timestamp", int(sampleTime), "Delta", delta
						with open("tsLog.txt", "a") as fileP:
							fileP.write("Timestamp, %s, %s \n" % (sampleTime, delta))


	def _flushBufUDP(self, socketConnection, galilAddrTup):

		self._sendAndReceiveUDP("TP;", socketConnection, galilAddrTup)
		for cnt in range(2):
			self._receiveUDP(socketConnection)

		self.udpInBuffer = ""
		self.flushSocketRecvBuf(socketConnection)

	def _receiveUDP(self, socketConnection):
		startTime = time.time()
		ret = ""
		while time.time() < (startTime + CONF_TIMEOUT):
			try:
				tmp, ipAddr = socketConnection.recvfrom(1024)
				self.udpInBuffer += tmp
			except socket.error:
				pass
			#print self.udpInBuffer

			if self.udpInBuffer.find(":")+1:
				ret, self.udpInBuffer = self.udpInBuffer.split(":", 1)
				ret = ret.rstrip().lstrip()
				if ret:		# Check we actually have something.
							# Occationally, you just get two colons ("::"), which results in an empty ret
					break

		return ret



	def _sendAndReceiveUDP(self, cmdStr, socketConnection, addrTuple):
		#First, we need to clear the input buffer, because we want to get rid of any previous strings
		self.flushSocketRecvBuf(self.con)


		cmdStr = cmdStr + "\r\n"
		socketConnection.sendto(cmdStr, addrTuple) 		# send the command string
		time.sleep(0.2)				# give some time for the galil to respond

		socketConnection.settimeout(CONF_TIMEOUT)
		return self._receiveUDP(socketConnection)


	def __initUDPMessageSocket(self):

		print "Opening UDP Socket"

		# We need to know the local address to bind to to receive UDP messages from the galil
		# There is not particularly elegant way to get this. As such, we open a TCP socket connection
		# and then look at the local connection information to figure out which interface we're using to
		# talk to the galil over TCP. It's probably safe to use that for UDP too

		# it's either that, or try to call `route` using subprocess and parse that output, and that
		# is a REALLY clumsly solution
		con = socket.create_connection((self.ip, self.port ), 1)
		if not globalConf.fakeGalil:
			localIP = (con.getsockname()[0])
		else:
			localIP = None
		con.shutdown(socket.SHUT_RDWR)
		con.close()

		_UDP_PORT = 5005
		_UDP_ADDR_TUPLE = (localIP, _UDP_PORT)
		_GALIL_UDP_ADDR_TUPLE = (self.ip, _UDP_PORT)

		# UDP socket for DR (data record) logging from the galil
		drSock = socket.socket(socket.AF_INET, # Internet
 		                    socket.SOCK_DGRAM, # UDP
 		                    socket.IPPROTO_UDP)

		drSock.bind(_UDP_ADDR_TUPLE)

		if globalConf.fakeGalil:
			return

		print "Flushing UDP connection",
		self._flushBufUDP(drSock, _GALIL_UDP_ADDR_TUPLE)
		print "Connection Flushed"
		ret = ""
		# It seems that occationally the initial response from the galil on a UDP socket
		# is garbage. Therefore, we loop until we see a proper response to the initial query
		print "Waiting for a valid packet"
		while not ret.find("IH") + 1:
			ret =  self._sendAndReceiveUDP("WH;", drSock, _GALIL_UDP_ADDR_TUPLE)
			if not ret.find("IH") + 1:
				print "Bad return value - '%s'" % ret

		self.udpHandleNumber = self.__axisLetterToInt(ret)
		if (self.udpHandleNumber > 7) or (self.udpHandleNumber < 0) :
			raise ValueError("Invalid handle number. Garbled data on init?")

		print "UDP Handle: \"%s\", e.g. handle %d" % (ret, self.udpHandleNumber)

		ret =  self._sendAndReceiveUDP("QZ;", drSock, _GALIL_UDP_ADDR_TUPLE)
		self.infoTopology = ret

		# receive until we start timing out.
		tmp = self._receiveUDP(drSock)
		while tmp:
			print "Ret: \"", tmp, "\""
			tmp = self._receiveUDP(drSock)

		drSock.sendto("DR 103,%s\r\n" % self.udpHandleNumber, _GALIL_UDP_ADDR_TUPLE)

		#drSock.settimeout(1)
		#time.sleep(1)



		#print data, addr
		print "UDP Init done"

		self._startPollingUDP(drSock, _GALIL_UDP_ADDR_TUPLE)


		#self._startPollingUDP()


	def _startPollingUDP(self, udpSock, galilAddrTup):

			self.pollUDPTh = threading.Thread(target = self._pollUDP, name = "galilUDPPollThread", args = (udpSock, galilAddrTup))
			self.pollUDPTh.start()
			self.threads.append(self.pollUDPTh)


	def handleDatarecord(self, dr):

		self.udpPackets += 1

		# Pull out status vars and single values
		self.gpsMsTow    = dr['mstow']
		self.haveGpsLock = dr['lock']
		self.gpsMsTowErr = dr['towerr'] * -1

		# Axis letter in the DR dictionary, and their corresonding offset
		# in the self.pos/self.vel/self.inMot arrays
		axes = [("A", 0),
				("B", 1),
				("C", 2),
				("D", 3)]

		for axis, offset in axes:
			if axis in dr:
				#print dr[axis]
				self.pos[offset]    = dr[axis]["motorPos"]
				self.vel[offset]    = dr[axis]["vel"]
				self.inMot[offset]  = dr[axis]["status"]["moving"]
				self.motOn[offset]  = not dr[axis]["status"]["motorOff"]



		if self.doUDPFileLog:
			logStr = "DR Received, %s, %s, %s, %s\n" % (int(time.time()*1000), self.gpsMsTow, self.gpsMsTow, self.gpsMsTowErr)
			self.fileH.write(logStr)


		if self.debug:
			print("Data record!")
			print("MSTOW", self.gpsTime)
			print("MSTOW err", self.gpsDelTime)


	def _pollUDP(self, udpSock, galilAddrTup):

		while self.running:

			try:
				dat, ip = udpSock.recvfrom(1024)
				#print "received", len(dat), ip,
				dr = drParse.parseDataRecord(dat)

				if dr:
					self.handleDatarecord(dr)
				else:
					if self.doUDPFileLog:
						self.fileH.write("Bad DR Received, %s\n" % (time.time()))

			except socket.timeout:					# Exit on timeout
				pass

			except socket.error:				# I've Seen socket.error errors a few times. They seem to not break anything.
										# Therefore, we just ignore them
				print "pollUDP socket.error wut"
				if self.doUDPFileLog:
					self.fileH.write("Socket Error, %s, %s\n" % (time.time(), time.strftime("Datalog - %Y/%m/%d, %a, %H:%M:%S", time.localtime())))

		# Turn off the data-record outputs
		self._sendAndReceiveUDP("DR 0,0;\r\n", udpSock, galilAddrTup)

		# Tell the galil to close the UDP socket
		# This *seems* to work, though supposedly the IH command only works on sockets the galil opens as master.
		# Undocumented features, AHOY!
		# Never mind, it's documented, just in more recent docs
		self._sendAndReceiveUDP("IHS=-3;\r\n", udpSock, galilAddrTup)	# IHS=-3 means "close the socket this command is received on"

		pktFlushTime = 3
		for x in range(pktFlushTime):
			print "Waiting for any remaining packets, ", pktFlushTime-x

			try:
				dat, ip = udpSock.recvfrom(1024)
				#print "received", len(dat), ip

			except socket.timeout:					# Exit on timeout
				pass

			except socket.error:					# I've Seen socket.error errors a few times. They seem to not break anything.
													# Therefore, we just ignore them

				print "pollUDP exiting socket.error wut"


	def __downloadFunctions(self, stripComments=False):

		#
		# Download a file of galilCode to the remote controller.
		#
		# Note: The galil only supports one "file" of code. Every time you download new routines, it overwrites everything
		# that is currently on the galil. You can have multiple functions in one code-file, so it's not a serious problem,
		# just something you have to keep in mind.
		#

		#First, we need to clear the input buffer, because we want to get rid of any previous strings
		self.con.settimeout(0.0)
		try:
			self.con.recv(256)
		except socket.error:
			pass

		gcFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'galilCode', "stageCode.dmc")
		codeFile = open(gcFile, "r")
		routines = codeFile.read()
		codeFile.close()

		# Enter program download mode
		self.con.sendall("DL\r")

		# for printing a nice representation of the code
		lineNum = 1

		print "Starting download of galilcode routines"
		print "LineNum, Code"
		for line in routines.split("\n"):

			# Strip whatever variety of \r\n chars are in the file
			line = line.rstrip()

			if stripComments and (line == "" or line.strip(" ")[0:2] == "NO"):
				continue # ignore blank and comment lines if told to

			elif line == "":
				line = "'"
				# add a comment character ("'") to all empty lines
				# so they don't break the galil
				# the galil terminal does this silently, behind the scenes, when you send a code file.
				# very confusing, since the manual states that empty lines are not allowed, but they
				# work anyways within the galilTerminal application

			# the Galil wants carriage-return (only!) line endings.
			# I wonder if the original galil protocol design work was done on a mac?
			cleanedLine = line + "\r"

			if len(cleanedLine) > 80:				# Check line lengths
				print "Error - Line %d too long" % lineNum
				print "Ensure all galilCode lines are shorter then 80 characters"
				print "Line contents: ", cleanedLine
				raise ValueError

			# Print linenum and line (and strip the extra \r / \n) (for debugging)
			print str(lineNum).zfill(4), cleanedLine.rstrip()
			lineNum += 1

			self.con.sendall(cleanedLine)				# finally, send the line
			try:
				if self.con.recv(256) and not globalConf.fakeGalil:
					# and check for a response
					# (there shouldn't be. You only get a response of there is an error)
					# Note: In "download" mode, the galil *does not* respond with ":" after each line
					# If you're seeing those, there is a problem somewhere, or you're not in download mode.
					# The galil only responds with ":"/"?" in interactive mode.
					raise ValueError("Error downloading galil code")
			except socket.error:
				pass

			time.sleep(0.05)					# a short pause so we don't overflow the galil's TCP input buffer
												# (Yes, it was happening)

		self.con.sendall("\\\r")					# leave program download mode

		time.sleep(0.1)							# Needed to work around some bugs in the crApple python TCP stack

		print "Sent"
		try:
			# Check status return code from the download operaton
			# It should be two colons ("::"). Should probably check for that.
			print "Received - ", self.con.recv(64).rstrip().lstrip().rstrip(":").lstrip(":")

		except socket.error:
			print "Galil Timed Out"
			traceback.print_exc(6)


		self.con.settimeout(CONF_TIMEOUT)


	def __startPolling(self):
		self.polCon = socket.create_connection((self.ip, self.port + 1), CONF_TIMEOUT)
		self.polCon.settimeout(CONF_TIMEOUT)
		#self.con.setblocking(0)

		self.pollPosTh = threading.Thread(target = self.posVelPol, name = "galilPollThread")
		self.pollPosTh.start()
		self.threads.append(self.pollPosTh)



	def flushSocketRecvBuf(self, socketCon):
		#python socket.socket doesn't have a flush() function! WTF?

		try:
			socketCon.settimeout(0.0)
			socketCon.recv(1024)
		except socket.error:
			pass
		finally:
			socketCon.settimeout(CONF_TIMEOUT)


	def posVelPol(self):
		fp = open("posvelpol.txt", "a")
		while self.running:
			self.flushSocketRecvBuf(self.polCon)

			try:
				# Horrible one-liners of DOOOOOOOMMMMM
				#
				# This line takes the return values from the "TP" command, cleans them, breaks them into separate variables
				# typeconverts to int, and stuffs them into a list
				#

				self.polCon.sendall("TP\r\n")
				temp =  [int(float(i)) for i in self.receiveOnly(self.polCon).rstrip("\r\n:").strip().strip(":").replace(", ", " ").split()]
				self.pos = temp

				# and for the "TV" command
				self.polCon.sendall("TV\r\n")
				temp = [int(float(i)) for i in self.receiveOnly(self.polCon).rstrip("\r\n:").strip().strip(":").replace(", ", " ").split()]
				self.vel = temp

				#Now, we check axis state (moving or not moving)

				# First, construct a query string based on the number of axis the galil has
				motionStStr = "MG "
				for x in range(self.numAxis):
					axLetter = self.__axisIntToLetter(x)
					motionStStr += ", _BG%s, _MO%s" % (axLetter, axLetter)
				motionStStr += "\r\n"

				# then query the galil
				self.polCon.sendall(motionStStr)
				recStr = self.receiveOnly(self.polCon)

				#finally, another horrible one-liner to parse the return string

				self.inMot = [bool(int(i.split(".")[0])) for i in recStr.rstrip("\r\n:").strip().strip(":").replace(", ", " ").split()]

				#print motionStStr, recStr

				#print recStr
				#print "Pos, Vel", self.pos, self.vel

				#print "Polled"
				fp.write("Polled, %s, %s\n" % (time.time(), time.strftime("Datalog - %Y/%m/%d, %a, %H:%M:%S", time.localtime())))
			except socket.error:
				print "Communications Error"
				fp.write("Comm Error, %s, %s\n" % (time.time(), time.strftime("Datalog - %Y/%m/%d, %a, %H:%M:%S", time.localtime())))
				traceback.print_exc()

			time.sleep(0.1)

		fp.close()

	def checkAxis(self, axis):						# Check if an axis number is valid
		if (axis + 1) > self.numAxis:
			print axis
			raise ValueError("Invalid Axis")


	def sendOnly(self, cmdStr, debug = True):				# Send a command string without listening for a response
		cmdStr = cmdStr + "\r"						# append the line terminator the galil wants

		if debug:
			print "Sent Command - \"", cmdStr.rstrip().strip(), "\""

		self.con.sendall(cmdStr)


	def receiveOnly(self, socketConnection, mask=False):				# Receive from the galil until the galil sends a line terminator
										# The terminates lines with either a  ":" or a "?"
										#
										# ":" - Indicates the previous command was successful
										# "?" - Indicates there was an error in the previous command (either syntax or system)

		errors = 0

		retString = ""
		while not retString.find(":")+1:				# Galil return strings end with a colon (":"). We loop on the socket untill we either see a colon, or time out
			try:
				retString += socketConnection.recv(1)

			except socket.timeout:					# Exit on timeout
				print "Galil Timed Out"
				traceback.print_exc(6)
				break

			except socket.error:					# I've Seen socket.error errors a few times. They seem to not break anything.
													# Therefore, we just ignore them
				print "receiveOnly socket.error wut"
				errors += 1
			if retString.find("?")+1:				# print error info if we receive a error
				print "Syntax Error - ",
				print "Returned Value:", retString
				print "Error Code:"
				print self.sendAndReceive("TC1")		# "TC1" - This queries the galil for what the previous error was caused by
				break

			if errors > 100:
				raise ValueError("Socket is returning garbage!")
		return retString

	def sendAndReceive(self, cmdStr, debug = True):
		#
		#	This is probably a little brittle for long term reliance
		#
		# Anyways, you pass the command you want to send the galil, and a
		# line termniator is autmatically appended, and the return value is read
		# back, and returned.
		#
		# The return value has the line terminator and some of the window decoration (":")
		# stripped from it to make it easier to parse
		#

		#First, we need to clear the input buffer, because we want to get rid of any previous strings
		self.flushSocketRecvBuf(self.con)


		self.sendOnly(cmdStr, debug)			# send the command string
		time.sleep(0.050)				# give some time for the galil to respond
		retString = ""


		retString = self.receiveOnly(self.con)				# check for the response.
		retString = retString.rstrip("\r\n:").strip().strip(":")	# and strip off the garbage the galil sends to make interacting with it over telnet easier.

		return retString

	def getPosition(self):

		positionStr = self.sendAndReceive("TP")

		retVals = []

		if positionStr:

										# parse the returned string of ints into a list of actual ints.

			stripStr = positionStr.replace(" ", "")

			for item in stripStr.split(","):
				try:
					retVals.append( int(item) )
				except:
					print positionStr
					raise ValueError

		return retVals

	def getVelocity(self):

		velocityStr = self.sendAndReceive("TV")

		retVals = []

		if velocityStr:
										# parse the returned string of ints into a list of actual ints.

			stripStr = velocityStr.replace(" ", "")

			for item in stripStr.split(","):
				try:
					retVals.append( int(item) )
				except:
					print velocityStr
					raise ValueError

		return retVals


	# Most of these commands are pretty self-explanitory.
	# They do what is says on the tin.
	# Mostly, the diffrerence is just in the command string

	def moveAbsolute(self, axis, position):
		self.checkAxis(axis)
		command = "PA%s=%d" % (self.__axisIntToLetter(axis), position)

		responseStr = self.sendAndReceive( command )
		#print command, positionStr

		return responseStr


	def moveRelative(self, axis, deltaPosition):
		self.checkAxis(axis)
		command = "PR%s=%d" % (self.__axisIntToLetter(axis), deltaPosition)

		responseStr = self.sendAndReceive( command )
		#print command, positionStr

		return responseStr


	def setMoveSpeed(self, axis, velocity):
		self.checkAxis(axis)
		command = "SP%s=%d" % (self.__axisIntToLetter(axis), velocity)

		responseStr = self.sendAndReceive( command )
		#print command, positionStr

		return responseStr


	def moveAtSpeed(self, axis, velocity):
		self.checkAxis(axis)
		command = "JG%s=%d" % (self.__axisIntToLetter(axis), velocity)

		responseStr = self.sendAndReceive( command )
		#print command, positionStr

		return responseStr


	def beginMotion(self, axis = None):
		if axis != None:
			command = "BG %s" % self.__axisIntToLetter(axis)
		else:
			command = "BG"

		responseStr = self.sendAndReceive( command )

		return responseStr

	def inMotion(self, axis):
		command = "MG _BG%s " % self.__axisIntToLetter(axis)

		responseStr = self.sendAndReceive( command , debug = False)

		response = bool(float(responseStr))

		return response

	def endMotion(self, axis = None):
		if axis != None:
			command = "ST %s" % self.__axisIntToLetter(axis)
		else:
			command = "ST"

		responseStr = self.sendAndReceive( command )

		return responseStr

	def motorOn(self, axis = None):
		if axis != None:
			command = "SH %s" % self.__axisIntToLetter(axis)
		else:
			command = "SH"

		responseStr = self.sendAndReceive( command )

		return responseStr

	def motorOff(self, axis = None):
		if axis != None:
			command = "MO %s" % self.__axisIntToLetter(axis)
		else:
			command = "MO"

		responseStr = self.sendAndReceive( command )

		return responseStr

	def checkMotorPower(self, axis = 0):
		return "0.0000" == self.sendAndReceive("MG _MO%s" % self.__axisIntToLetter(axis))


	#THIS THING
	#It needs to be changed, for the sake of consistency.
	#I feel like it is something that should be moved,
	#and that this library should be only the lowest level
	#primatives for interacting with the galil.
	def scan(self, x_i, encoderTics, period, cycles):
		print "Scanning. ", "x_i = ", x_i, "encoderTics = ", encoderTics, "period = ", period, "cycles = ", cycles
		max_accel = max_deccel = 1e6
		#initial_angle = 0
		# self.motorOn(x_i) #make sure a motor is on

		frequency = 1.0/period

		axis_letter = self.__axisIntToLetter(x_i)


		# This generates sinusoidial motion.

		code = 'VM {0}N;'         # VM {axis}N; = N indicates vector mode for a single real axis
		code += 'VA {1};'         # Vector Acceleration
		code += 'VD {1};'         # And decelleration
		code += 'VS {2};'         # Define vector speed of
		code += 'CR {3}, 0, {4};' # Vector mode specifies a 2-dimensional arc segment. CR {encoder tics to traverse}, {start angle}, {x/360 = number of complete cycles to traverse)
		code += 'VE;'             # End vector specification sequence
		code += 'BG S'            # Begin vector motion move
		# Note. Trailing semocolon is inserted automatically

		code = code.format(axis_letter,
						   int(max_accel), 							# Max accel and deccel
						   int(2*math.pi*encoderTics*frequency),	# Vector speed
						   int(encoderTics/2.0),					# Circular Segment. Input is in diameter, so / 2
						   int(360*cycles))
		self.flushSocketRecvBuf(self.con)
		for line in code.split(';'):
			line = line.rstrip().lstrip() 		# Clean up the tabs from the line since it's got newlines in it
			self.sendOnly(line+';')
			time.sleep(0.03)
		print "Receiving:", self.receiveOnly(self.con)

	def homeAxis(self, axis):

		command = "#HOME%s" % self.__axisIntToLetter(axis)
		self.executeFunction(command)

	def executeFunction(self, func):

		if func[0] != "#":						# if the function name is not prefixed with a "#", add one.
			func = "#" + func

		command = "XQ %s" % func


		responseStr = self.sendAndReceive( command )

		return responseStr

	def resetGalil(self, download = True):
				#We re-download the galilcode on reset, since resetting clears the function memory
				# if you don't want to re-download the functions, pass download = false

		command = "RS"

		self.sendOnly( command )

		time.sleep(0.5)
		if download:
			self.__downloadFunctions()



	def close(self, motorsOff = True):		#Optionally turn the motors off, and then try to close the socket
										# connection gracefully

		if self.running:			# This can be called both manually and by __del__
			self.running = False 	# Therefore, we look at self.running to determine if we need to stop the threads
			for thread in self.threads:			# Stop the various threads
				if thread:
					print "Stopping thread:", thread
					thread.join()

			if self.doUDPFileLog:
				self.fileH.close()


		try:							# Since this is called both manually and by the destructor, we have to simply catch and ignore errors here.
										# otherwise, there are errors arising from the fact that it winds up trying to close a closed connection.
			if self.con:
				print "Closing Connection"

				if motorsOff:
					self.sendOnly("MO")


				self.sendOnly("IHT=-3;")	# Close ALL THE (other) SOCKETS
				self.con.shutdown(socket.SHUT_RDWR)
				self.con.close()
				self.con = None
		except (TypeError, socket.error):
			pass




def test():
	print "RUNNING GALIL CONNECTION TESTS"

	if len(sys.argv) == 2:
		galilIp = sys.argv[1]
		print("Connecting to galil at ip '%s'" % galilIp)
	else:
		galilIp = "10.1.2.250"


	gInt = GalilInterface(ip = galilIp, poll = False, resetGalil = True, unsol = True, download = False, debug=True, dr=True)


	time.sleep(1)
	print "done"
	#gInt.motorOn()
	#gInt.executeFunction("MAIN")

	try:
		while 1:
			time.sleep(10)
	except KeyboardInterrupt:
		print "Exiting"

	gInt.close(False)
	sys.exit(0)


if __name__ == "__main__":
	test()
