FROM python:3.8-buster

ENV PYTHONDONTWRITEBYTECODE True
ENV PYTHONUNBUFFERED True

ADD requirements.txt .
RUN python -m pip install -r requirements.txt --use-deprecated=legacy-resolver

WORKDIR /app
ADD . /app

ENV PYTHONPATH=${PYTHONPATH}:.

ENTRYPOINT ["python", "ack/entrypoints/cli/main.py"]
