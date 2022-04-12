FROM python:3.10

WORKDIR /home/app

COPY *.py requirements.txt ./
RUN apt-get update
RUN apt-get install latexmk
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "start.py"]
