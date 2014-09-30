'''

Galil Data-Record block structures:

 UB = Unsigned byte			# 1 Byte
 UW = Unsigned Word			# 2 Bytes
 SW = Signed Word			# 2 Bytes
 SL = Signed Long Word		# 4 Bytes

UB	1 st byte of header				Header
UB	2 nd byte of header				Header
UB	3 rd byte of header				Header
UB	4 rth byte of header			Header

UW	sample number					I block 		2 Bytes
UB	general input 0					I block 		1 Byte
UB	general input 1					I block 		1 Byte
UB	general input 2					I block 		1 Byte
UB	general input 3					I block 		1 Byte
UB	general input 4					I block 		1 Byte
UB	general input 5					I block 		1 Byte
UB	general input 6					I block 		1 Byte
UB	general input 7					I block 		1 Byte
UB	general input 8					I block 		1 Byte
UB	general input 9					I block 		1 Byte
UB	general output 0				I block 		1 Byte
UB	general output 1				I block 		1 Byte
UB	general output 2				I block 		1 Byte
UB	general output 3				I block 		1 Byte
UB	general output 4				I block 		1 Byte
UB	general output 5				I block 		1 Byte
UB	general output 6				I block 		1 Byte
UB	general output 7				I block 		1 Byte
UB	general output 8				I block 		1 Byte
UB	general output 9				I block 		1 Byte
UB	error code						I block 		1 Byte
UB	general status					I block 		1 Byte

24 Bytes total for I Block
str = <HBBBBBBBBBBBBBBBBBBBBBB


UW	segment count of coordinated move for S plane				S block		2 Bytes
UW	coordinated move status for S plane							S block		2 Bytes
SL	distance traveled in coordinated move for S plane			S block		4 Bytes

UW	segment count of coordinated move for T plane				T block		2 Bytes
UW	coordinated move status for T plane							T block		2 Bytes
SL	distance traveled in coordinated move for T plane			T block		4 Bytes

8 Bytes per block for S and T blocks
str = <HHl


UW	a axis status					A block		2 Bytes
UB	a axis switches					A block		1 Byte
UB	a axis stop code				A block		1 Byte
SL	a axis reference position		A block		4 Bytes
SL	a axis motor position			A block		4 Bytes
SL	a axis position error			A block		4 Bytes
SL	a axis auxiliary position		A block		4 Bytes
SL	a axis velocity					A block		4 Bytes
SW	a axis torque					A block		2 Bytes
SW	a axis analog					A block		2 Bytes

28 bytes per block (?)
str = <HBBlllllhh


UW	b axis status					B block
UB	b axis switches					B block
UB	b axis stop code				B block
SL	b axis reference position		B block
SL	b axis motor position			B block
SL	b axis position error			B block
SL	b axis auxiliary position		B block
SL	b axis velocity					B block
SW	b axis torque					B block
SW	b axis analog					B block

UW	c axis status					C block
UB	c axis switches					C block
UB	c axis stop code				C block
SL	c axis reference position		C block
SL	c axis motor position			C block
SL	c axis position error			C block
SL	c axis auxiliary position		C block
SL	c axis velocity					C block
SW	c axis torque					C block
SW	c axis analog					C block

UW	d axis status					D block
UB	d axis switches					D block
UB	d axis stop code				D block
SL	d axis reference position		D block
SL	d axis motor position			D block
SL	d axis position error			D block
SL	d axis auxiliary position		D block
SL	d axis velocity					D block
SW	d axis torque					D block
SW	d axis analog					D block

UW	e axis status					E block
UB	e axis switches					E block
UB	e axis stop code				E block
SL	e axis reference position		E block
SL	e axis motor position			E block
SL	e axis position error			E block
SL	e axis auxiliary position		E block
SL	e axis velocity					E block
SW	e axis torque					E block
SW	e axis analog					E block

UW	f axis status					F block
UB	f axis switches					F block
UB	f axis stop code				F block
SL	f axis reference position		F block
SL	f axis motor position			F block
SL	f axis position error			F block
SL	f axis auxiliary position		F block
SL	f axis velocity					F block
SW	f axis torque					F block
SW	f axis analog					F block

UW	g axis status					G block
UB	g axis switches					G block
UB	g axis stop code				G block
SL	g axis reference position		G block
SL	g axis motor position			G block
SL	g axis position error			G block
SL	g axis auxiliary position		G block
SL	g axis velocity					G block
SW	g axis torque					G block
SW	g axis analog					G block

UW	h axis status					H block
UB	h axis switches					H block
UB	h axis stop code				H block
SL	h axis reference position		H block
SL	h axis motor position			H block
SL	h axis position error			H block
SL	h axis auxiliary position		H block
SL	h axis velocity					H block
SW	h axis torque					H block
SW	h axis analog					H block
'''

import struct
from bitstring import ConstBitStream

I_BLK_PARSE_STR 	= "<H22B"
I_BLK_SIZE 		= struct.calcsize(I_BLK_PARSE_STR)

ST_BLK_PARSE_STR	= "<HHl"
ST_BLK_SIZE 		= struct.calcsize(ST_BLK_PARSE_STR)

AX_BLK_PARSE_STR	= "<xxBBlllllhh"
AX_BLK_SIZE 		= struct.calcsize(AX_BLK_PARSE_STR)


def bitflip(intIn):
	"""Flips the bits of intIn."""
	ret = 0
	for x in range(8):
		if intIn & _BV(x):
			ret |= _BV(7-x)

	return ret


# Common mnemomic for specifying a bit-value. Stolen from AVR libc
def _BV(inVal):
	return 1<<inVal

def axis(n):
	return chr(65+n)

def parseIBlock(iBlkStr):
	ret = dict()
	if len(iBlkStr) != I_BLK_SIZE:
		raise ValueError("Invalid passed string length")

	#This is going to need considerable rework in the near future to properly decode the data in the GI bytes anyways (it's packed
	# in the hardware). I need to extract the unpacking from the hardware first (blurgh).
	keys = ["SN",
	"GI0", "GI1", "GI2", "GI3", "GI4",
	"GI5", "GI6", "GI7", "GI8", "GI9",
	"GO0", "GO1", "GO2", "GO3", "GO4",
	"GO5", "GO6", "GO7", "GO8", "GO9",
	"EC", "GS"]

	vals = struct.unpack(I_BLK_PARSE_STR, iBlkStr)

	# Build dict of {key:value}
	ret = dict(zip(keys, vals))

	# GI8 is reversed in the hardware. We need to flip it back to make it valid
	ret["GI8"] = bitflip(ret["GI8"])

	return ret

def parseAxisBlock(axBlkStr):
	ret = dict()
	if len(axBlkStr) != AX_BLK_SIZE:
		raise ValueError("Invalid passed string length")

	keys = ["status", "switches", "stopCode", "refPos", "motorPos",
	"posError", "auxPos", "vel", "torque", "analog"]

	statusKeys = ["moving", "motionMode1", "motionMode1", "findingEdge",
				  "homing", "homeP1Done", "homeP2Done", "coordMotion",
				  "movingNeg", "contourMode", "slewingMode", "stopping",
				  "finalDecel", "latchArmed", "offOnErrArmed", "motorOff"]

	# The fucking galil is little endian, so [:2] splits off the segment of the string we want, and [::-1] reverses it
	statusBs = ConstBitStream(bytes=axBlkStr[:2][::-1])

	# Status is 16 boolean values packed into a uint_16
	statusVals = statusBs.readlist(["uint:1"]*16)

	# zip flags and names into dict
	zipped = zip(statusKeys, statusVals)

	vals = [dict(zipped)]
	vals.extend(struct.unpack(AX_BLK_PARSE_STR, axBlkStr))

	ret = dict(zip(keys, vals))

	return ret


def parseDataRecord(drString):
	if len(drString) < 4:
		print "Invalid data record"
		return False

	flags, drLen = struct.unpack("<HH", drString[:4])
	if len(drString) != drLen:
		print "Invalid DR length"
		return False

	# Byte swap the flags (cause it's sent big-endian?)
	# This doesn't match the docs, but it seem to match what I'm actually receiving.
	# Done with integer math because fuck you
	flags = (flags / 2**8) + ((flags % 2**8) * 2**8)

	# first 4 bytes are the length and flags, which are checked above.
	# We therefore start with an offset of 4 bytes to skip them for extracting actual contents.
	offsetInDat = 4

	# Blocks transmitted in the order:
	# I S T A B C D E F G H
	ret = {}
	if flags & _BV(10):		# I Block (General Status and IO) is present

		ret["I"] = parseIBlock(drString[offsetInDat:(offsetInDat+I_BLK_SIZE)])
		offsetInDat += I_BLK_SIZE

	if flags & _BV(8): 		# S Block (segmented moves in S-plane)
		offsetInDat += ST_BLK_SIZE

	if flags & _BV(9): 		# T Block (segmented moves in T-plane)
		offsetInDat += ST_BLK_SIZE

	for i in range(8):
		if flags & _BV(i): 	# Axis status block is present
			ret[axis(i)] = parseAxisBlock(drString[offsetInDat:(offsetInDat+AX_BLK_SIZE)])
			offsetInDat += AX_BLK_SIZE

	ret['lock'], ret['mstow'] = extractMsTow(ret)


	curTOW = getMsTOWwMasking()
	ret['towerr'] = curTOW - ret['mstow']

	return ret

def extractMsTow(dr):
	timeStamp = ((dr["I"]["GI8"] & 0x1F) * 2**24) + (dr["I"]["GI9"] * 2**16) + (dr["I"]["GI5"] * 2**8) + (dr["I"]["GI4"])

	# The top two bits of GI8 are bit 17 and 18 of the elevation encoder
	# the third bit is the GPS-lock status.
	# The rest are the top bits of the time-stamp
	lockStatus = dr["I"]["GI8"] & (1 << 5)

	return lockStatus, timeStamp


import datetime

def getMsTOWwMasking():		# Get the current millisecond time of week
	d = datetime.datetime.utcnow().toordinal()
	last = d# - 6
	sunday = last - (last % 7)
	startOfWeek = datetime.datetime.fromordinal(sunday)
	#print startOfWeek, type(startOfWeek)
	delta = datetime.datetime.utcnow() - startOfWeek

	return int(delta.total_seconds()*1000) & 0x1FFFFFFF



if __name__ == "__main__":
	print "DERP"
	#print getMsTOWwMasking()

	print bitflip(1)
	print bitflip(2)
	print bitflip(4)
	print bitflip(8)
	print bitflip(16)
	print bitflip(32)
	print bitflip(64)
	print bitflip(128)
