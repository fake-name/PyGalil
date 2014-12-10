#!C:/Python26

import Queue

#	Interthread Comms
#	QOut - GUI -> SerIO
#	Qin  - SerIO -> GUI
#

serThread = None

galilIP		=	"192.168.1.241"
fakeGalil	=	False


Qin		=	Queue.Queue()
Qout		=	Queue.Queue()
