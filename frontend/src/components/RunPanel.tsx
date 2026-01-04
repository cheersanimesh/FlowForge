import { useState, useMemo, useEffect, useRef } from 'react';
import { useWorkflowStore } from '../state/useWorkflowStore';
import { BlockType } from '../types';
import { startWorkflowRun, getWorkflowRunStatus, downloadFile, downloadNodeResult } from '../api/client';
import toast from 'react-hot-toast';

export function RunPanel() {
  const { nodes, edges, loadSampleWorkflow, clearStatuses, setNodeStatus, setNodeError } =
    useWorkflowStore();
  const [runResponse, setRunResponse] = useState<any>(null);
  const [isRunResultsExpanded, setIsRunResultsExpanded] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    
    // Check that all sources are Read CSV
    const sourceNodes = nodes.filter(
      (node) => !edges.some((edge) => edge.target === node.id)
    );
    for (const node of sourceNodes) {
      if (node.data.nodeType !== BlockType.READ_CSV) {
        errors.push(`Source node "${node.data.label}" must be a Read CSV node`);
      }
    }

    // Check that all nodes have valid params
    for (const node of nodes) {
      if (node.data.nodeType === BlockType.READ_CSV) {
        const params = node.data.params as { path?: string };
        if (!params.path || !params.path.trim()) {
          errors.push(`Node "${node.data.label}" requires a CSV path`);
        }
      }
    }

    return errors;
  }, [nodes, edges]);

  const isValid = validationErrors.length === 0 && nodes.length > 0;

  const pollWorkflowStatus = async (runId: string) => {
    try {
      const response = await getWorkflowRunStatus(runId);
      setRunResponse(response);

      // Update node statuses from response
      if (response.nodes) {
        response.nodes.forEach((nodeResult: any) => {
          setNodeStatus(nodeResult.id, nodeResult.status, nodeResult.progress);
          if (nodeResult.error) {
            setNodeError(nodeResult.id, nodeResult.error.message || nodeResult.error);
          } else {
            setNodeError(nodeResult.id, null);
          }
        });
      }

      // Stop polling if workflow is complete
      if (response.status === 'success' || response.status === 'failed') {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        setIsRunning(false);

        if (response.status === 'success') {
          toast.success('Workflow completed successfully!');
        } else {
          toast.error(`Workflow failed: ${response.error?.message || 'Unknown error'}`);
        }
      }
    } catch (error: any) {
      console.error('Error polling workflow status:', error);
      // Don't stop polling on error, just log it
      // The next poll will retry
    }
  };

  const handleRun = async () => {
    if (!isValid) {
      toast.error('Please fix validation errors before running');
      return;
    }

    // Stop any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    clearStatuses();
    setIsRunning(true);

    // Convert React Flow format to backend format
    const workflowSpec = {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.data.nodeType,
        params: node.data.params,
      })),
      edges: edges.map((edge) => ({
        from: edge.source,
        to: edge.target,
      })),
    };

    try {
      // Start the workflow run
      const startResponse = await startWorkflowRun(workflowSpec);
      const runId = startResponse.run_id;

      // Start polling immediately, then every 5 seconds
      pollWorkflowStatus(runId);
      pollingIntervalRef.current = setInterval(() => {
        pollWorkflowStatus(runId);
      }, 5000);
    } catch (error: any) {
      toast.error(`Failed to start workflow: ${error.message}`);
      setIsRunning(false);
      nodes.forEach((node) => {
        setNodeStatus(node.id, 'failed');
        setNodeError(node.id, error.message);
      });
    }
  };

  const handleDownload = async () => {
    if (!runResponse?.output_csv_path && !runResponse?.outputs) {
      toast.error('No output file available');
      return;
    }

    const outputPath = runResponse.output_csv_path || 
      (runResponse.outputs && Object.values(runResponse.outputs)[0] && 
        (Object.values(runResponse.outputs)[0] as { output_csv_path: string }).output_csv_path);
    
    if (!outputPath) {
      toast.error('No output file path found');
      return;
    }

    try {
      const filename = outputPath.split('/').pop() || 'output.csv';
      const blob = await downloadFile(outputPath, filename);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Download started');
    } catch (error: any) {
      console.error('Error downloading file:', error);
      toast.error(`Failed to download file: ${error.message || 'Unknown error'}`);
    }
  };

  const handleDownloadNodeResult = async (nodeId: string) => {
    if (!runResponse?.run_id) {
      toast.error('No run ID available');
      return;
    }

    try {
      const node = nodes.find((n) => n.id === nodeId);
      const nodeLabel = node?.data.label || nodeId;
      const filename = `${nodeLabel}_result.csv`;
      
      const blob = await downloadNodeResult(runResponse.run_id, nodeId, filename);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`Download started for ${nodeLabel}`);
    } catch (error: any) {
      console.error('Error downloading node result:', error);
      toast.error(`Failed to download result: ${error.message || 'Unknown error'}`);
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="border border-gray-200 rounded-lg bg-gray-50">
        <div 
          className="px-4 py-3 bg-gray-100 border-b border-gray-200 rounded-t-lg cursor-pointer hover:bg-gray-200 transition-colors"
          onClick={() => setIsRunResultsExpanded(!isRunResultsExpanded)}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Run / Results</h2>
            <div className="flex items-center gap-3">
              <div className="flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    loadSampleWorkflow();
                  }}
                  className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  Load Sample Workflow
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRun();
                  }}
                  disabled={!isValid || isRunning}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isRunning ? 'Running...' : 'Run Workflow'}
                </button>
              </div>
              <button
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
                aria-label={isRunResultsExpanded ? 'Collapse' : 'Expand'}
                onClick={(e) => {
                  e.stopPropagation();
                  setIsRunResultsExpanded(!isRunResultsExpanded);
                }}
              >
                <svg
                  className={`w-5 h-5 transition-transform ${isRunResultsExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {isRunResultsExpanded && (
          <div className="p-4">
            {validationErrors.length > 0 && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
                <div className="font-semibold text-red-800 mb-2">Validation Errors:</div>
                <ul className="list-disc list-inside text-sm text-red-700">
                  {validationErrors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {runResponse && (
              <div className="space-y-4">
          <div className="p-3 bg-gray-50 border border-gray-200 rounded">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="font-semibold">Status: </span>
                <span
                  className={
                    runResponse.status === 'success'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }
                >
                  {runResponse.status.toUpperCase()}
                </span>
                {runResponse.run_id && (
                  <span className="ml-4 text-sm text-gray-600">
                    Run ID: {runResponse.run_id}
                  </span>
                )}
              </div>
              {runResponse.status === 'success' && (
                <button
                  onClick={handleDownload}
                  className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Download CSV
                </button>
              )}
            </div>

            {runResponse.nodes && runResponse.nodes.length > 0 && (
              <div className="mt-3">
                <div className="font-semibold mb-2">Node Status:</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {runResponse.nodes.map((nodeResult: any) => {
                    const node = nodes.find((n) => n.id === nodeResult.id);
                    return (
                      <div
                        key={nodeResult.id}
                        className={`p-2 rounded ${
                          nodeResult.status === 'success'
                            ? 'bg-green-50'
                            : nodeResult.status === 'failed'
                            ? 'bg-red-50'
                            : 'bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium">
                              {node?.data.label || nodeResult.id}
                            </div>
                            <div className="text-xs text-gray-600">
                              Status: {nodeResult.status}
                              {nodeResult.progress !== undefined && nodeResult.progress !== null && (
                                <span className="ml-2">({nodeResult.progress.toFixed(1)}%)</span>
                              )}
                              {nodeResult.rows !== undefined && (
                                <span className="ml-2">({nodeResult.rows} rows)</span>
                              )}
                            </div>
                            {nodeResult.progress !== undefined && nodeResult.progress !== null && nodeResult.status === 'running' && (
                              <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${nodeResult.progress}%` }}
                                />
                              </div>
                            )}
                            {nodeResult.error && (
                              <div className="mt-1 text-xs text-red-600">
                                {nodeResult.error.message}
                              </div>
                            )}
                          </div>
                          {nodeResult.status === 'success' && runResponse.run_id && (
                            <button
                              onClick={() => handleDownloadNodeResult(nodeResult.id)}
                              className="ml-2 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                              title="Download Result"
                            >
                              Download
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {runResponse.error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                <div className="font-semibold text-red-800 mb-1">Error:</div>
                <div className="text-sm text-red-700">{runResponse.error.message}</div>
                {runResponse.error.trace && (
                  <details className="mt-2">
                    <summary className="text-xs text-red-600 cursor-pointer">
                      Show trace
                    </summary>
                    <pre className="mt-2 text-xs bg-red-100 p-2 rounded overflow-auto max-h-40">
                      {runResponse.error.trace}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>

              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

