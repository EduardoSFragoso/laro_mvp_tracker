FROM python:3.13.7-alpine
WORKDIR /app
COPY src ./
RUN pip3 install -r requirements.txt
ENV HEALTH_PORT=8080
CMD [ "python", "app.py"]
