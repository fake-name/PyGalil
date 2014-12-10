try:
	import pycallgraph
	pycallgraph.start_trace()
except:
	pass



import sys
sys.path.append("../../")


import queVars
import ipCheck


ipCheckWin = ipCheck.IpChecker(0)
ipCheckWin.MainLoop()


import galilInterface

import GUIInit						#GUI Handling
import serIO
import threading
#def __init__(self, ip, port = 23, fakeGalil = False, poll = False, resetGalil = False):


queVars.gInt = galilInterface.GalilInterface(ip=queVars.galilIP, poll=False, resetGalil=False)

queVars.serThread = threading.Thread(target = serIO.mainLoop, name = "serThread")
queVars.serThread.start()

#import time
#time.sleep(1)

mainWin = GUIInit.MyApp(0)
mainWin.MainLoop()
