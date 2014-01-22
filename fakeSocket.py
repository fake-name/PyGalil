# To change this template, choose Tools | Templates
# and open the template in the editor.


class create_connection:
	
	def __init__(self, *args, **kwargs):
		pass
	
	def settimeout(self, timeout):
		pass

	def recv(self, bytes):
		return ":"


	def sendall(self, data):
		pass
		
	def __getattr__(self, name):
		def method(*args):
			print("tried to handle unknown method " + name)
			if args:
				print("it had arguments: " + str(args))

class timeout(StandardError):
	def __init__(self, errno, address):
		pass


class error(StandardError):
	def __init__(self, errno, address):
		pass
