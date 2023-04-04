FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --requirement ./requirements.txt
COPY iam_killer.py .
CMD ["python", "iam_killer.py"]
