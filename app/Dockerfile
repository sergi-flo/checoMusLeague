# Use the official Python image as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /home

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the requirements file into the container
COPY . .

# Command to run your Flask app
CMD sh -c "python csv_to_sql.py; gunicorn --bind 0.0.0.0:5003 wsgi:app -c gunicorn.conf.py"
