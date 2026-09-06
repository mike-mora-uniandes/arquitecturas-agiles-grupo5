FROM solventa/flask-base:latest

WORKDIR /backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /backend/

EXPOSE 5000
CMD ["sh", "run.sh"]
