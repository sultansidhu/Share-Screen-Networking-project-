#-------------------Imports------------------#
import os
import socket
import sys
import time
from PIL import ImageGrab
import select
import pygame
import threading

#-------------------Constants----------------#
SERVER_IP = "10.100.102.11"									#server ip to connect
TCP_PORT = 1095												#tcp port for genreal socket
IMAGE_PORT = 1637												#image port  for image socket transfer
WHITE = (255,255,255)											#white colour
BLACK = (0,0,0)													#black colour
SILVER= (192,192,192)											#sliver colour 
RED = (255,0,0)													#red colour
BLUE = (0, 0, 255)												#blue colour
SHARE_FPS = 30													#fps value that recommended for sharing screens programs.

#-------------------Global-------------------#
screenshot_pointer = None									#ShareScreenThread pointer
share_window = None											#pointer to Window object
ConnectionObject = None										#pointer to SocketConnection object
GameFlag = True													#boolean that hold true if the loop is run\suppose to run, else false.
EntirePic = []														#list that holds chunks of the image 
#-------------------Objects----------------#
	
class ShareScreenThread(threading.Thread):

	def __init__(self):
		'''
		Enter Statement: the constructor doesn't get paramaters
		Exit Statement: the constructor create ShareScreenThread object
		'''
		threading.Thread.__init__(self)				#init Thread constructor
		self.__run_thread = False						#don't start the thread yet
		self.__fpsClock = pygame.time.Clock()		#init fps clock
		self.__kill_thread = False						#don't kill the thread yet
		self.__fps = SHARE_FPS						#fps time


	def set_runthread(self,thread_bool):
		'''
		Enter Statement: the function gets a boolean
		Exit Statement: the function set the run thread propertie to start or to stop
						Function doesn't return value.
		'''
		self.__run_thread = thread_bool
		
		
	def kill_thread(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the fucntion "kill" the thread (main thread loop)
						the function doesn't return value.
		'''
		self.__kill_thread = True
		
	def is_sharing (self):		
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function return True if the client currently sharing,
						else the function return false.
		'''
		return self.__run_thread			
	
	def get_runthread(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function return True if the thread is running , else return false.
		'''
		return self.__kill_thread
	
	def run(self):	
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function run the thread, doesn't return value.
		'''
		
		#as long as the thread is alive
		while not self.__kill_thread:
			
			#if i'm currently need to share my screen
			if self.__run_thread:
			
				info = TCP_get()							#get request from the server to send image
				grabpic = ScreenGrab()					#get Screen Shot
				sendFullFrameBuffer(grabpic[0])		#send the screen shot

			self.__fpsClock.tick(self.__fps)			#tick the clock
				
#-----------------------------------------------#
	
class Window():
	
	def __init__(self,resolution,flags,depth,caption,xpos,ypos,displayMessage):
		'''
		Enter Statement: the function gets 2 attributes
		Exit Statement: the function init the attributes and create Window Object
		'''
		self.__display =  pygame.display.set_mode(resolution,flags,depth)					#window pointer
		pygame.display.set_caption(caption)															#set window title
		os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (xpos,ypos)					#set window position
		self.__display.fill(WHITE)																			#fill the window with white background
		self.__displayMessage = displayMessage														#the message to display on window

	def GetNameWindow(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function display window that gets user name, and return the name
		'''
		data = ""
		fontObj = pygame.font.SysFont("Ariel", 30)
		textSurfaceObj = fontObj.render(data, True, BLUE)
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				elif event.type == pygame.KEYDOWN:
					
					
					#the limit is 15 letters for name
					if len(data) > 15:
						return data
						
				# If backspace pressed
					elif event.key == pygame.K_BACKSPACE:
						data = data[:-1]
					# If letter pressed and it is a-z or A-Z
					elif (event.unicode.isalpha()) and ((event.unicode>='a' and event.unicode<='z') or (event.unicode>='A' and event.unicode<='Z')):
						data += event.unicode
					# If space pressed
					elif event.key ==pygame.K_SPACE:
						data += " "
					# If enter pressed
					elif event.key == 13:
						return data
						
			#display the letters that the client typed
			pygame.draw.rect(self.__display,SILVER,(275,78,200,20))
			textSurfaceObj = fontObj.render(data, True, BLUE)
			self.__display.blit(textSurfaceObj, (278,78))
			pygame.display.update()
		
	def FirstWindow(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function display the first window in this program, doesn't return any value
		'''
		username_font = pygame.font.SysFont("monospace", 14)			
		warning_font = pygame.font.SysFont("monospace", 13)
		username_label = username_font.render("Enter User Name(English Letters):",1,BLACK)	
		warning_label = warning_font.render("*By Pressing \"ENTER\" You Agree That",1,RED)
		self.__display.blit(username_label,(35,78))							
		self.__display.blit(warning_label,(35,120))							
		warning_label = warning_font.render("The Server Will Get Your Screen Images.",1,RED)
		self.__display.blit(warning_label,(33,135))							
		pygame.draw.rect(self.__display,SILVER,(275,78,200,20))	
		pygame.display.update()
		
		name = self.GetNameWindow()		#GET name of client
		return name
	
	def OnSharingWindow(self):
		'''
		Enter Statement: the function doesn't get parameters
		Exit Statement: the function creates the DisconnectedWindow, no return value
		'''
		disconnected_font = pygame.font.SysFont("monospace", 15)
		disconnected_label = disconnected_font.render("Click here to exit the program",1,BLACK)	
		self.__display.blit(disconnected_label,(20,20))	
		pygame.display.update()
		
		
	def DisplayMessage(self):	
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function display message on the window, doesn't return value
		'''
		
		#display the message to the client, and the quit after 7 seconds
		self.__display.fill(WHITE)	
		disconnected_font = pygame.font.SysFont("monospace", 15)
		disconnected_label = disconnected_font.render(self.__displayMessage,1,BLACK)	
		self.__display.blit(disconnected_label,(10,20))	
		pygame.display.update()
			
			
	def DisconnectedWindow(self):
		'''
		Enter Statement: the function doesn't get parameters
		Exit Statement: the function display the disconnected message and close window
		'''

		self.DisplayMessage()
		
		#wait 3.5 seconds so the client will see the message in the disconnected window
		time.sleep(3.5)
		pygame.quit()
	
	def setDisplayMessage(self,newDisplayMessage):
		'''
		Enter statement: the function gets string
		Exit Statement: the function set the displayMessage , no return value
		'''
		self.__displayMessage = newDisplayMessage

#-----------------------------------------------#

class SocketConnection():

	def __init__(self):
		'''
		Enter Statement: the constructor doesn't get paramaters
		Exit Statement: the constructor create Socket Connection
		'''
		self.__TcpSocketConnection = None							#connetion and disoconnection socket
		self.__TcpSocketImage = None						#transfer images socket
		
	def SetUpConnection(self):
		'''
		Enter Statement: the function doesn't take paramaters
		Exit Statement: the function return True if the connection was made, else return false
		'''
		try:
			self.__TcpSocketConnection = socket.socket(socket.AF_INET,socket.SOCK_STREAM)				
			self.__TcpSocketImage = socket.socket(socket.AF_INET,socket.SOCK_STREAM)			
			
			#connect to the server
			self.__TcpSocketConnection.connect((SERVER_IP,TCP_PORT))
			self.__TcpSocketImage.connect((SERVER_IP,IMAGE_PORT))
			
			#return true if everything went succesfully ok.
			return True
		except socket.error, errorMessage:	
			share_window.setDisplayMessage("Server Down. exit.")
			return False
			
			
	def CloseConnection(self):
		'''
		Enter Statement: the function doesn't get paramaters
		Exit Statement: the function close the connection and the sockets
		'''
		try:
			self.__TcpSocketConnection.close()
			self.__TcpSocketImage.close()
		except socket.error, e:
			print
			
	def getConnectionSocket(self):
		'''
		Enter Statement: the function doesn't take paramaters
		Exit Statement: the function return the Connection Socket
		'''
		return self.__TcpSocketConnection
		
	def getImageSocket(self):
		'''
		Enter Statement: the function doesn't take paramaters
		Exit Statement: the function return the Image Socket
		'''
		return self.__TcpSocketImage
	
#------------------Functions--------------------#

		
def ScreenGrab():
	'''
	Enter Statement: the function doesn't take paramaters
	Exit Statement: the function grab screen shot and return it and the size.
	'''
	
	#grab screen shot
	im = ImageGrab.grab()
	im.save(r"ShareScreen_ByRoyKuper.jpg" , quality = 50 ,dpi = (400,400))
	
	size = os.path.getsize(r"ShareScreen_ByRoyKuper.jpg")/1000		#retrun size KB
	
	#get the data from the file
	with open (r"ShareScreen_ByRoyKuper.jpg","rb") as image_pointer:
		returnImage = image_pointer.read()
		

	return returnImage,size


def sendFullFrameBuffer(current_pic):
	'''
	Enter Statement: the function doesn't get parameters
	Exit Statement: the function encode the image amd semd it if the encoded image is diffrent then
					the encoded image before. doesn't return value.
	'''
	global EntirePic,ConnectionObject
	
	#as long as there is data in the file, keep sending it.
	while current_pic!="":
		TCP_send(ConnectionObject.getImageSocket(),current_pic[:1024])
		EntirePic.append(current_pic[:1024])  
		current_pic = current_pic[1024:]
		
	#send to the server that i'm done .
	TCP_send(ConnectionObject.getImageSocket(),"END")
	
	
def TCP_send(tcpsock,data):
	'''
	Enter Statement: the function get a socket and string
	Exit Statement: the function send via the socket, the data, no return value
	'''
	
	global GameFlag,share_window
	
	try:
		tcpsock.send(data)
	except socket.error , e:
	
		#connection problem, close the program.
		screenshot_pointer.kill_thread()		
		GameFlag = False
		share_window.setDisplayMessage("Connection Error occur... exit")


def TCP_get():
	'''
	Enter Statement: the function doesn't get paramaters
	Exit Statement: the function get data from socket and the function return this data.
	'''
	global ConnectionObject,GameFlag,share_window
	
	try:
		data = ConnectionObject.getConnectionSocket().recv(1024)
		return data
	except socket.error,e :
	
		#connection problem, close program.
		screenshot_pointer.kill_thread()
		GameFlag = False
		share_window.setDisplayMessage( "Connection Error occur... exit")		
		return False
		
#-------------------Main-Code----------------

pygame.init()								#initialize parameters in pygame module

#first window, getting input , and close window
SetUpWindow = Window((500,300),0,32,"Sharing Screens - by Roy Kuper",350,200,"")
name = SetUpWindow.FirstWindow()

#the window that appear when the client finish type his name.
share_window = Window((500,300),0,32,"Share Screen",0,650,"Click Here To Exit")
share_window.OnSharingWindow()
share_window.setDisplayMessage("Waiting for connection...")
share_window.DisplayMessage()

#connection object to handle the sockets of the program.
ConnectionObject = SocketConnection()

#get true if the connction succeed.
GameFlag = ConnectionObject.SetUpConnection()
if GameFlag:

	#display message, means that the connection was successfull.
	share_window.setDisplayMessage("Click Here to exit the program")
	share_window.DisplayMessage()
	
	#send the name to the server.
	TCP_send(ConnectionObject.getConnectionSocket(),name)
	screenshot_pointer = ShareScreenThread()		#create and start the screen shot thread.
	screenshot_pointer.start()
	
#main program loop that keeps run as long as there is no errors\the client didn't exit the program.
while GameFlag:	

	#get events
	for event in pygame.event.get():
	
		#check if the client decided to exit the program
		if event.type ==pygame.QUIT or event.type==pygame.MOUSEBUTTONUP:
			share_window.setDisplayMessage ("See you soon")			#display see u soon mesage
			screenshot_pointer.kill_thread()										#kill the thread
			GameFlag = False														#kill the game loop
			break																		#break the event loop
			
	#if client decided to exit, quit the game loop
	if GameFlag==False:
		break
	
	
	rlist,wlist,xlist = select.select([ConnectionObject.getConnectionSocket()],[],[],0.1)
	if len(rlist)==1:
		
		server_data = TCP_get()
		
		#check if the server fell or something happened to him
		if server_data=="":
			share_window.setDisplayMessage("Server down...exit")
			screenshot_pointer.kill_thread() 											#kill the thread.
			break																			#kill main program loop
			
		if not screenshot_pointer.is_sharing():
			if server_data=="START":	
				screenshot_pointer.set_runthread(True)							#start sharing if the server told me to

		else:
			if server_data=="STOP":
				screenshot_pointer.set_runthread(False)							#stop sharing if the server told me to


#avoid from null pointer exception, (example: server down and we try to connect to him)
if screenshot_pointer!=None:			
	screenshot_pointer.kill_thread()
	
share_window.DisconnectedWindow()			#show the client the final window with the information
ConnectionObject.CloseConnection()			#close the sockets and the connection in general.