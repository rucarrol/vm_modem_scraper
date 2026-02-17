FROM alpine:latest

WORKDIR /code
COPY ./ /code
RUN apk update
RUN apk add python3;
RUN python3 -m venv script;
RUN source /code/script/bin/activate;
RUN /code/script/bin/pip3 install -r requirements.txt;

EXPOSE 8000

ENTRYPOINT ["/code/script/bin/python3", "/code/script.py"]
