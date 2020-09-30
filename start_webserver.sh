#!/bin/sh

gunicorn --log-level=INFO DLAPI:app -b 0.0.0.0:4248 -t 60