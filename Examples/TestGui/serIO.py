 #!C:\Python26


import sys


import queVars
import time

import galilInterface

import sys

import time

def mainLoop():

	while 1:

		if not queVars.Qout.empty():
			temp = queVars.Qout.get()
			print "Threading Message:",  temp, " ",




			if "Shutdown" in temp:
				print "Serial Thread Exiting"
				sys.exit(0)



			if "moveRelative" in temp:
				axis, deltaPosition = temp["moveRelative"]
				queVars.gInt.moveRelative(axis, deltaPosition)


			if "moveAbsolute" in temp:
				axis, position = temp["moveAbsolute"]
				queVars.gInt.moveAbsolute(axis, position)


			if "setMoveSpeed" in temp:
				axis, velocity = temp["setMoveSpeed"]
				queVars.gInt.setMoveSpeed(axis, velocity)

			if "moveAtSpeed" in temp:
				axis, velocity = temp["moveAtSpeed"]
				queVars.gInt.moveAtSpeed(axis, velocity)


			if "beginMotion" in temp:
				axis = temp["beginMotion"]
				queVars.gInt.beginMotion(axis)

			if "endMotion" in temp:
				axis = temp["endMotion"]
				queVars.gInt.endMotion(axis)

			if "inMotion" in temp:
				axis = temp["inMotion"]
				queVars.gInt.inMotion(axis)

			if "motorOn" in temp:
				axis = temp["motorOn"]
				queVars.gInt.motorOn(axis)

			if "motorOff" in temp:
				axis = temp["motorOff"]
				queVars.gInt.motorOff(axis)

			if "getPositionStatus" in temp:
				print queVars.gInt.getPosition()

			if "getVelocityStatus" in temp:
				print queVars.gInt.getVelocity()



			if "reboot" in temp:
				queVars.gInt.resetGalil()





			if "homeAxis" in temp:
				queVars.gInt.homeAxis(temp["homeAxis"])




		#queVars.gInt.moveRelative(0)
		time.sleep(0.030)
