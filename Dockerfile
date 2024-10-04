# Step 1: Use an official Python runtime as the base image
FROM python:3.9-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the project’s requirements file
COPY requirements.txt .

# Step 4: Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Step 5: Copy the entire Django project to the working directory
COPY . .

# Step 6: Set environment variables (for Django settings)
# These can be overridden when running the container
ENV DJANGO_SETTINGS_MODULE=api.settings
ENV PYTHONUNBUFFERED=1

# Step 7: Expose port 8000 (the default port Django runs on)
EXPOSE 8000

# Step 8: Run migrations and collect static files
RUN python manage.py collectstatic --noinput

# Step 9: Specify the command to run the Django app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "pdf_management.wsgi:application"]
