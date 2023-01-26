FROM python:3.6.8-slim-jessie

COPY . /export

WORKDIR /export

RUN pip install -r requirements.txt

ENTRYPOINT [ "/usr/local/bin/python3", "export.py", "-s" ]

