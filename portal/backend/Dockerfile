FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI binary directly (avoids apt slowness in slim images)
RUN python -c "import urllib.request, tarfile, io, os; \
    url='https://download.docker.com/linux/static/stable/x86_64/docker-26.1.3.tgz'; \
    data=urllib.request.urlopen(url).read(); \
    tf=tarfile.open(fileobj=io.BytesIO(data), mode='r:gz'); \
    member=tf.getmember('docker/docker'); f=tf.extractfile(member); \
    open('/usr/local/bin/docker','wb').write(f.read()); \
    os.chmod('/usr/local/bin/docker', 0o755)"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
