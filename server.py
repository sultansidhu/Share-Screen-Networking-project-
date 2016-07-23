#---------------------Imports----------------------#
import pygame
from pygame.locals import *
import sys
import socket
import select
import os
import time
import threading

#-------------------Constants----------------------#

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" %(2,2)										#put the screen in the top right of the screen
pygame.init()																			#initialize parameters in pygame module
	
WHITE = (255,255,255)																	#white colour
SILVER= (192,192,192)																	#silver colour
BLACK = (0,0,0)																			#black colour
TCP_PORT = 1095																			#TCP port (the genreal socket)
IMAGE_PORT = 1637																		#IMAGE port(the image transfer socket)
WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h		#width and height of the screen
CLIENTS_SCREEN = (WIDTH-420,100,320,850)												#size of the 'Online Clients' list\screen
SHARE_WINDOW = (10,10, WIDTH-500, HEIGHT-100)											#the size of the image to presend

#-------------------Global----------------------#

#Open ports:
#os.system("netsh advfirewall firewall add rule name=\"Port 1637 \" dir=in action=allow protocol=TCP localport=1637")	
#os.system("netsh advfirewall firewall add rule name=\"Port 1095\" dir=in action=allow protocol=TCP localport=1095")			

try:

	#TCP socket for getting clients and exit clients.
	TCP_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	TCP_socket.bind(('0.0.0.0',TCP_PORT))
	TCP_socket.listen(5)
	
	#TCP socket for getting images.
	TcpSocketImage = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	TcpSocketImage.bind(('0.0.0.0',IMAGE_PORT))
	TcpSocketImage.listen(5)
	
except socket.error, socketerror:
	print "Error Opening Socket for client, Try Again. The error message:\n"+socketerror[1]
	sys.exit(-1)
	

current_sharing = None											#hold the client socket that currently sharing his screen, the regular socket
current_sending = None											#hold the client socket that currently sharing his screen, the Images socket
is_MouseClicked = False											#boolean that hold the info if server clicked or not
client_list = None												#Clientlist object pointer
share_screen = None												#Share Screen Thread Object pointer
first_enter = True												#sometimes the FULL_PIC request failed in first time, so we will send again.
#-------------------Classes------------------------#

class Client(object):

	'''This Object is the Client that connect to my Program and want to share his screen'''
	
	def __init__(self,username,usersocket):
		'''
		Enter Statement: the constructor get 2 paramaters
		Exit Statement: the constructor init the attributes and create Client object
		'''
		self.__username = username					#string that holds the user name
		self.__usersocket = usersocket				#string that holds the user socket
		
	def getUsername(self):
		'''
		Enter Statement: the function doesn't get parameters
		Exit Statement: the function returns username
		'''
		return self.__username
		
	def getUsersocket(self):
		'''
		Enter Statement: the function doesn't get parameters
		Exit Statement: the function returns the user socket
		'''
		return self.__usersocket
		
	def SetName(self,name):
		'''
		Enter Statement: the function doesn't get Parameters
		Exit Statement: the function set the name of the user to his name+ the value of the paramater
		'''
		self.__username = name
		
		
#----------------------------------	
class Clientlist(object):

	'''This Object is the Client List , which managed all the the list of online clients'''
	
	def __init__(self):
		'''
		Enter Statement: the constructor doesn't get paramaters
		Exit Statement: the constructor create empty list
		'''
		self.__online_clients = []
	
	def add_client(self, newclient):
		'''
		Enter Statement: the function get Client Object
		Exit Statement: the function add to the client list the client object
		'''
		self.__online_clients.append(newclient)

	def getClientByPosition(self,Yposition):
		'''
		Enter Statement: the function get Y position of mouse clicking in Online Clients area
		Exit Statement: the function returns the Client Object in the clicking position
		'''
		
		#check if the position of the clicking is valid (there is a client in this position)
		if Yposition<999 and Yposition>=120 and (Yposition/50)-2 < len(self.__online_clients):
		
			#return the client in the position of the clicking
			return self.__online_clients[(Yposition/50)-2]
		else:
		
			#return None - there is no Client in the position of the clicking
			return None
		
	def remove_client(self,client_socket):
		'''
		Enter Statement: the function gets Client Object
		Exit Statement: the function remove client from the client list
		'''
		client_to_remove = None

		#search for the client with the socket in the paramaters
		for OnlineClient in self.__online_clients:
			if OnlineClient.getUsersocket()==client_socket:
				client_to_remove = OnlineClient
				break
				
		#check if there is a socket in the list (the socket that the function got in the paramaters)
		if client_to_remove != None:
			self.__online_clients.remove(client_to_remove)
	
	def get_clients_names(self):
		'''
		Enter Statement: the function doesn't get parameters
		Exit Statement: the function returns list of all names in clients list
		'''
		
		global client_list
		
		list_of_names = []			#this list will hold all client's names
		
		#For each client, add his name to the list, and return the list of names in the end
		for eachClient in self.__online_clients:
			list_of_names.append(eachClient.getUsername())
			
		return list_of_names
		
	def getClientBySocket(self,ClientSocket):
		'''
		Enter Statement: the function get socket object
		Exit Statement: the function return Client object by his socket
		'''
		client_to_get = None

		#search for the client with the socket in the paramaters
		for OnlineClient in self.__online_clients:
			if OnlineClient.getUsersocket()==ClientSocket:
				client_to_get = OnlineClient
				break
		
		return client_to_get
	
		
#----------------------------------	
	

class ShareScreenThread(threading.Thread):
	''' Object that handle the thread of share screen '''


	def __init__(self,sharing):
		'''
		Enter Statement: the constructor gets boolean
		Exit Statement: the function init ShareScreenThread properties and create an object of this type
		'''
	
		threading.Thread.__init__(self)						#init threading constructor
		self.__sharing_status = sharing						#boolean that hold if there is a share screen process currently				
		self.__kill_thread = False							#boolean that hold true if the Thread needs to be killed
		
	def set_sharing(self,sharing):
		'''
		Enter Statement: the function get sharing status (if someone is sharing or not)
		Exit Statement: the function set the sharing_status by the parameter
		'''
		self.__sharing_status = sharing
		
		
	def kill_thread_sign(self):
		'''
		Enter Statement: the function doesn't get parameter
		Exit Statement: the function set the kill thread boolean to True
		'''
		self.__kill_thread = True	

	def getKillThread(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function return the kill thread status(true or false)
		'''
		return self.__kill_thread
		
		
	def run(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function run the Thread. doesn't return value.
		'''
		global TCP_socket,TcpSocketImage
		
		#as long as the program didn't kill the thread
		while self.__kill_thread == False:
		
			#if some one is sharing
			if self.__sharing_status:
			
				#REQUEST: full pic from the client
				FrameBufferRequest("FULL_PIC")
				
				#gets full image, and check if the image is good enough for displaying it.
				IsSuccess = recvFullFrameBuffer()
				if IsSuccess and EntireImage!=[]:
					display_photo()
				
			else:
				pygame.draw.rect(DISPLAY,WHITE,SHARE_WINDOW)				#clean the window from the last image
			
		try:
			#when the thread is killed , close the sockets.
			TCP_socket.close()
			TcpSocketImage.close()
			pygame.quit()
			sys.exit()
		except:
			print
#----------------------------------	

class SocketsList():

	''' handle the sockets of the clients'''


	def __init__(self):
		'''
		Enter Statement: the constructor doesn't get paramaters
		Exit Statement: the constructor creates to empty lists
		'''
		self.__Open_Clients_General_sockets = []					#list for general sockets (connection, disconnection ...)
		self.__Open_Clients_Image_Sockets = []						#list for sockets to transfer images
		
	def addGeneralSocket(self,usersocket):
		'''
		Enter Statement: the function get a socket object
		Exit Statement: the function add to the __Open_Clients_General_sockets a socket, doesn't return value
		'''
		self.__Open_Clients_General_sockets.append(usersocket)
	
	def addImageSocket(self,usersocket):
		'''
		Enter Statement: the function get a socket object
		Exit Statement: the function add to the __Open_Clients_Image_Sockets a socket, doesn't return value
		'''
		self.__Open_Clients_Image_Sockets.append(usersocket)
		

	def getGeneralSockets(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function return the general sockets list
		'''
		return self.__Open_Clients_General_sockets
		
	def getImageSockets(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function return the Image sockets list
		'''
		return self.__Open_Clients_Image_Sockets
	
#-------------------Functions----------------------#

def window_setup():
	'''
	Enter Statement: the function doesn't get parameters
	Exit Statement: the function set up the window gui of the server, the function returns DisplaySurf
	'''
	DISPLAY = pygame.display.set_mode((WIDTH,HEIGHT),0,32)							#creates the window
	pygame.display.set_caption("Sharing Screens")					#Set title
	DISPLAY.fill(WHITE)												
	pygame.draw.rect(DISPLAY,SILVER,CLIENTS_SCREEN)									#Screen of online clients
	myfont = pygame.font.SysFont("Arial", 30)			
	textSurfaceObj = myfont.render("Online Clients:",1,BLACK)	
	DISPLAY.blit(textSurfaceObj,(WIDTH-420,67))										#display "Clients" title
	return DISPLAY
	
	
def FrameBufferRequest(TransforType):	
	'''
	Enter Statement: the function doesn't get paramaters
	Exit Statement: the function sends a frame buffer request to the client.
	'''
	global current_sharing,first_enter
	
	#wait till the client will be available to listen to me .
	rlist,wlist,xlist = select.select([],[current_sharing.getUsersocket()],[])
	while len(wlist)==0:
		rlist,wlist,xlist = select.select([],[current_sharing.getUsersocket()],[])	
	
	first_enter = True
	#sending request to the client
	TCP_send(current_sharing.getUsersocket(),TransforType)		

	
def recvFullFrameBuffer():
	'''
	Enter Statement: the function doesn't get paramaters
	Exit Statement: the function recieve full image from the client, return true if success and need to be present on screen, else return false.
	'''
	global current_sending,EntireImage,share_screen,TcpSocketImage

	EntireImage = []		#list that holds the image in chunks of 1024
	
	#get the first chunk
	chunk = TCP_get(current_sending)
	
	#as long as we didn't reach to the end of the image
	while not "END" in chunk :
	
		#get another chunk and add to the image list,after checking for memory errors
		#memory error can occur when the packet comes distorted and the 'END' sign not coming up, and the loop can continue for ever,
		#which will fill the memory
		try:
			EntireImage.append(chunk)
		except:
			EntireImage = []
			return False
			
		chunk = TCP_get(current_sending)
		
		#if there is a problem in the connection or if the server fell down or the program closed, we return with False to not present the image
		if chunk == "ERROR" or share_screen.getKillThread():
			EntireImage = []
			return False
			
		#if the server wait to much to the client, we skip the frame
		elif chunk=="timed out":
			EntireImage = []
			return True
	
	#add the last chunk and remove the sign of END of file.
	EntireImage.append(chunk.replace("END",""))
	return True
		
def update_client_list():
	'''
	Enter Statement: the function doesn't get parameters
	Exit Statement: the function update the gui screen with the update client list
	'''
	height = 120														#variable that hold the height of the client text.
	
	pygame.draw.rect(DISPLAY,SILVER,CLIENTS_SCREEN)						#font initialize
	myfont = pygame.font.SysFont("Arial", 15)
	
	#run on the list of the clients that connect to my program
	for any_client in client_list.get_clients_names():
	
		#display the name on the screen
		textSurfaceObj = myfont.render(any_client,1,BLACK)	
		DISPLAY.blit(textSurfaceObj,(WIDTH-400,height))							
		
		#go down 100 to print the next client's name
		height += 50
		
	#update the client list with the new names.
	pygame.display.update()
		
	
def display_photo():
	'''
	Enter Statement: the function doesn't take paramaters
	Exit Statement: the function display screen picture, doesn't return value
	'''
	global EntireImage
	
	try:
	
		#open a file, put the image list that we recieve from the client and present it on the screen.
		fh = open (r"temp.jpg","wb")
		fh.write(("".join(EntireImage)))#.decode('base64'))
		fh.close()
		
		#load the image, and present it on screen
		img = pygame.image.load(r"temp.jpg")
		img =  pygame.transform.scale(img, (SHARE_WINDOW[2], SHARE_WINDOW[3]))
		DISPLAY.blit(img,(SHARE_WINDOW[0],SHARE_WINDOW[1]))
		
	except pygame.error:
		print 
		

def TCP_send(TCP_sock,data):
	'''
	Enter Statement: the function gets string 
	Exit Statement: the function sends the string via the TCP socket, the function doesn't return value
	'''
	global first_enter
	
	try:
		#send the data
		TCP_sock.send(data)
		
	except socket.error, socketerror:
		
		#check if FULL_PIC request failed in the first time, if it does try send again
		if first_enter:
			first_enter = False
			TCP_send(TCP_sock,data)
		
		
	
def TCP_get(TCP_sock,length = 1028):
	'''
	Enter Statement: the function get socket and a default paramater
	Exit Statement: the function get data from TCP socket, return data if success, or else return string with the problem
	'''
	global current_sharing
	
	try:
	
		#check if we got a socket in paramater, if we does, we will use it
		if TCP_sock!= None:
		
			#set max time that i'll wait for information
			TCP_sock.settimeout(1)
			data = TCP_sock.recv(length)
			return data
		else:
			#else, we use the current_sharing socket
			current_sharing.getUsersocket().settimeout(1)
			data = current_sharing.getUsersocket().recv(length)
			return data
			
	except socket.error as e:	
	
		#if this a time out error, send to the recvFullFrameBuffer an "timed out" error so he will skip this image
		if type(e) == socket.timeout:
			return "timed out"
			
		#else this is a connection problem.
		elif TCP_sock!=None:
			DisconnectClient(TCP_sock)
		else:
			DisconnectClient(current_sharing.getUsersocket())
		return "ERROR"
	

	
def DisconnectClient(disClient):
	'''
	Enter Statement: the function doesn't get parameters
	Exit Statement: the function disconnect a client, no return value
	'''
	global client_list, share_screen,socketlist_handler,current_sharing
	
	
	#put in variables the lists, so we will not have to call the functions a lot of times.
	general_sockets = socketlist_handler.getGeneralSockets()
	image_sockets = socketlist_handler.getImageSockets()
	
	ExitClient = client_list.getClientBySocket(disClient)			#get the client that disconnected
	
	#avoid from none pointer exception
	if ExitClient!=None:
	
		#set his name do disconnected name and display his "new" name (example: my name is avi, so when i'll disconnect--> avi - disconnected)
		ExitClient.SetName(ExitClient.getUsername().replace("-Currently Sharing","")+" - Disconnected")
		update_client_list()
	
	#remove the client from the list .
	client_list.remove_client(disClient)							#remove from client list
	
	#check if the socket his in the general_sockets
	if disClient in general_sockets:
	
		#if it is, we will remove his socket from both lists 
		index_of_sharing = general_sockets.index(disClient)
		image_sockets.remove(image_sockets[index_of_sharing])
		general_sockets.remove(disClient)

	#check if the socket his in the image_sockets
	elif disClient in image_sockets:
	
		#if it is, we will remove his socket from both lists
		index_of_sharing = image_sockets.index(disClient)
		general_sockets.remove(general_sockets[index_of_sharing])
		image_sockets.remove(disClient)
		
	#the client disconnected so we stop the sharing screen
	if current_sharing==None:
		share_screen.set_sharing(False)
		
	#if no one is currently sharing, draw white on the last image that was presented
	if not "-Currently Sharing" in ' '.join(client_list.get_clients_names()):
		pygame.draw.rect(DISPLAY,WHITE,SHARE_WINDOW)
	
	#sleep for 2 seconds so the server will see the  "disconnected" name, and update the list.
	time.sleep(2)
	update_client_list()		
						
#-------------------Main----------------------#

#create Objects that I need to the program
client_list = Clientlist()
socketlist_handler = SocketsList()

#creates window for the server
DISPLAY = window_setup()
pygame.display.update()

#start the  share screen thread
share_screen = ShareScreenThread(False)
share_screen.start()

#as long as the game loop is True
GameLoop = True
while GameLoop:

	#iterate over list with the last events of the server
	for event in pygame.event.get():
	
		# Check if pressed quit button
		if event.type==QUIT:
			GameLoop  = False
			break
			
		#check if pressed on mouse button
		if event.type==MOUSEBUTTONUP:
			is_MouseClicked = True			
		else:
			is_MouseClicked = False
			
	#if the server clicked on the Quit button, stop the main loop immediately.
	if GameLoop==False:
		break
		
	rlist,wlist,xlist = select.select([TCP_socket,TcpSocketImage]+socketlist_handler.getGeneralSockets(),[],[],0.1)	
	
	#run on the rlist 
	for each_client in rlist:	
	
		#first, check if this is a new client that want to connect to this program
		if each_client is TCP_socket :
		
			#accept his request, and get his name
			new_sock,addr = TCP_socket.accept()
			name = TCP_get(new_sock,1024)
			
			#create new Client object, add him to the client list
			new_client = Client(name,new_sock)
			client_list.add_client(new_client)
			
			#add his socket to the socket list (general), and display his name on the screen 
			socketlist_handler.addGeneralSocket(new_sock)
			update_client_list()
			
		#when the client connect to my program, he will also want to connect to the TcpSocketImage
		elif each_client is TcpSocketImage:
			
			#accept him and add his socket to the list
			newsock,addr = TcpSocketImage.accept()
			socketlist_handler.addImageSocket(newsock)

		else:
		
			#else, if there is other things that the client sent to me.
			data = TCP_get(each_client,1024)
			
			#check if the client wants to exit the program
			if data == "" and(each_client in socketlist_handler.getGeneralSockets() or each_client in socketlist_handler.getImageSocketsSockets()):
				DisconnectClient(each_client)	
			
					
				
	#check if one of the server events his pressing the mouse button.
	if is_MouseClicked:
	
		#gets Y position of clicking.
		Yposition = pygame.mouse.get_pos()[1]
		
		#gets client from the list by the clicking position
		new_sharing_client = client_list.getClientByPosition(Yposition)
		
		#check if there is a client in the position of clicking
		if new_sharing_client != None :
			
			#check if there is a sharing client currently, if there is , tell him to stop share because the server chose other client .
			if current_sharing != None: 
				TCP_send(current_sharing.getUsersocket(),"STOP")
				prevClient = client_list.getClientBySocket(current_sharing.getUsersocket())
				if prevClient != None:
					prevClient.SetName(prevClient.getUsername().replace("-Currently Sharing",""))				# delete the status of currently sharing
				
			#tell the new client that was chosen by the server, to start share his screen
			TCP_send(new_sharing_client.getUsersocket(),"START")			
		
			#update the current_sharing to the new client, and also the current_sending
			current_sharing = new_sharing_client			
			index_of_sharing = socketlist_handler.getGeneralSockets().index(new_sharing_client.getUsersocket())
			current_sending = socketlist_handler.getImageSockets()[index_of_sharing]
			
			share_screen.set_sharing(True)			#pressing the list = sharing status is True. someone is sharing .
					
			#put the status of currently sharing next to his name, and update the screen
			new_sharing_client.SetName(new_sharing_client.getUsername()+"-Currently Sharing")
			update_client_list()
			
			
		is_MouseClicked = False
	
		
	#check if there is no clients in the program, or no one is sharing..
	if len(client_list.get_clients_names()) == 0:
		#if there is: reset current_sharing, set sharing to False(in the thread) 
		current_sharing = None										#no one is currently sharing.
		share_screen.set_sharing(False)								#in case that sharing status is True						
		pygame.draw.rect(DISPLAY,WHITE,SHARE_WINDOW)				#clean the window from the last image

			
	#update the screen to see the changes
	pygame.display.update()									
	
#when the main loop is stop, close the program.
share_screen.kill_thread_sign()
