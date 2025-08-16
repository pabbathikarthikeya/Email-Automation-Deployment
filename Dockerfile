# Step 1: Specify the base image (Updated to Python 3.11)
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Install the spaCy model
RUN python -m spacy download en_core_web_sm

# Step 5: Copy your application code into the container
COPY . .

# Step 6: Define the command that runs your application (Updated to mailapp.py)
CMD ["python", "mailapp.py"]