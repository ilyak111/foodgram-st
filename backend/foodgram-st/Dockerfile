FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
RUN pip install gunicorn
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"] 
