FROM alpine

RUN apk add python3

ADD utils/ /root/utils
ADD app/ /root/app/
ENV PYTHONPATH /root/

ENTRYPOINT [ "/root/main.py" ]
