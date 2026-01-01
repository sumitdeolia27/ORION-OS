# ORION OS Navigator - Backend Connection Guide

This guide explains how to connect the Next.js frontend to the Python backend.

## Architecture

- **Frontend**: Next.js application (runs on port 3000)
- **Backend**: Flask API server (runs on port 5000)
- **Connection**: Next.js API routes proxy requests to Flask backend

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install flask flask-cors
```

### 2. Start the Backend Server

```bash
python scripts/api_server.py
```

The server will start on `http://localhost:5000`

You should see:
```
============================================================
ORION OS Navigator API Server
============================================================
Starting server on http://localhost:5000
Press Ctrl+C to stop
============================================================
```

### 3. Start the Frontend

In a separate terminal:

```bash
npm run dev
# or
pnpm dev
```

The frontend will start on `http://localhost:3000`

### 4. Configure Backend URL (Optional)

By default, the Next.js API routes connect to `http://localhost:5000`.

To change this, create a `.env.local` file in the project root:

```env
BACKEND_API_URL=http://localhost:5000
```

## API Endpoints

### Command Processing
- `POST /api/command` - Process a command
  ```json
  {
    "command": "take screenshot"
  }
  ```

### System Information
- `GET /api/system/info` - Get system information

### Tasks
- `GET /api/tasks` - Get all tasks
- `POST /api/tasks` - Add a new task

### Reminders
- `GET /api/reminders` - Get all reminders
- `POST /api/reminders` - Add a new reminder

### Notes
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Add a new note

### History
- `GET /api/history` - Get command history

## Testing the Connection

1. Start the backend server
2. Start the frontend
3. Open the browser console and check for any connection errors
4. Try typing a command in the command console (e.g., "time", "screenshot", "help")

## Troubleshooting

### Backend not responding
- Make sure the Flask server is running on port 5000
- Check if port 5000 is already in use: `netstat -ano | findstr :5000` (Windows) or `lsof -i :5000` (Mac/Linux)
- Check the backend console for error messages

### CORS errors
- The Flask server has CORS enabled, but if you see CORS errors, make sure `flask-cors` is installed

### Connection refused
- Verify the backend URL in `.env.local` matches where the Flask server is running
- Check firewall settings

### Command not working
- Check the backend console for Python errors
- Some commands require system permissions (e.g., volume control, screenshots)
- Make sure all Python dependencies are installed

## Development

### Running Both Servers

You can run both servers in separate terminals, or use a process manager like `concurrently`:

```bash
npm install -D concurrently
```

Then add to `package.json`:
```json
{
  "scripts": {
    "dev:all": "concurrently \"npm run dev\" \"python scripts/api_server.py\""
  }
}
```

Run with:
```bash
npm run dev:all
```

