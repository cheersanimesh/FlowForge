import { useCallback, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useWorkflowStore } from '../state/useWorkflowStore';
import { ReadCsvNode } from '../nodes/ReadCsvNode';
import { FilterNode } from '../nodes/FilterNode';
import { EnrichLeadNode } from '../nodes/EnrichLeadNode';
import { FindEmailNode } from '../nodes/FindEmailNode';
import { SaveCsvNode } from '../nodes/SaveCsvNode';
import toast from 'react-hot-toast';

const nodeTypes = {
  'read-csv': ReadCsvNode,
  'filter': FilterNode,
  'enrich-lead': EnrichLeadNode,
  'find-email': FindEmailNode,
  'save-csv': SaveCsvNode,
};

export function FlowCanvas() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect: storeOnConnect,
    setSelectedNode,
    deleteNode,
  } = useWorkflowStore();

  // Debug: log nodes when they change
  useEffect(() => {
    console.log('FlowCanvas nodes:', nodes);
  }, [nodes]);

  const onConnect = useCallback(
    (connection: Connection) => {
      try {
        storeOnConnect(connection);
        toast.success('Connection created');
      } catch (error: any) {
        toast.error(error.message || 'Failed to create connection');
      }
    },
    [storeOnConnect]
  );

  const onNodeClick = useCallback(
    (_: any, node: any) => {
      setSelectedNode(node.id);
    },
    [setSelectedNode]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  const onNodesDelete = useCallback(
    (deleted: any[]) => {
      deleted.forEach((node) => deleteNode(node.id));
    },
    [deleteNode]
  );

  return (
    <div className="flex-1 h-full" style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onNodesDelete={onNodesDelete}
        nodeTypes={nodeTypes}
        fitView
        deleteKeyCode={['Backspace', 'Delete']}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}

