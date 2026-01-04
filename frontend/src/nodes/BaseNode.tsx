import { Handle, Position } from 'reactflow';
import type { NodeStatus } from '../types';
import { BlockType } from '../types';

interface BaseNodeProps {
  data: {
    label: string;
    nodeType?: BlockType;
    status?: NodeStatus;
    error?: string;
    progress?: number;
  };
  selected?: boolean;
}

const statusColors: Record<NodeStatus, string> = {
  idle: 'bg-gray-100 border-gray-300',
  queued: 'bg-orange-100 border-orange-300',
  running: 'bg-purple-100 border-purple-300',
  success: 'bg-green-100 border-green-400',
  failed: 'bg-red-100 border-red-400',
};

const statusBadges: Record<NodeStatus, string> = {
  idle: '',
  queued: '⏳',
  running: '🔄',
  success: '✅',
  failed: '❌',
};

const blockTypeIcons: Record<BlockType, string> = {
  [BlockType.READ_CSV]: '📄',
  [BlockType.FILTER]: '🔍',
  [BlockType.ENRICH_LEAD]: '✨',
  [BlockType.FIND_EMAIL]: '📧',
  [BlockType.SAVE_CSV]: '💾',
};

export function BaseNode({ data, selected }: BaseNodeProps) {
  const status = data.status || 'idle';
  const borderColor = selected ? 'border-blue-500' : statusColors[status].split(' ')[1];
  const bgColor = statusColors[status].split(' ')[0];
  const showProgress = status === 'running' && data.progress !== undefined && data.progress !== null;

  return (
    <div
      className={`px-2 py-1 shadow-md rounded-md ${bgColor} border-2 ${borderColor} min-w-[90px]`}
    >
      <div className="flex items-center justify-between">
        <div className="font-semibold text-xs flex items-center gap-1">
          {data.nodeType && blockTypeIcons[data.nodeType] && (
            <span>{blockTypeIcons[data.nodeType]}</span>
          )}
          <span>{data.label}</span>
        </div>
        {statusBadges[status] && (
          <span className="text-xs">{statusBadges[status]}</span>
        )}
      </div>
      {showProgress && (
        <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-1.5 rounded-full transition-all duration-500 ease-out progress-bar-shimmer progress-bar-pulse"
            style={{ width: `${Math.min(100, Math.max(0, data.progress || 0))}%` }}
          />
        </div>
      )}
      {data.error && (
        <div className="mt-1 text-xs text-red-600 truncate" title={data.error}>
          {data.error}
        </div>
      )}
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}

