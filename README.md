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

<details>
<summary>POST - /api/v1/content</summary>
Adds the ID to the monitored list, when the ID is done downloading auto send to JDownloader to be downloaded to the provided path.
</br>
<code>
{
    'magnet_url': A magnet url you want to download
    'path': Download path on server
}
</code>
</details>

<details>
<summary>GET - /api/v1/content/all</summary>
Get a list of all monitored Real Debrid ID's and their download path.
</details>