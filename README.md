# NosTale-Gfless
A library that allows you to launch NosTale client without GF launcher, or create your own private server launcher that starts the game client in the server selection screen (you skip the login & pass window)

# Emulating GF launcher
The launcher communicates with the game using [named pipe](https://docs.microsoft.com/en-us/windows/win32/ipc/named-pipes) and [JSON-RPC](https://en.wikipedia.org/wiki/JSON-RPC) protocol.

# Preparation
Before the game is started GF launcher creates two environment variables:
* `_TNT_CLIENT_APPLICATION_ID` - This is the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) that is stored in windows registry, it is probably const for the GF launcher itself.
* `_TNT_SESSION_ID` - This var contains random [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) to identify game client in the launcher (in case you run multiple game clients)

## What is the purpose of those vars?
* `_TNT_CLIENT_APPLICATION_ID` helps to locate the GF client installation folder, the game reads it from registry key `Computer\HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall{THE_UUID_FROM_VAR}_is1` in order to locate the `gameforge_client_api.dll`. If the var doesn't exist the game tries to grab the dll from the game folder itself. So if you don't set the var you need to copy the dll manually from GF launcher to game folder.
* `_TNT_SESSION_ID` the var also isn't mandatory, you don't have to set it if you want to make things simpler.

Please note, as long as you don't set those vars you are fine, however if you for some reasons want to do that **do NOT set those variables as global windows environments, instead set it as local vars for your process**

# The pipe
The next step before launching the game is to create MS Windows pipe named `\\.\pipe\GameforgeClientJSONRPC` using `CreateNamedPipe` winapi func with duplex and byte modes. Then you need to launch the game client with `gf` parameter, and wait for the informations sent over pipe using `ConnectNamedPipe`

If you see error messagebox like `gf init failed` at this points, it means that the game client couldn't locate `gameforge_client_api.dll` either in the location pointed via registry key, or inside the game folder itself.

# The protocol
You can read/write to the pipe using winapi calls like `ReadFile` or `WriteFile`. After the game client initialize, it will send...
## First message (isClientRunning):
Message from client:

```
{{\"id\":1,\"jsonrpc\":\"2.0\",\"method\":\"ClientLibrary.isClientRunning\",\"params\":{{\"sessionId\":\"SESSION_FROM_TNT_SESSION_ID\"}}}}
```

You need to answer:

```
{{\"id\":1,\"jsonrpc\":\"2.0\",\"result\":true}}
```

## Second message (initSession):
Message from client:

```
{{\"id\":2,\"jsonrpc\":\"2.0\",\"method\":\"ClientLibrary.initSession\",\"params\":{{\"sessionId\":\"SESSION_FROM_TNT_SESSION_ID\"}}}}
```

You need to answer:

```
{{\"id\":2,\"jsonrpc\":\"2.0\",\"result\":\"SESSION_FROM_TNT_SESSION_ID\"}}
```

## Third message (isClientRunning):
It looks the same as first message, except the `id: 1` now becomes `id: 3`

## Fourth message (queryAuthorizationCode):
Message from client:

```
{{\"id\":4,\"jsonrpc\":\"2.0\",\"method\":\"ClientLibrary.queryAuthorizationCode\",\"params\":{{\"sessionId\":\"SESSION_FROM_TNT_SESSION_ID\"}}}}
```

You need to answer with the token obtained from GF API, you may use this library to obtain the token: [Nostale-Auth](https://github.com/morsisko/NosTale-Auth). Remember, you need the raw token (the UUID), not the hexlified one. If you create private server launcher you need to suply your own auth token, that you can later validate inside your login/game server:

```
{{\"id\":4,\"jsonrpc\":\"2.0\",\"result\":\"AUTH_TOKEN_IN_UUID_FORM\"}}
```

## Fifth and the last message (queryGameAccountName):
Message from client:

```
{{\"id\":5,\"jsonrpc\":\"2.0\",\"method\":\"ClientLibrary.queryGameAccountName\",\"params\":{{\"sessionId\":\"SESSION_FROM_TNT_SESSION_ID\"}}}}
```

It looks like it really doesn't matter what display name you will send, you will login anyway, however if you want to stick what the GF launcher does, you can obtain the proper display name using library linked above.

```
{"id":5,"jsonrpc":"2.0","result":"DISPLAY_NAME"}
```

## What to note
* All the communication is done in JSON format, it looks really strange here because it is in escaped format, however any proper json should be accepted.
* If you dont set the `_TNT_SESSION_ID` then `SESSION_FROM_TNT_SESSION_ID` will be empty in all the messages exchanged between launcher and game, however this doesn't really matter
* **After each packet send you may have to create the pipe again using `CreateNamedPipe`**

# Running example server
In order to run the example server you need to:
* Install python3 (remember, set the checkbox with "Add to PATH")
* Modify the very first line of server.py to **set the correct game path**
* Install the `requests` and `pywin32` libraries, you can do it easily using `pip`
* Run the shell with admin permissions and execute the `python server.py <email> <password>`

NOTE: If you don't have the GF launcher installed you firstly need to put the `gameforge_client_api.dll` into the game folder, and comment out the line with `os.environ["_TNT_CLIENT_APPLICATION_ID"] = ....`
