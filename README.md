# BellFlow API

A simple FastAPI application with sample CRUD endpoints for the BellFlow project.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

#### For Windows with WSL, macOS, and Linux

1. **Navigate to the backend directory:**
   ```bash
   cd src/backend
   ```

2. **Windows only, run WSL:**
   ```bash
   wsl
   ```

3. **Check Python installation:**
   ```bash
   python3 --version
   ```
   If Python is not installed:
   - **WSL/Linux:** `sudo apt update && sudo apt install python3 python3-pip python3-venv`
   - **macOS:** `brew install python3`

4. **Make scripts executable (macOS/Linux only):**
   ```bash
   chmod +x setup.sh run.sh
   ```

5. **Set up the application:**
   ```bash
   bash setup.sh
   ```

6. **Run the application:**
   ```bash
   bash run.sh
   ```

## 🌐 Accessing the API

Once the application is running:

- **API Base URL:** `http://localhost:8000`
- **Interactive API Documentation:** `http://localhost:8000/docs`
- **Alternative API Documentation:** `http://localhost:8000/redoc`

## 📚 Available Endpoints

### Health Check
- `GET /` - Main health check endpoint
- `GET /health` - Alternative health check endpoint

### Items API
- `GET /api/items` - Get all items
- `GET /api/items/{item_id}` - Get specific item by ID
- `POST /api/items` - Create a new item
- `PUT /api/items/{item_id}` - Update an existing item
- `DELETE /api/items/{item_id}` - Delete an item
- `POST /api/items/seed` - Add sample data for testing

## 🛠️ Manual Setup (Alternative)

If the automated scripts don't work:

1. **Create and activate virtual environment:**
   ```bash
   cd src/backend
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🧪 Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/

# Get all items
curl http://localhost:8000/api/items

# Create a new item
curl -X POST "http://localhost:8000/api/items" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Item", "description": "A test item", "price": 99.99, "is_available": true}'

# Add sample data
curl -X POST "http://localhost:8000/api/items/seed"
```

### Using the Interactive Documentation

Visit `http://localhost:8000/docs` in your browser to test all endpoints interactively.

## 🔧 Troubleshooting

### Common Issues

1. **Permission denied on scripts:**
   ```bash
   chmod +x setup.sh run.sh
   ```

2. **Python not found:**
   - Make sure Python 3.8+ is installed
   - Try using `python` instead of `python3`

3. **Port already in use:**
   - Kill the process using the port: `lsof -ti:8000 | xargs kill -9`
   - Or change the port in `run.sh`

4. **Virtual environment issues:**
   - Delete the `venv` folder and run `setup.sh` again
   - Make sure you're in the `src/backend` directory