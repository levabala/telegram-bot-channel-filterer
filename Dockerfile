FROM python:3.13

ADD requirements.txt *.session /
ADD src /src
VOLUME /dbs

RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "src/main.py"]
