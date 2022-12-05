import socket
from client import Client
print(socket.gethostbyname(socket.gethostname()))

def pickMessage(question, answers):
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

res = pickMessage("What do you want to do?", ["Await for a connection", "Connect to someone"])
cli = Client()

if (res == 0):
  print("Your ip is: " + socket.gethostbyname(socket.gethostname()))
  print("Awaiting for a connection")
  cli.awaitConnection()
else:
  while True:
    ip = input("Enter the ip of the person you want to connect to: ")
    try:
      cli.connect(ip)
      break
    except:
      print("Could not connect to the ip")
      print("Try again")