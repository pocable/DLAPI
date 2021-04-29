#!/bin/sh

trap "kill 0" INT

while : 
do
    gunicorn --log-level=INFO dlapi:app -b 0.0.0.0:4248 -t 240
    echo "DLAPI server has crashed! This could be casued by JDownloader not being started before the app, or could be another cause."
    echo "Please open an issue if this happens a lot."
    echo "Waiting 10 seconds and attempting it again..."
    sleep 10
done