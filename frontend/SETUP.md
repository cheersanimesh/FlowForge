# Frontend Setup Instructions

## Quick Start

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to `http://localhost:3000`

## Backend Requirements

The frontend expects the backend to be running on `http://localhost:8000`. 

### Static File Serving (Optional but Recommended)

For preview files and CSV downloads to work, the backend should serve static files from the `runs/` directory. You can add this to your FastAPI backend:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/runs", StaticFiles(directory="runs"), name="runs")
```

Alternatively, you can create download endpoints in the backend that serve the files.

## Features Implemented

✅ Visual DAG editor with React Flow
✅ Block palette (click to add nodes)
✅ Node configuration forms for all block types
✅ Edge validation (max 1 incoming edge, no cycles)
✅ Source node validation (must be Read CSV)
✅ Workflow execution with status updates
✅ Preview data viewing
✅ CSV download functionality
✅ Sample workflow loader
✅ Error handling and validation messages
✅ Toast notifications

## Project Structure

```
frontend/
├── src/
│   ├── components/      # UI components
│   ├── nodes/          # React Flow node components
│   ├── api/            # API client & hooks
│   ├── state/          # Zustand store
│   └── types.ts        # TypeScript types
├── package.json
├── vite.config.ts      # Vite config with proxy
└── tailwind.config.js  # Tailwind CSS config
```

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

