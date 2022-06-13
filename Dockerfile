FROM alpine

RUN apk add python3

ADD utils/ /root/utils
ADD ./main.py /root/
ENV PYTHONPATH /root/

ENTRYPOINT [ "/root/main.py" ]
