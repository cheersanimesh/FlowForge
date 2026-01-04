"""
FastAPI application for workflow engine.
"""
import uuid
from pathlib import Path
import logging
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from models import WorkflowSpec, RunResponse
from core.context import RunContext
from core.context_utils import sanitize_id
from workflow import execute_workflow
from workflow.workflow_dag_setup import setup_and_validate_dag
from workflow.workflow_response import initialize_components
import pandas as pd
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Workflow Engine", version="1.0.0")

origins = [
    'http://localhost:3000',
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allows the specified origins
    allow_credentials=True,         # Allows cookies/authorization headers to be included in requests
    allow_methods=["*"],            # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],            # Allows all headers
)
# Workspace directory
WORKSPACE_DIR = Path("./runs")
WORKSPACE_DIR.mkdir(exist_ok=True)

# Uploads directory for CSV files
UPLOADS_DIR = Path("./uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


def run_workflow_background(spec: WorkflowSpec, run_id: str):
    """Background task to execute workflow."""
    try:
        run_ctx = RunContext(run_id, str(WORKSPACE_DIR))
        execute_workflow(spec, run_ctx, WORKSPACE_DIR)
    except Exception as e:
        logger.error(f"Error executing workflow {run_id}: {e}", exc_info=True)


@app.post("/run")
async def run_workflow(spec: WorkflowSpec, background_tasks: BackgroundTasks):
    """
    Start a workflow execution.
    
    Uses DAG format (nodes + edges).
    Returns run_id immediately. Use GET /run/{run_id} to poll for status.
    """
    run_id = str(uuid.uuid4())
    
    # Initialize run context
    run_ctx = RunContext(run_id, str(WORKSPACE_DIR))
    
    # Parse spec to get nodes and initialize components
    try:
        nodes, edges, sources, sinks, error_response = setup_and_validate_dag(spec, run_ctx)
        if error_response:
            # Save error state
            error_response.run_id = run_id
            error_state = error_response.model_dump()
            run_ctx.save_state(error_state)
            return {"run_id": run_id}
        
        # Initialize all components with queued status
        initial_response = initialize_components(nodes, sources, sinks)
        initial_response.run_id = run_id
        initial_response.status = "queued"
        initial_state = initial_response.model_dump()
        run_ctx.save_state(initial_state)
    except Exception as e:
        # If parsing fails, save basic error state
        logger.error(f"Error parsing workflow spec for {run_id}: {e}", exc_info=True)
        error_response = RunResponse(
            run_id=run_id,
            status="failed",
            nodes=None,
            sources=None,
            sinks=None,
            outputs=None,
            error={"message": str(e), "trace": None}
        )
        error_state = error_response.model_dump()
        run_ctx.save_state(error_state)
        return {"run_id": run_id}
    
    # Execute workflow in background
    background_tasks.add_task(run_workflow_background, spec, run_id)
    
    return {"run_id": run_id}


@app.get("/run/{run_id}", response_model=RunResponse)
async def get_workflow_status(run_id: str):
    """
    Get the current status of a workflow execution.
    
    Returns the current state of the workflow execution, including:
    - Status (queued, running, success, failed)
    - Node/block results
    - Output paths
    - Error information (if any)
    """
    run_ctx = RunContext(run_id, str(WORKSPACE_DIR))
    state = run_ctx.load_state()
    
    if state is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Convert state dict back to RunResponse model
    return RunResponse(**state)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file.
    
    Returns the file path (relative to backend working directory) that can be used in read_csv blocks.
    Works correctly even when frontend and backend are on different servers.
    """
    # Validate file extension
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Generate unique filename to avoid collisions
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOADS_DIR / f"{file_id}{file_extension}"
    
    # Ensure uploads directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Return relative path (relative to backend working directory)
        # This path will work when the workflow runs on the backend
        relative_path = str(file_path)
        logger.info(f"File uploaded: {file.filename} -> {relative_path}")
        
        return {"path": relative_path, "filename": file.filename}
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}", exc_info=True)
        # Clean up partial file if it exists
        if file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Download a file from the backend.
    
    The file_path should be relative to the backend's working directory.
    Common paths include:
    - runs/{run_id}/output.csv
    - uploads/{file_id}.csv
    """
    try:
        # Security: prevent directory traversal and absolute paths
        if '..' in file_path or file_path.startswith('/'):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Resolve the path relative to current directory
        base_dir = Path.cwd()
        full_path = (base_dir / file_path).resolve()
        
        # Security: ensure resolved path is still within the base directory
        try:
            full_path.relative_to(base_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file path: outside allowed directory")
        
        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Get filename for download
        filename = full_path.name
        
        return FileResponse(
            path=full_path,
            filename=filename,
            media_type='text/csv'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.get("/get_result")
async def get_node_csv(
    node_id: str = Query(..., description="The ID of the node to download CSV for"),
    run_id: Optional[str] = Query(None, description="The run ID (optional, will search if not provided)")
):
    """
    Download the CSV output for a completed or partially completed node.
    
    The endpoint accepts a node_id and optionally a run_id. If run_id is not provided,
    it will search through recent runs to find the node.
    
    Returns the CSV file for the specified node.
    """
    try:
        # If run_id is provided, use it directly
        if run_id:
            run_ctx = RunContext(run_id, str(WORKSPACE_DIR))
            parquet_path = run_ctx.workspace_dir / f"node_{sanitize_id(node_id)}.parquet"
            print(f'parquet path : {parquet_path}')
            if not parquet_path.exists():
                raise HTTPException(
                    status_code=404, 
                    detail=f"Node output not found for node_id={node_id} in run_id={run_id}"
                )
            
            # Load parquet and convert to CSV
            df = pd.read_parquet(parquet_path)
            
            # Convert DataFrame to CSV bytes
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_buffer.seek(0)
            
            # Return CSV as streaming response
            return StreamingResponse(
                csv_buffer,
                media_type='text/csv',
                headers={
                    "Content-Disposition": f'attachment; filename="node_{sanitize_id(node_id)}.csv"'
                }
            )
        else:
            # Search through runs to find the node
            # This is less efficient but allows the frontend to only provide node_id
            if not WORKSPACE_DIR.exists():
                raise HTTPException(status_code=404, detail="No runs found")
            
            # Search through all run directories
            for run_dir in sorted(WORKSPACE_DIR.iterdir(), reverse=True):  # Most recent first
                if not run_dir.is_dir():
                    continue
                
                potential_run_id = run_dir.name
                run_ctx = RunContext(potential_run_id, str(WORKSPACE_DIR))
                parquet_path = run_ctx.workspace_dir / f"node_{sanitize_id(node_id)}.parquet"
                
                if parquet_path.exists():
                    # Found it! Load and return
                    df = pd.read_parquet(parquet_path)
                    
                    # Convert DataFrame to CSV bytes
                    csv_buffer = io.BytesIO()
                    df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    csv_buffer.seek(0)
                    
                    # Return CSV as streaming response
                    return StreamingResponse(
                        csv_buffer,
                        media_type='text/csv',
                        headers={
                            "Content-Disposition": f'attachment; filename="node_{sanitize_id(node_id)}.csv"'
                        }
                    )
            
            # Node not found in any run
            raise HTTPException(
                status_code=404,
                detail=f"Node output not found for node_id={node_id} in any run"
            )
            
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting node CSV for node_id={node_id}, run_id={run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting node CSV: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

