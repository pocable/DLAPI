build:
	docker build -t python-dlapi .

test:
	pyhton -m unittest

run:
	docker run --env-file A:\\Development\\DLAPI_KEYS.txt -d -p 4248:4248 python-dlapi

upload:
	docker tag python-dlapi pocable/dlapi:latest
	docker push pocable/dlapi:latest