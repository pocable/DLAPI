build:
	docker build -t python-dlapi .

run:
	docker run --env-file A:\\Development\\DLAPI_KEYS.txt -d -p 4248:4248 python-dlapi
	