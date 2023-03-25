FROM python:3.10

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

RUN mkdir /app
COPY ./requirements.txt /app
WORKDIR /app
RUN pip install -r ./requirements.txt
COPY . /app

CMD ["python3", "/app/main.py"]
