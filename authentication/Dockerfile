FROM ubuntu:latest

WORKDIR $PWD/home/app
RUN apt-get update --fix-missing && apt-get install -y \
    software-properties-common
RUN add-apt-repository universe
RUN apt-get install -y python3-pip python-dev build-essential curl openssl


RUN python3.8 -m pip install -U pip

RUN pip3 install pipenv 


COPY Pipfile*  /tmp/

COPY ./frontend /home/app/frontend/

COPY ./authentication/auth_service.py /home/app/

RUN cd /tmp && pipenv lock --requirements > /tmp/requirements.txt
RUN python3.8 -m pip install -r /tmp/requirements.txt --user
RUN pip3 install fastapi-users[mongodb] #Can potentially move to Pipfile

CMD ["python3.8","auth_service.py"]