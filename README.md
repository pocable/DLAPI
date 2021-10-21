# DLAPI
A API to send torrent magnet links to real debrid and on completion download the
link using JDownloader.
```
Magnet Link --> DLAPI --> RD --> DLAPI --> RD --> JDownloader
```

## Setup
Use the [docker container](https://hub.docker.com/repository/docker/pocable/dlapi)
provided to make it easier, otherwise do the following steps:
* Edit: Makefile to point to an environment file
* Run: make build
* Run: make run

## Development Setup
This is only if you want to run it locally without docker.
* Run pip install -r requirements.txt
* Run pip install -e .
* Modify ENVIRONMENT.bat to declare your environment variables
* Run the bat file depending on if you want to run the application or test it

## Environment File
```
JD_USER= JDownloader Username
JD_PASS= JDownloader Password
JD_DEVICE= JDownloader Device
RD_KEY= Real Debrid API Key
API_KEY= Custom API Key

(OPTIONAL) ENABLE_CORS_PROXY= true/false (default false)
(OPTIONAL) JACKETT_URL= Jackett server IP
(OPTIONAL) JACKETT_API_KEY= Jackett API Key
(OPTIONAL) USER_PASS= The user password for sessioning. Required for sessioning to be enabled.
(OPTIONAL) SESSION_EXPIRY_DAYS= The number of days before a session expires. Default = 1
```
A folder at /dlconfig/ will be created to store the file in the run directory. 
This is so docker containers can keep config files saved if they point this using PATH.

Note that the session expiry is personal preference, but should be limited in order to secure the system.

## API Calls
All calls require an Authorization header </br>
```
{'Authorization': API_KEY here}
```

### POST - /api/v1/content
Adds the torrent magnet to the monitored list, when the magnet link is done downloading auto send to JDownloader to be downloaded to the provided path.

```
{

    'magnet_url': A magnet url you want to download OR 'id': Real debrid ID to be added. OR 'url': A link which redirects to a magnet link (JACKETT).

    'title': Optional title. Makes the GET return id, path and title rather than just ID.

    'path': Download path on server.
}
```
Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 400        | Error in the input. See the content message for which one. |
| 401        | Authentication failed. Check your DLAPI key.               |
| 417        | RealDebrid error, See the content message for details.     |

Success Returns
```
{}
```

Error Returns
```
{
    'Error' : 'message'
}
```

### DELETE - /api/v1/content
Removes an ID to the monitored list.

```
{
    'id': Real Debrid ID, can be obtained from GET - /api/v1/content/all
}
```
Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 400        | Error in the input. See the content message for which one. |
| 401        | Authentication failed. Check your DLAPI key.               |
| 410        | ID was not being watched so nothing has changed.           |

Success Returns
```
{}
```

Error Returns
```
{
    'Error' : 'message'
}
```

### GET - /api/v1/content/check
Immedietly check RD to see if content has finished downloading.

Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 401        | Authentication failed. Check your DLAPI key.               |

Success Returns
```
{}
```

Error Returns
```
{
    'Error' : 'message'
}
```

### GET - /api/v1/content/all
Get a list of all monitored Real Debrid ID's and their download path.

Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 401        | Authentication failed. Check your DLAPI key.               |

Success Returns (Example)
```
{
    "EXAMPLE1ID": {
        "path": "/media/movies/",
        "title": "Movie Title"
    },
    "EXAMPLE2ID": {
        "path": "/media/tv/",
        "title": "Title 2"
    }
}
```

Error Returns
```
{
    'Error' : 'message'
}
```

### DELETE - /api/v1/content/all
Delete all ID's being watched by the system.

Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 401        | Authentication failed. Check your DLAPI key.               |

Success Returns
```
{}
```

Error Returns
```
{
    'Error' : 'message'
}
```


### GET - /api/v1/corsproxy
Simple CORS proxy to GET a given url. Disabled when it is not configured in the environment.

```
URL Parameters:
url=[URL to proxy]
```

This proxy will return the exact status code and text from the source.


### GET - /api/v1/jackett/search
Search jackett and get the raw information back. Disabled when the environment is not set.

```
URL Parameters:
query=[The item to seach for on jackett.]
categories=[Jackett categories. '&categories=' + categories. Example: "2045,2050,2060"]
```

This proxy will return the exact status code and text from the source

### POST - /api/v1/authenticate
Authenticate a given user password in order to recieve a token. This module is optional but allows for cookie saving in JDRD.
```
{
    'userpass': The userpassword set earlier.
}
```

Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 400        | Error in the input. See the content message for which one. |
| 401        | Authentication failed. Check your DLAPI key.               |
| 410        | Sessioning is disabled. This call is not needed.           |

Success Returns
```
{
    'token': The returned session token.
}
```

Error Returns
```
{
    'Error' : 'message'
}
```

### POST - /api/v1/authenticate/validtoken
Check if a token is still valid on the server side. 
```
{
    'token': The user token.
}
```

Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 400        | Error in the input. See the content message for which one. |
| 410        | Sessioning is disabled. This call is not needed.           |

Success Returns
```
{
    'is_valid': boolean if its valid.
}
```

Error Returns
```
{
    'Error' : 'message'
}
```

### POST - /api/v1/authenticate/closesession
Close the user session with the provided token.
```
{
    'token': The user token.
}
```

Returns
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 200        | Success                                                    |
| 400        | Error in the input. See the content message for which one. |
| 410        | Sessioning is disabled. This call is not needed.           |

Success Returns
```
{
    'is_valid': boolean if its valid.
}
```

Error Returns
```
{
    'Error' : 'message'
}