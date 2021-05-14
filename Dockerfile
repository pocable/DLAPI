FROM python:3

LABEL author='thomas@pocable.ca'

# Add project files to the docker container
ADD dlapi /dlapi
ADD requirements.txt /
ADD start_webserver.sh /

# Run requirements installation
RUN pip install -r requirements.txt
RUN chmod +x start_webserver.sh

# Run the program
ENTRYPOINT ["./start_webserver.sh"]
