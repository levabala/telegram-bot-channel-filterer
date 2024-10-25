FROM python:3.13

ADD requirements.txt *.session bot.py /

RUN pip3 install -r requirements.txt

CMD ["python3", "bot.py"]
