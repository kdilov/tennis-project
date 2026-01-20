# Start from Python 3.11 slim image (smaller than full image)
FROM python:3.11-slim

# Set working directory
WORKDIR /app


# The installer requires curl (and certificates) to download the release archive
RUN pip install uv

# Copy dependency files first (pyproject.toml, uv.lock)
# This layer gets cached if dependencies don't change

COPY pyproject.toml uv.lock ./ 

# Install dependencies using uv

RUN uv sync --frozen

# Copy the rest of your application code

COPY . . 

# Expose port 8003
EXPOSE 8003

# Command to run the app with uvicorn
# Hint: use "uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
# The --host 0.0.0.0 is important - it allows connections from outside the container

CMD ["uv", "run","python","-m","uvicorn",  "app.main:app","--host","0.0.0.0", "--port", "8003"]