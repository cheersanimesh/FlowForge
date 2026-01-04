import { useState, useMemo } from 'react';
import { useWorkflowStore } from '../state/useWorkflowStore';

export function WorkflowConfigViewer() {
  const { nodes, edges } = useWorkflowStore();
  const [isExpanded, setIsExpanded] = useState(true);

  const workflowConfig = useMemo(() => {
    return {
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
  }, [nodes, edges]);

  const configJson = JSON.stringify(workflowConfig, null, 2);

  return (
    <div className="border border-gray-200 rounded-lg bg-gray-50">
      <div 
        className="px-4 py-2 bg-gray-100 border-b border-gray-200 rounded-t-lg cursor-pointer hover:bg-gray-200 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-700">Current Workflow Config</h3>
            <p className="text-xs text-gray-500 mt-1">
              This is the configuration that will be sent to the backend
            </p>
          </div>
          <button
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            <svg
              className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
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
      {isExpanded && (
        <div className="p-4">
          {nodes.length === 0 ? (
            <div className="text-sm text-gray-500 italic">
              No nodes in workflow. Add nodes from the palette to see the config.
            </div>
          ) : (
            <pre className="text-xs bg-white border border-gray-200 rounded p-3 overflow-auto max-h-96 font-mono">
              {configJson}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

