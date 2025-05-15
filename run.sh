#!/bin/bash

# Show usage information
show_help() {
  echo "FinOps360 Cost Analysis Dashboard"
  echo "--------------------------------"
  echo "Usage: ./run.sh [options]"
  echo ""
  echo "Options:"
  echo "  --help          Show this help message"
  echo "  --dev           Run in development mode with auto-reload"
  echo "  --port=PORT     Specify the port to run on (default: 8080)"
  echo "  --workers=N     Specify the number of workers (default: based on CPU count)"
  echo "  --sample        Use sample data instead of BigQuery"
  echo ""
  echo "Examples:"
  echo "  ./run.sh                           # Run in production mode on port 8080"
  echo "  ./run.sh --dev                     # Run in development mode with auto-reload"
  echo "  ./run.sh --port=8081               # Run on port 8081"
  echo "  ./run.sh --dev --port=8081         # Run in development mode on port 8081"
  echo "  ./run.sh --sample                  # Use sample data (no BigQuery credentials needed)"
  echo ""
}

# Set environment variables
export PYTHONPATH="$(pwd)"

# Get arguments
PORT=${1:-8080}
WORKERS=${2:-0}  # 0 means auto-detect based on CPU count
RELOAD=0
USE_SAMPLE_DATA=0

# Parse options
while [[ $# -gt 0 ]]; do
  case $1 in
    --help)
      show_help
      exit 0
      ;;
    --dev)
      RELOAD=1
      shift
      ;;
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --workers=*)
      WORKERS="${1#*=}"
      shift
      ;;
    --sample)
      USE_SAMPLE_DATA=1
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# Set up virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for BigQuery credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✓ Using Google Application Credentials from: $GOOGLE_APPLICATION_CREDENTIALS"
else
    echo "⚠ No Google Application Credentials found"
    echo "Using sample data"
fi

# Ensure all dependencies are installed in the virtual environment
echo "Installing/updating dependencies..."
pip install --upgrade -r requirements.txt

# Check if db-dtypes is installed (critical for BigQuery data handling)
if ! pip list | grep -q "db-dtypes"; then
    echo "⚠️ db-dtypes package not found. Installing now..."
    pip install db-dtypes>=1.1.1
fi

# Set default to use sample data if flag is provided or no credentials exist
USE_SAMPLE_DATA=0
if [[ "$@" == *"--sample"* ]] || [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    USE_SAMPLE_DATA=1
    echo "🧪 Using sample data mode"
    
    # Clear any existing credentials to force sample data usage
    unset GOOGLE_APPLICATION_CREDENTIALS
fi

# Run the application
if [ $RELOAD -eq 1 ]; then
    echo "Starting in development mode with auto-reload..."
    python -m app --port $PORT --reload
else
    if [ $WORKERS -eq 0 ]; then
        echo "Starting in production mode..."
        python -m app --port $PORT
    else
        echo "Starting in production mode with $WORKERS workers..."
        python -m app --port $PORT --workers $WORKERS
    fi
fi
