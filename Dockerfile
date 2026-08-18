FROM python:3.10-slim

# Install git and other system dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

COPY . /code/

EXPOSE 7860

# Run the Gradio app directly
CMD ["python", "app.py"]






# # Use the official Python image as base (Hugging Face defaults to Python 3.10+)
# FROM python:3.10-slim

# # Install system dependencies: git (for cloning repos) and any others if needed
# RUN apt-get update && \
#     apt-get install -y git && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Set working directory
# WORKDIR /code

# # Copy requirements first for better caching
# COPY requirements.txt /code/requirements.txt

# # Install Python dependencies
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir -r /code/requirements.txt

# # Copy the rest of the application code
# COPY . /code/

# # Expose the port Hugging Face expects
# EXPOSE 7860

# # Run the FastAPI app with Uvicorn (adjust 'app:app' if your file/module name differs)
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--reload"]