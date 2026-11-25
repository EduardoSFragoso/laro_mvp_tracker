FROM python:3.15.2-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --chown=app:app src ./
RUN pip3 install --no-cache-dir -r requirements.lock
ENV HEALTH_PORT=8080
ENV PYTHONDONTWRITEBYTECODE=1
USER app
CMD [ "python", "app.py"]
