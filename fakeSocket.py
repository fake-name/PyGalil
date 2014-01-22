
class create_connection:
	
	def __init__(self, *args, **kwargs):
		pass
	
	def settimeout(self, timeoutError):
		pass

	def recv(self, bytes):
		return ":"

	def shutdown(self, args):
		pass

	def close(self):
		pass

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

class socket():
	def __init__(self, *args, **kwargs):
		pass
	def bind(self, wat):
		pass
	def sendto(self, hurr, durr):
		pass

	def settimeout(self, blargh):
		pass

SHUT_RDWR = "wat"
AF_INET = "lol"
SOCK_DGRAM = "derp"
IPPROTO_UDP = "herp"