 #!C:\Python26


import numpy as np
import pandas as pd 	# Faster csv import

import matplotlib
matplotlib.use("WxAgg")

import matplotlib.pyplot as pplt

def doThisThing():

	print "loading data"
	dat = np.genfromtxt("./posvelDR.1.txt", delimiter=",")

	#dat = np.array(pd.read_csv("./posvelDR.1.txt", delimiter=","))

	print "Loaded"

	
	#print dat[...,0]
	#print dat[...,1]
	#print dat[...,4]

	#Add space between subplots to make them look nicer

	numPlots = 1

	ts = dat[...,4]

	'''

	tmp = []

	for x in xrange(dat.shape[0]):
		tmpS = bin(int(dat[x,4]))
		preFix, val = tmpS[:2], tmpS[2:]
		#out = preFix + ("0" * (8-len(val))) + val
		#print out
		tmp.append(int(dat[x,4]))

	'''
	print ts.shape[0]

	print "Processing out spikes"
	
	oldVal = 0
	oldVal = ts[0]

	for x in xrange(1, ts.shape[0]-1):
		if ts[x] > 500000000:
			print x, ts[x]
			ts[x] = np.NaN

		if oldVal - ts[x] > 1000:
			#print "Found step!", x, oldVal, ts[x]
			ts[x] = ts[x] + 67929088
		oldVal = ts[x]

		# Filter single point spikes
		if ((ts[x] - ts[x-1]) > 20)  and ((ts[x] - ts[x-1]) > 20):
			ts[x] = np.NaN

	print "Done. Plotting"


	mainWin = pplt.figure()
	mainWin.subplots_adjust(hspace=.4, wspace=.4)

	plot2 = mainWin.add_subplot(numPlots, 1, 1)
	plot2.plot(ts[1:-2])

	print "Plotting"
	pplt.show()
	print "Done"

	


if __name__ == "__main__":

	print doThisThing()