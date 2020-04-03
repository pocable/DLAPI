FROM python:3

LABEL author='thomas@pocable.ca'

# Add project files to the docker container
ADD DLAPI.py /
ADD requirements.txt /
ADD start_webserver.sh /

# Run requirements installation
RUN pip install -r requirements.txt

# Run the program
ENTRYPOINT ["./start_webserver.sh"]
