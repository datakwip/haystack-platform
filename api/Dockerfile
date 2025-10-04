FROM python:3.9.12
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
COPY ./setup.py /code/setup.py
#COPY ./gunicorn.conf.py /code/gunicorn.conf.py
COPY ./src/app/config.json /code/config.json
COPY ./src/app /code/app
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8087", "--log-level", "critical"]
#CMD ["gunicorn", "app.main:app", "--workers", "8", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", ":8087"]
CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", ":8087", "--timeout", "300"]
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8087"]
#CMD ["sleep", "infinity"]