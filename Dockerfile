FROM tiangolo/uwsgi-nginx-flask:python3.8

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY ./app /app