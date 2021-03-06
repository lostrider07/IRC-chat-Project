import os
import sys
import time
import ast
import _thread
from _thread import *
import socket
from socket import *
import struct
from struct import *
#import simplecrypt
#from simplecrypt import encrypt, decrypt

flag = True
subscription_list = []
file_count = 0
decryption_key = ''
uid = ''

def exp_handle(sock):
	print('The IRC Server is not responding. Try reconnecting after some time')
	quit_routine(sock)
	exit()

####################################################################################################

def error(code):
	if code == 'NE001':
		return 'IrcNameError001: Username cannot have any spaces\nTry a different username'
	elif code == 'NE002':
		return 'IrcNameError002: Username must have at least one character'
	elif code == 'NE003':
		return 'IrcNameError003: Username can have maximum length of 20'
	elif code == 'NE004':
		return 'IrcNameError004: Room name can have maximum length of 10'
	elif code == 'AE001':
		return 'IrcArgumentError001: Too many arguments given'
	elif code == 'AE002':
		return 'IrcArgumentError002: Too few arguments given'
	elif code == "AE004":
		return 'IrcArgumentError004: Invalid value of argument/s for given command'
	elif code == 'ME001':
		return 'IrcMessageError001: Unauthorized message\nYou do not have the authorization for posting this message'
	elif code == 'ME002':
		return 'IrcMessageError002: Message size bigger than permitted'
	elif code == 'CE001':
		return 'IrcCommandError001: Invalid command. IRC does not recognize this command. Please enter a valid command.'
	elif code == 'CE002':
		return 'IrcCommandError002: This command can only be executed once for given set of arguments'
	elif code == 'IOE01':
		return 'IrcIOError01: IRC could not open file\nPlease check the file name and make sure it is in your current working directory'

####################################################################################################

def initializer(handler_socket):
	global uid
	print(handler_socket.recv(64).decode('ascii'))
	uid_status = 'unregistered'
	while uid_status == 'unregistered':
		uid = input('Choose a username: ')
		if len(uid.split(' ')) > 1:
			print(error('NE001'))
		elif len(uid.split(' ')) < 1:
			print(error('NE002'))
		elif len(uid.split(' ')) == 1:
			if len(uid) > 20:
				print(error('NE003'))
			else:
				try:
					handler_socket.send(bytes('register '+uid, 'utf-8'))
					uid_status = handler_socket.recv(12).decode('ascii')
					print(handler_socket.recv(128).decode('ascii'))
				except ConnectionError:
			#	except OSError:
					exp_handle(handler_socket)
	print('\nType in \"help\" any time for command help\n')
	server_handler(handler_socket, uid)

####################################################################################################

def quit_routine(sock):
	sock.close()
	global flag
	flag = False
	return

def message_routine(handler_socket, command):
	header = ' '.join(command[0:2])
	message = ' '.join(command[2:])
	if len(message) > 448:
		print(error('ME002'))
		if input('\nSend anyway ? Y/N') == (N or n):
			return
	try:
		handler_socket.send(bytes(header, 'utf-8'))
		handler_socket.send(bytes(message, 'utf-8'))
	except ConnectionError:
#	except OSError:
		exp_handle(handler_socket)
	else:
		return

def list_routine(handler_socket, command):
	try:
		handler_socket.send(bytes(command, 'utf-8'))
		buff = handler_socket.recv(4)
	#	buff = handler_socket.recv(8)
	except ConnectionError:
#	except OSError:
		exp_handle(handler_socket)
	else:
		size = unpack('L', buff)[0]
	try:
		string = handler_socket.recv(size).decode('ascii')
	except ConnectionError:
#	except OSError:
		exp_handle(handler_socket)
	else:
		List = ast.literal_eval(string)
		print('\n\t'+command.split(' ')[1]+': ', str(List)[1:-1])
	return

def transfer_routine(handler_socket, command):
	try:
		fh = open(command[1], 'rb')
		File = fh.read()
		fh.close()
	except IOError:
		print(error('IOE01'))
	else:
		try:
			handler_socket.send(bytes(' '.join(command), 'utf-8'))
			trans_status1 = handler_socket.recv(10).decode('ascii')
			if trans_status1 == 'Failed':
				return
			key = input(handler_socket.recv(64).decode('ascii'))
			handler_socket.send(bytes(key, 'utf-8'))
			trans_status2 = handler_socket.recv(10).decode('ascii')
		except ConnectionError:
	#	except OSError:
			exp_handle(handler_socket)
		else:
			if trans_status2 == 'Success':
				print('Key Verification Successful: Preparing to send file\n')
				handler_socket.send(pack('L', sys.getsizeof(File)))
				handler_socket.send(File)
				print('File In Transit...\n')
			else:
				print('Key Verification Failed: Not authorized to send file to '+command[2])
	return

def secure_routine(handler_socket, command):
	cryptext = encrypt(command[2], ' '.join(command[3:]))
	try:
		handler_socket.send(bytes(' '.join(command[0:2]), 'utf-8'))
		handler_socket.send(pack('L', sys.getsizeof(cryptext)))
		handler_socket.send(cryptext)
	except ConnectionError:
#	except OSError:
		exp_handle(handler_socket)
	return

####################################################################################################

def help():
	print("\nTo join a room:\n	join-room					Usage: 	join-room <room-name>\n\nTo leave a room:\n	exit-room					Usage: 	exit-room <room-name>\n\nTo send message to a room:\n	chat-room					Usage: 	chat-room <room-name> <your message here>\n\nTo send a private message to another user:\n	pvt-msg						Usage: 	pvt-msg <recipient-name> <your message here>\n\nTo send a secure message to another user:\n	secure-msg					Usage:	secure-msg <recipient-name> <key> <your message here>\n\nTo enter decryption key:\n	decryption-key					Usage:	decryption-key <key>\n\nTo list available rooms, active users, or members of a room:\n	list						Usage: 	list rooms / list users / list members <room-name>\n\nTo list the rooms user is subscribed to:\n	my-rooms					Usage: 	my-rooms\n\nTo set the file transfer key for receiving files:\n	set-file-transfer-key				Usage: 	set-file-transfer-key <key>\n\nTo send a file to another user:\n	send-file					Usage: 	send-file <file-name.extension> <recipient-name>\n\nTo send a message to all active users:\n	broadcast					Usage:	broadcast all <your message here>\n\nTo quit IRC:\n	quit-irc					Usage: 	quit-irc\n\nTo view this message:\n	help						Usage:	help")

####################################################################################################

def server_handler(handler_socket, uid):
	while True:
		command = input('%s:\n' %(uid))
		cmd_split = command.split(' ')
		intent = cmd_split[0]
		if intent == 'quit-irc':
			if len(cmd_split) > 1:
				print(error('AE001')+'\nUsage: quit-irc')
			else:
				try:
					handler_socket.send(bytes(command, 'utf-8'))
				except ConnectionError:
			#	except OSError:
					exp_handle(handler_socket)
				else:
					quit_routine(handler_socket)
				finally:
					sys.exit()

		elif intent == 'join-room':
			if len(cmd_split) < 2 or len(cmd_split[1].strip()) == 0:
				print(error('AE002')+'\nUsage: join-room <room-name>')
			elif len(cmd_split) > 2:
				print(error('AE001')+'\nUsage: join-room <room-name>')
			elif len(cmd_split) == 2:
				if len(cmd_split[1]) > 10:
					print(error('NE004'))
				else:
					if cmd_split[1] not in subscription_list:
						try:
							handler_socket.send(bytes(command, 'utf-8'))
							print(handler_socket.recv(64).decode('ascii'))
						except ConnectionError:
					#	except OSError:
							exp_handle(handler_socket)
						else:
							subscription_list.append(cmd_split[1])
					else:
						print(error('CE002'))

		elif intent == 'exit-room':
			if len(cmd_split) < 2:
				print(error('AE002')+'\nUsage: exit-room <room-name>')
			elif len(cmd_split) > 2:
				print(error('AE001')+'\nUsage: exit-room <room-name>')
			elif len(cmd_split) == 2:
				if cmd_split[1] in subscription_list:
					subscription_list.remove(cmd_split[1])
					try:
						handler_socket.send(bytes(command, 'utf-8'))
					except ConnectionError:
				#	except OSError:
						exp_handle(handler_socket)
				else:
					print(error("AE004"))

		elif intent == 'chat-room':
			if len(cmd_split) < 3:
				print(error('AE002')+'\nUsage: chat-room <room-name> <your message here>')
			else:
				if cmd_split[1] in subscription_list:
					message_routine(handler_socket, cmd_split)
				else:
					print(error('ME001')+'\nPlease join the room to send messages')

		elif intent == 'pvt-msg':
			if len(cmd_split) < 3:
				print(error('AE002')+'\nUsage: pvt-msg <recipient-name> <your message here>')
			else:
				message_routine(handler_socket, cmd_split)

		elif intent == 'secure-msg':
			if len(cmd_split) < 4:
				print(error('AE002')+'\nUsage: secure-msg <recipient-name> <key> <your message here>')
			else:
				message = ' '.join(cmd_split[3:])
				print('\nSecure Messaging is only available on linux servers. The secure message code has been commented out so as to run the project on Windows host. To test secure messaging on linux, the required code could be un-commented as directed at the top of the source code.\n')
			#	secure_routine(handler_socket, cmd_split)

		elif intent == 'list':
			if len(cmd_split) > 3:
				print(error('AE001') + '\nUsage: list rooms/users OR list members <room-name>')
			elif len(cmd_split) < 2:
				print(error('AE002') + '\nUsage: list rooms/users OR list members <room-name>')
			elif cmd_split[1] == 'members':
				if len(cmd_split) < 3:
					print(error('AE002') + '\nUsage: list members <room-name>')
				else:
					list_routine(handler_socket, command)
			elif cmd_split[1] == 'rooms' or 'users':
				if len(cmd_split) > 2:
					print(error('AE001') + '\nUsage: list rooms/users')
				else:
					list_routine(handler_socket, command)
			else:
				print(error('AE004'))

		elif intent == 'my-rooms':
			if len(cmd_split) > 1:
				print(error('AE001') + '\nUsage: my-rooms')
			else:
				print('\n\tMy Rooms: ', str(subscription_list)[1:-1])

		elif intent == 'set-file-transfer-key':
			if len(cmd_split) < 2:
				print(error('AE002') + '\nUsage: set-file-transfer-key <key>')
			else:
				if len(' '.join(cmd_split[1:])) > 10:
					print('The key could at most be 10 characters long\nTry again with a different key')
				else:
					try:
						handler_socket.send(bytes(command, 'utf-8'))
						print(handler_socket.recv(64).decode('ascii'))
					except ConnectionError:
				#	except OSError:
						exp_handle(handler_socket)

		elif intent == 'send-file':
			if len(cmd_split) > 3:
				print(error('AE001') + '\nUsage: send-file <file-name.extension> <recipient-name>')
			elif len(cmd_split) < 3:
				print(error('AE002') + '\nUsage: send-file <file-name.extension> <recipient-name>')
			else:
				transfer_routine(handler_socket, cmd_split)

		elif intent == 'broadcast':
			if len(cmd_split) < 3:
				print(error('AE002') + '\nUsage: broadcast all <your message here>')
			else:
				message_routine(handler_socket, cmd_split)

		elif intent == 'decryption-key':
			global decryption_key
			decryption_key = cmd_split[1]

		elif intent == 'help':
			if len(cmd_split) > 1:
				print(error('AE001') + '\nUsage: help')
			else:
				help()
		else:
			print(error('CE001'))

####################################################################################################

def message_handler(message_socket):
	global flag
	global decryption_key
	global uid
	while flag:
		connection_m, address_m = message_socket.accept()
		try:
			buff = connection_m.recv(512).decode('ascii')
			if buff.split(' ')[0] == 'secure-msg':
				sender = buff.split(' ')[1]
				connection_m.send(b'ok')
				size = unpack('L', connection_m.recv(4))[0]
			#	size = unpack('L', connection_m.recv(8))[0]
				sec_buff = connection_m.recv(size)
				print('Received secure message from '+sender+'. Enter decryption key to view message')
				while not decryption_key:
					time.sleep(2)
				message = decrypt(decryption_key, sec_buff).decode('ascii')
				print(sender+' says: '+message+'\n'+uid+':\n')
				decryption_key = ''
			else:
				print(buff)

		except ConnectionError:
	#	except OSError:
			exp_handle(message_socket)
		else:
			connection_m.close()
	_thread.exit()

####################################################################################################

def file_handler(file_socket):
	global flag
	while flag:
		connection_f, address_f = file_socket.accept()
		try:
			head_size = unpack('L', connection_f.recv(4))[0]
		#	head_size = unpack('L', connection_f.recv(8))[0]
			header = connection_f.recv(head_size).decode('ascii')
			sender, ext = tuple(header.split(' '))
			file_size = unpack('L', connection_f.recv(4))[0]
		#	file_size = unpack('L', connection_f.recv(8))[0]
			File = connection_f.recv(file_size)
		except ConnectionError:
	#	except OSError:
			exp_handle(file_socket)
		else:
			global file_count
			file_name = 'file'+str(file_count)+'.'+ext
			fh = open(file_name, 'w+b')
			fh.write(File)
			fh.close()
			file_count += 1
			global uid
			print('You received file '+file_name+' from '+sender+'\n'+uid+':')
			connection_f.close()
	_thread.exit()

####################################################################################################

server_socket = socket()
try:
	server_socket.connect((gethostname(), 1234))
	buff = server_socket.recv(4)
#	buff = server_socket.recv(8)
except ConnectionError:
#except OSError:
	exp_handle(server_socket)

port_h = unpack('L', buff)[0]
server_socket.close()

handler_socket = socket()
try:
	handler_socket.connect((gethostname(), port_h))
except ConnectionError:
#except OSError:
	exp_handle(handler_socket)

port_m = port_h + 1
port_f = port_h + 2

message_socket = socket()
try:
	message_socket.bind((gethostname(), port_m))
	message_socket.listen()
except ConnectionError:
#except OSError:
	exp_handle(handler_socket)

file_socket = socket()
try:
	file_socket.bind((gethostname(), port_f))
	file_socket.listen()
except ConnectionError:
#except OSError:
	exp_handle(handler_socket)

start_new_thread(message_handler, (message_socket,))
start_new_thread(file_handler, (file_socket,))
initializer(handler_socket)