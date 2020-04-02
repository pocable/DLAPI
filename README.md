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

### Environment File
```
JD_USER= JDownloader Username
JD_PASS= JDownloader Password
JD_DEVICE= JDownloader Device
RD_KEY= Real Debrid API Key
API_KEY= Custom API Key
```

## API Calls
All calls require an Authorization header </br>
```
{'Authorization': API_KEY here}
```

### POST - /api/v1/content
Adds the torrent magnet to the monitored list, when the magnet link is done downloading auto send to JDownloader to be downloaded to the provided path.

```
{

    'magnet_url': A magnet url you want to download OR 'id': Real debrid ID to be added.

    'title': Optional title. Makes the GET return id, path and title rather than just ID.

    'path': Download path on server.
}
```

### DELETE - /api/v1/content
Removes an ID to the monitored list.

```
{
    'id': Real Debrid ID, can be obtained from GET - /api/v1/content/all
}
```

### GET - /api/v1/content/all
Get a list of all monitored Real Debrid ID's and their download path.

### DELETE - /api/v1/content/all
Delete all ID's being watched by the system.



## HTTP Codes
| HTTP Codes | Description                                                |
|------------|------------------------------------------------------------|
| 400        | Error in the input. See the content message for which one. |
| 200        | Success                                                    |
| 401        | Authentication failed. Check your DLAPI key.               |
| 410        | The ID provided does not exist/is not watched.             |