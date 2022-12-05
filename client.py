import os
import json
import socket
import random
import threading
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import image
import time
import sys

pd.options.display.max_rows = 1000
MAX_LENGTH = 1024
SHARED_FOLDER = "./shared"
DOWNLOAD_FOLDER = "./download"

# Client TCP P2P class
class Client():
  def __init__(self, port=-1, max_connection=10):
    self.port = port # Port of the client
    if self.port == -1: self.port = random.randint(12345, 65535) # If no port is specified, choose a random one
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket
    self.ip = socket.gethostbyname(socket.gethostname()) # Get the IP of the client
    self.socket.bind((self.ip, self.port)) # Bind the socket to the IP and the port
    self.max_connection = max_connection # Max number of connection
    if not os.path.exists(SHARED_FOLDER): os.mkdir(SHARED_FOLDER) # Create the shared folder if it doesn't exist
    if not os.path.exists(DOWNLOAD_FOLDER): os.mkdir(DOWNLOAD_FOLDER) # Create the download folder if it doesn't exist
    self.exit = False # Exit variable
    self.launch()

  # Ask the user to select a choice in a list
  def selectChoice(self, question, answers):
    print(question)
    for i in range(len(answers)): # Print the answers
      print(str(i) + ". " + answers[i])
    while True: # Loop until a valid answer is given
      try:
        choice = int(input("Select your choice: "))
        if choice >= 0 and choice < len(answers):
          return choice
      except:
        pass

  # Ask the user if he wants to listen for a connection or connect to a client
  def launch(self):
    choice = self.selectChoice("What do you want to do ?", ["Listen", "Connect"])
    if choice == 0:
      self.listen()
    elif choice == 1:
      self.connect()

  # Connect to a client
  def connect(self):
    while True:
      try:
        ip = input("Enter the IP of the client you want to connect to: ")
        port = int(input("Enter the port of the client you want to connect to: "))
        self.socket.connect((ip, port)) # Try to connect to the client with the given IP and port
        print("Connected to", ip, "on port", port)
        self.communicate() # If the connection is successful, communicate with the client
      except:
        if self.exit: break
        print("Connection failed, ip or port invalid")
        print("Try again")
        self.socket.close()

  # Retrieve and print the file list and select a file to access
  def getFileList(self, msg):
    file_list = msg[1][2:-2].replace("'", "").replace(" ", "").split(',') # Retrieve the file list
    file_list.insert(0, "Exit") # Add the exit option
    choice = self.selectChoice("Which file do you want to access ?", file_list) # Make a selection of the file to access
    if choice == 0: # If the user wants to exit
      self.socket.close()
      self.exit = True
      sys.exit()
    self.socket.send(("2;" + str(file_list[int(choice)])).encode()) # Send the wanted file to the server

  # Listen and accept incoming connections
  def listen(self):
    self.socket.listen(self.max_connection) # Listen for incoming connections
    print("Listening with IP", self.ip, "on port", self.port)
    while True: 
      conn, addr = self.socket.accept() # Accept incoming connections
      thread = threading.Thread(target=self.manageClientConnection, args=(conn, addr)) # Create a thread for each new connection
      thread.start() 

  # Send the file list to the client
  def sendFileList(self, conn): 
    files = [item for item in os.listdir(SHARED_FOLDER) if os.path.isfile(os.path.join(SHARED_FOLDER, item))] # Get the file list in the shared folder
    conn.send(("1;" + str(files)).encode()) # Send the file list to the client

  def manageClientConnection(self, conn, addr):
    print("New connection from", addr)
    self.sendFileList(conn)
    while True: # Loop until the client disconnects
      msg = conn.recv(MAX_LENGTH).decode().split(';')
      if (msg == ['']): break # If the client disconnects, break the loop
      if (int(msg[0]) == 0): # If protocol is 0, client is asking for file list
        self.sendFileList(conn)
      if int(msg[0]) == 2: # If client requested for a file
        print("Sending file", msg[1])
        data = open(os.path.join(SHARED_FOLDER, msg[1]), 'rb').read() # Read the requested file
        conn.send(("3;" + str(len(data)) + ";" + msg[1]).encode()) # Send the file lenght in bytes
        conn.send(data) # Send the file
        print("File sent")

  def communicate(self):
    while True: # Loop until the client disconnects
      msg = self.socket.recv(MAX_LENGTH).decode().split(';') # Receive the client message
      try: protocol = int(msg[0]) # Unknow protocol
      except: protocol = -1
      if protocol == 0: self.socket.send("0".encode())
      if protocol == 1:  # If protocol is 1, client is asking for file list
        self.getFileList(msg)
      elif protocol == 3: # If protocol is 3 the client is about to send a file
        filename = msg[2]
        choice = self.selectChoice('What do you want to do ?', ['Download', 'Visualize', 'Cancel'])
        if choice == 0:
          print("Receiving file")
          self.downloadFile(msg) # Download the file to the download folder
          print("File " + filename + " successfully downloaded.")
        elif choice == 1:
          self.downloadFile(msg) # Download the file to visualize it
          self.visualize(msg) # Visualize the file
          self.delFile(msg) # Delete the file after visualization
        self.socket.send("0".encode()) # Go back to the file list

  # Download a file
  def downloadFile(self, msg):
    timeBeforePacketRecv = time.time()
    try:
      data = self.socket.recv(int(msg[1]))
    except:
      print("Access to file timeout")
      return
    print("Latency", time.time() - timeBeforePacketRecv, "seconds") # Calculate the latency
    filename = msg[2]
    file = open(os.path.join(DOWNLOAD_FOLDER, filename), 'wb') # Create the file in the download folder
    file.write(data) # Write the data in the file
    file.close()

  def visualize(self, msg):
    if (msg[2].find('.csv') != -1): # If the file is a csv file read and print it with the pandas library
      try:
        print(pd.read_csv(os.path.join(DOWNLOAD_FOLDER, msg[2])))
      except:
        print("Error: The file is not a valid csv file")
    elif (msg[2].find('.json') != -1): # If the file is a json file read and print it with the json library
      with open(os.path.join(DOWNLOAD_FOLDER, msg[2])) as datafile:
        try:
          data = json.load(datafile)
          print(json.dumps(data, indent=2))
        except:
          print("Error: The file is not a valid json file")
          return
    elif (msg[2].find('.png') != -1 or msg[2].find('.jpg') != -1): # If the file is a png or jpg file open it with the matplotlib library
      try:
        img = image.imread(os.path.join(DOWNLOAD_FOLDER, msg[2]))
        plt.imshow(img)
        plt.show()
      except:
        print("Error: The file is not a valid png file")
    else:
      print("Error: You can't visualize this file")

  # Delete a file from the download folder
  def delFile(self, msg): 
    try:
      os.remove(os.path.join(DOWNLOAD_FOLDER, msg[2])) # Delete the file
    except:
      pass


cli = Client()
