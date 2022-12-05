import os
import json
import socket
import random
import threading
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import image

pd.options.display.max_rows = 1000
MAX_LENGTH = 1024
SHARED_FOLDER = "./shared"
DOWNLOAD_FOLDER = SHARED_FOLDER + "/download/"

# Client TCP P2P class
class Client():
  def __init__(self, port=-1, max_connection=10):
    self.port = port
    if self.port == -1: self.port = random.randint(12345, 65535)
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.ip = socket.gethostbyname(socket.gethostname())
    self.socket.bind((self.ip, self.port))
    self.max_connection = max_connection
    if not os.path.exists(SHARED_FOLDER): os.mkdir(SHARED_FOLDER)
    self.launch()

  def selectChoice(self, question, answers):
    print(question)
    for i in range(len(answers)):
      print(str(i) + ". " + answers[i])
    while True:
      try:
        choice = int(input("Select your choice: "))
        if choice >= 0 and choice < len(answers):
          return choice
      except:
        pass

  def launch(self):
    choice = self.selectChoice("What do you want to do ?", ["Listen", "Connect"])
    if choice == 0:
      self.listen()
    elif choice == 1:
      self.connect()

  def connect(self):
    while True:
      # try:
        ip = input("Enter the IP of the client you want to connect to: ")
        port = int(input("Enter the port of the client you want to connect to: "))
        self.socket.connect((ip, port))
        print("Connected to", ip, "on port", port)
        self.communicate()
      # except Exception as e:
        # print("Connection failed, ip or port invalid")
        # print(e)
        # print("Try again")
        # self.socket.close()

  def send_file_list(self, msg):
    print("Files available:", msg[1]) # Print the file available
    file_list = msg[1][2:-2].replace("'", "").replace(" ", "").split(',')
    choice = self.selectChoice("Which file do you want to download ?", file_list) # Make a selection of the file to download
    if choice == len(msg[1]): return # Break (close socket) to 
    self.socket.send(("2;" + str(file_list[int(choice)])).encode()) # Send the wanted file to the server

  def listen(self):
    self.socket.listen(self.max_connection)
    print("Listening with IP", self.ip, "on port", self.port)
    while True:
      conn, addr = self.socket.accept()
      thread = threading.Thread(target=self.manageClientConnection, args=(conn, addr))
      thread.start()
  
  def sendFileList(self, conn):
    files = [item for item in os.listdir(SHARED_FOLDER) if os.path.isfile(os.path.join(SHARED_FOLDER, item))]
    conn.send(("1;" + str(files)).encode())

  def manageClientConnection(self, conn, addr):
    print("New connection from", addr)
    files = [item for item in os.listdir(SHARED_FOLDER) if os.path.isfile(os.path.join(SHARED_FOLDER, item))]
    conn.send(("1;" + str(files)).encode())
    while True:
      msg = conn.recv(MAX_LENGTH).decode().split(';')
      if (int(msg[0]) == 0):
        files = [item for item in os.listdir(SHARED_FOLDER) if os.path.isfile(os.path.join(SHARED_FOLDER, item))]
        conn.send(("1;" + str(files)).encode())
      if int(msg[0]) == 2: # If client requested for a file
        print("Sending file", msg[1])
        data = open(os.path.join(SHARED_FOLDER, msg[1]), 'rb').read()
        conn.send(("3;" + str(len(data)) + ";" + msg[1]).encode()) # Send the file lenght
        conn.send(data) # Send the file
        print("File sent")

  def communicate(self):
    while True:
      msg = self.socket.recv(MAX_LENGTH).decode().split(';')
      try: protocol = int(msg[0])
      except: protocol = -1
      if protocol == 0: self.socket.send("0".encode())
      if protocol == 1:  # If protocol is 1, client is asking for file list
        self.send_file_list(msg)
      elif protocol == 3: # If protocol is 3 the client is about to send a file
        filename = msg[2]
        choice = self.selectChoice('What do you want to do ?', ['Download', 'Visualize', 'Cancel'])
        if choice == 0:
          self.downloadFile(msg)
        elif choice == 1:
          self.downloadFile(msg)
          self.visualize(msg)
          self.delFile(msg)
        elif choice == 2:
          self.socket.send("0".encode())
    # self.socket.close()

  def downloadFile(self, msg):
    print("Receiving file")
    data = self.socket.recv(int(msg[1]))
    filename = msg[2]
    file = open(os.path.join(DOWNLOAD_FOLDER, filename), 'wb')
    file.write(data)
    file.close()
    
  def visualize(self, msg):
    if (msg[2].find('.csv') != -1):
      try:
        print(pd.read_csv(DOWNLOAD_FOLDER + msg[2]))
      except:
        print("Error: The file is not a valid csv file")
    elif (msg[2].find('.json') != -1):
      with open(DOWNLOAD_FOLDER + msg[2]) as datafile:
        try:
          data = json.load(datafile)
          print(json.dumps(data, indent=2))
        except:
          print("Error: The file is not a valid json file")
          return
    elif (msg[2].find('.png') != -1 or msg[2].find('.jpg') != -1):
      try:
        img = image.imread(DOWNLOAD_FOLDER + msg[2])
        plt.imshow(img)
        plt.show()
      except:
        print("Error: The file is not a valid png file")
        
  def delFile(self, msg):
    try:
      os.remove(DOWNLOAD_FOLDER + msg[2])
    except:
      pass

cli = Client()
