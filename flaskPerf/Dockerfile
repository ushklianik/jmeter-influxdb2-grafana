FROM python:3.9
WORKDIR /flaskPerf
COPY requirements.txt /flaskPerf
RUN pip3 install --upgrade pip -r requirements.txt
COPY . /flaskPerf
EXPOSE 5000