NOSTALE_PATH = "C:/GF/Nostale/pl-PL/NostaleClientX.exe"
COUNTRY_CODE = "4"

import win32pipe, win32file, win32api, pywintypes
import sys
import json
import time
import os
import subprocess
from ntauth.ntauth import loginapi

if len(sys.argv) != 3:
    print("Usage: server.py <email> <password>")
    exit()

pipeName = r"\\.\pipe\GameforgeClientJSONRPC"

#If the gameforge_client_api.dll is inside game folder, you don't have to set the var.
os.environ["_TNT_CLIENT_APPLICATION_ID"] = "d3b2a0c1-f0d0-4888-ae0b-1c5e1febdafb"

def prepareResponse(request, response):
    resp = {}
    resp["id"] = request["id"]
    resp["jsonrpc"] = request["jsonrpc"]
    resp["result"] = response
    
    return json.dumps(resp, separators=(',', ':'))

api = loginapi.NtLauncher(locale="pl_PL", gfLang="pl")
if not api.auth(username=sys.argv[1], password=sys.argv[2]):
    print("Couldn't auth!")
    exit()
    
accounts = api.getAccounts()
if len(accounts) == 0:
    print("You don't have any any account")
    
for uid, displayName in accounts:
    print("Account key:", uid, "Account name:", displayName)

acc_similar_to_email = [(x,y) for x, y in accounts if sys.argv[1].startswith(y)]
if len(acc_similar_to_email) == 0:
    acc_similar_to_email = accounts
    
uid, displayName = acc_similar_to_email[0] #Select account that display name is similar to the email.
print("Selected account:", uid, "Name:", displayName)
token = api.getToken(uid, True) #Get raw token from auth api

subprocess.Popen([NOSTALE_PATH, "gf", COUNTRY_CODE]) #Launch NosTale with gf parameter

print("Waiting for NosTale...")

exitAfterWrite = False
while True:
    pipe = win32pipe.CreateNamedPipe(pipeName, win32pipe.PIPE_ACCESS_DUPLEX, win32pipe.PIPE_WAIT | win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE, 255, 0, 0, 3000, None) #Create pipe every time after write
    win32pipe.ConnectNamedPipe(pipe, None)
    
    code, resp = win32file.ReadFile(pipe, 1024)
    decoded = resp.decode(sys.stdout.encoding)
    data = json.loads(decoded)
    
    output = ""
    if data["method"] == "ClientLibrary.isClientRunning":
        print("NosTale asks if client is still running... of course!")
        output = prepareResponse(data, True)
    elif data["method"] == "ClientLibrary.initSession":
        print("NosTale wants to init session... why not?!")
        output = prepareResponse(data, data["params"]["sessionId"])
    elif data["method"] == "ClientLibrary.queryAuthorizationCode":
        print("NosTale wants to get the auth token... just a moment")
        output = prepareResponse(data, token)
    elif data["method"] == "ClientLibrary.queryGameAccountName":
        print("NosTale wants to get your display name, not sure why but... no problem!")
        output = prepareResponse(data, displayName)
        exitAfterWrite = True
        
    if output:
        win32file.WriteFile(pipe, output.encode(sys.stdout.encoding))
        
    if exitAfterWrite:
        print("I'm done... have fun!")
        exit()
    