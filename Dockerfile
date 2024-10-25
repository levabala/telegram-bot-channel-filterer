FROM python:3.13

ADD Pipfile Pipfile.lock bot.py /

RUN pip3 install pipenv
RUN pipenv install

CMD ["pipenv shell python3 bot.py"]
