# Use Python 3.12 for better stability, or stay on 3.14 if you prefer
FROM python:3.12-slim

# 1. Install system dependencies for SciPy
RUN apt-get update && apt-get install -y \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your code
COPY . .

# 5. Expose the port Render uses
EXPOSE 10000

# 6. Start command
# Since your main logic is likely in backend/ or start.py, 
# adjust 'start:app' to wherever your FastAPI/Flask app instance is.
CMD ["python", "start.py"]
