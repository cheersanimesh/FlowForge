import { useState, useEffect } from 'react';
import { getBackendUrl, setBackendUrl } from '../utils/backendConfig';
import { WorkflowConfigViewer } from './WorkflowConfigViewer';
import toast from 'react-hot-toast';

export function SettingsPanel() {
  const [isExpanded, setIsExpanded] = useState(true);
  const [backendUrl, setBackendUrlState] = useState<string>(getBackendUrl());

  useEffect(() => {
    setBackendUrlState(getBackendUrl());
  }, []);

  const handleBackendUrlChange = (url: string) => {
    setBackendUrlState(url);
    setBackendUrl(url);
    toast.success('Backend URL updated');
  };

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 flex flex-col flex-shrink-0">
      <div 
        className="px-4 py-3 bg-gray-100 border-b border-gray-200 cursor-pointer hover:bg-gray-200 transition-colors flex-shrink-0"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-700">Settings</h2>
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
        <div className="overflow-y-auto p-4 space-y-4" style={{ maxHeight: '40vh' }}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Backend URL:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => setBackendUrlState(e.target.value)}
                onBlur={(e) => handleBackendUrlChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleBackendUrlChange(backendUrl);
                  }
                }}
                placeholder="http://localhost:8000"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Enter the backend URL where workflow requests will be sent
            </p>
          </div>
          
          <div>
            <WorkflowConfigViewer />
          </div>
        </div>
      )}
    </div>
  );
}

