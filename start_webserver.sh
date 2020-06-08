#!/bin/sh

gunicorn DLAPI:app -b 0.0.0.0:4248 -t 60