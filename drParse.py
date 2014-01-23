'''

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
from bitstring import BitStream, ConstBitStream

iBlkParseStr 	= "<H22B"
iBlkSize 		= struct.calcsize(iBlkParseStr)

stBlkParseStr	= "<HHl"
stBlkSize 		= struct.calcsize(stBlkParseStr)

axBlkParseStr	= "<HBBlllllhh"
axBlkSize 		= struct.calcsize(axBlkParseStr)

def bitflip(intIn):
	"""Flips the bits of intIn."""
	out = BitStream("uint:8=%d" % intIn)
	out.reverse()
	return out.int

def _BV(inVal):
	return 1<<inVal
	
def axis(n):
	return chr(65+axis)

def parseIBlock(iBlkStr):
	ret = dict()
	if len(iBlkStr) != iBlkSize:
		raise ValueError("Invalid passed string length")
	
	# holy "one" liner unpacking, batman!
	ret["SN"], \
	ret["GI0"], ret["GI1"], ret["GI2"], ret["GI3"], ret["GI4"], \
	ret["GI5"], ret["GI6"], ret["GI7"], ret["GI8"], ret["GI9"], \
	ret["GO0"], ret["GO1"], ret["GO2"], ret["GO3"], ret["GO4"], \
	ret["GO5"], ret["GO6"], ret["GO7"], ret["GO8"], ret["GO9"],\
	ret["EC"], ret["GS"] = struct.unpack(iBlkParseStr, iBlkStr)

	ret["GI8"] = bitflip(ret["GI8"])	# GI8 is reversed in the hardware. We need to flip it back to
										# make it valid
	return ret

def parseAxisBlock(axBlkStr):
	ret = dict()
	if len(axBlkStr) != axBlkSize:
		raise ValueError("Invalid passed string length")
	ret["status"], ret["switches"], ret["stopCode"], ret["refPos"], ret["motorPos"], \
	ret["posError"], ret["auxPos"], ret["vel"], ret["torque"], ret["analog"] = struct.unpack(axBlkParseStr, axBlkStr)
	return ret


def parseDataRecord(drString):
	if len(drString) < 4:
		print "Invalid data record"
		return 

	flags, drLen = struct.unpack("<HH", drString[:4])
	if len(drString) != drLen:
		print "Invalid DR length"
		return

	flags = (flags / 2**8) + ((flags % 2**8) * 2**8) 
	# Byte swap the flags (cause it's sent big-endian?) This doesn't match the docs, but it seem to match what I'm actually receiving.
	# Done with integer math because fuck you

	offsetInDat = 4		# first 4 bytes are the length and flags 

	# Blocks transmitted in the order:
	# I S T A B C D E F G H
	ret = dict()
	if flags & _BV(10):		# I Block (General Status and IO) is present

		ret["I"] = parseIBlock(drString[offsetInDat:(offsetInDat+iBlkSize)])
		offsetInDat += iBlkSize

	if flags & _BV(8): 		# S Block (segmented moves in S-plane)
		offsetInDat += stBlkSize
		
	if flags & _BV(9): 		# T Block (segmented moves in T-plane)
		offsetInDat += stBlkSize
		
	for i in range(8):
		if flags & _BV(i): 	# Axis status block is present
			ret[axis(i)] = parseAxisBlock(drString[offsetInDat:(offsetInDat+axBlkSize)])
			offsetInDat += axBlkSize
			
	return ret


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
	print getMsTOWwMasking()
