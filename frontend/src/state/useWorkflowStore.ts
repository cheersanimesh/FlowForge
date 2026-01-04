import { create } from 'zustand';
import { nanoid } from 'nanoid';
import { BlockType } from '../types';
import type { NodeParams, NodeStatus } from '../types';
import { 
  Node as ReactFlowNode, 
  Edge as ReactFlowEdge,
  Connection,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
} from 'reactflow';

interface WorkflowStore {
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
  selectedNodeId: string | null;
  nodeStatuses: Record<string, NodeStatus>;
  nodeErrors: Record<string, string>;
  
  // Actions
  setNodes: (nodes: ReactFlowNode[]) => void;
  setEdges: (edges: ReactFlowEdge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  addNode: (type: BlockType, position: { x: number; y: number }) => string;
  updateNodeParams: (nodeId: string, params: NodeParams) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setNodeStatus: (nodeId: string, status: NodeStatus, progress?: number) => void;
  setNodeError: (nodeId: string, error: string | null) => void;
  clearStatuses: () => void;
  loadSampleWorkflow: () => void;
  deleteNode: (nodeId: string) => void;
}

const getDefaultParams = (type: BlockType): NodeParams => {
  switch (type) {
    case BlockType.READ_CSV:
      return { path: 'input.csv' };
    case BlockType.FILTER:
      return { mode: 'rules', rules: [], combine: 'and' };
    case BlockType.ENRICH_LEAD:
      return {
        lead_mapping: {},
        struct: {},
        output_prefix: 'enrich_',
      };
    case BlockType.FIND_EMAIL:
      return {
        lead_mapping: {},
        mode: 'PROFESSIONAL',
        output_prefix: 'email_',
      };
    case BlockType.SAVE_CSV:
      return { path: 'runs/{run_id}/output.csv' };
    default:
      return {};
  }
};

const getNodeLabel = (type: BlockType): string => {
  switch (type) {
    case BlockType.READ_CSV:
      return 'Read CSV';
    case BlockType.FILTER:
      return 'Filter';
    case BlockType.ENRICH_LEAD:
      return 'Enrich Lead';
    case BlockType.FIND_EMAIL:
      return 'Find Email';
    case BlockType.SAVE_CSV:
      return 'Save CSV';
    default:
      return type;
  }
};

export const useWorkflowStore = create<WorkflowStore>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  nodeStatuses: {},
  nodeErrors: {},

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection) => {
    const { edges, nodes } = get();
    
    // Validate connection has required fields
    if (!connection.source || !connection.target) {
      throw new Error('Invalid connection: source and target are required');
    }
    
    // Check if target already has an incoming edge
    const hasIncoming = edges.some(e => e.target === connection.target);
    if (hasIncoming) {
      throw new Error('Node can only have one incoming edge');
    }

    // Check for cycles
    const wouldCreateCycle = checkCycle(
      nodes,
      [...edges, { ...connection, id: `e${connection.source}-${connection.target}` } as ReactFlowEdge]
    );
    if (wouldCreateCycle) {
      throw new Error('This connection would create a cycle');
    }

    set({
      edges: addEdge(connection, edges),
    });
  },

  addNode: (type, position) => {
    const id = nanoid();
    const node: ReactFlowNode = {
      id,
      type: type.toLowerCase().replace(/_/g, '-'),
      position,
      data: {
        label: getNodeLabel(type),
        nodeType: type,
        params: getDefaultParams(type),
        status: 'idle',
      },
    };
    set({
      nodes: [...get().nodes, node],
    });
    return id;
  },

  updateNodeParams: (nodeId, params) => {
    set({
      nodes: get().nodes.map(node =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, params } }
          : node
      ),
    });
  },

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),

  setNodeStatus: (nodeId, status, progress) => {
    set({
      nodeStatuses: { ...get().nodeStatuses, [nodeId]: status },
      nodes: get().nodes.map(node =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, status, progress } }
          : node
      ),
    });
  },

  setNodeError: (nodeId, error) => {
    if (error) {
      set({
        nodeErrors: { ...get().nodeErrors, [nodeId]: error },
      });
    } else {
      const { [nodeId]: _, ...rest } = get().nodeErrors;
      set({ nodeErrors: rest });
    }
  },

  clearStatuses: () => {
    set({
      nodeStatuses: {},
      nodeErrors: {},
      nodes: get().nodes.map(node => ({
        ...node,
        data: { ...node.data, status: 'idle' as NodeStatus, error: undefined, progress: undefined },
      })),
    });
  },

  loadSampleWorkflow: () => {
    // Use fixed IDs to match the workflow specification
    const readId = 'read1';
    const filterId = 'filter1';
    const enrichId = 'enrich1';
    const findEmailId = 'find_email1';
    const save1Id = 'save1';
    const save2Id = 'save2';

    const nodes: ReactFlowNode[] = [
      {
        id: readId,
        type: 'read-csv',
        position: { x: 100, y: 200 },
        data: {
          label: 'Read CSV',
          nodeType: BlockType.READ_CSV,
          params: { 
            path: '/Users/animeshmishra/Desktop/Projects/sixtyFour/first_attempt/input_updated.csv' 
          },
          status: 'idle',
        },
      },
      {
        id: filterId,
        type: 'filter',
        position: { x: 300, y: 200 },
        data: {
          label: 'Filter',
          nodeType: BlockType.FILTER,
          params: { 
            mode: 'rules', 
            rules: [
              {
                col: 'company',
                op: 'contains',
                value: 'Graham-Francis',
              },
            ], 
            combine: 'and' 
          },
          status: 'idle',
        },
      },
      {
        id: enrichId,
        type: 'enrich-lead',
        position: { x: 500, y: 100 },
        data: {
          label: 'Enrich Lead',
          nodeType: BlockType.ENRICH_LEAD,
          params: {
            lead_mapping: {
              name: 'name',
              company: 'company',
            },
            struct: {
              industry: 'What industry is this company in?',
              linkedin: 'LinkedIn URL for the person',
            },
            output_prefix: 'enrich_',
          },
          status: 'idle',
        },
      },
      {
        id: findEmailId,
        type: 'find-email',
        position: { x: 500, y: 300 },
        data: {
          label: 'Find Email',
          nodeType: BlockType.FIND_EMAIL,
          params: {
            lead_mapping: {
              name: 'name',
              company: 'company',
            },
            mode: 'PROFESSIONAL',
            output_prefix: 'email_',
          },
          status: 'idle',
        },
      },
      {
        id: save1Id,
        type: 'save-csv',
        position: { x: 700, y: 100 },
        data: {
          label: 'Save CSV',
          nodeType: BlockType.SAVE_CSV,
          params: { path: 'runs/{run_id}/enriched_output.csv' },
          status: 'idle',
        },
      },
      {
        id: save2Id,
        type: 'save-csv',
        position: { x: 700, y: 300 },
        data: {
          label: 'Save CSV',
          nodeType: BlockType.SAVE_CSV,
          params: { path: 'runs/{run_id}/emails_output.csv' },
          status: 'idle',
        },
      },
    ];

    const edges: ReactFlowEdge[] = [
      { id: `e${readId}-${filterId}`, source: readId, target: filterId },
      { id: `e${filterId}-${enrichId}`, source: filterId, target: enrichId },
      { id: `e${filterId}-${findEmailId}`, source: filterId, target: findEmailId },
      { id: `e${enrichId}-${save1Id}`, source: enrichId, target: save1Id },
      { id: `e${findEmailId}-${save2Id}`, source: findEmailId, target: save2Id },
    ];

    set({ nodes, edges, selectedNodeId: null });
  },

  deleteNode: (nodeId) => {
    const { nodes, edges } = get();
    set({
      nodes: nodes.filter(n => n.id !== nodeId),
      edges: edges.filter(e => e.source !== nodeId && e.target !== nodeId),
      selectedNodeId: get().selectedNodeId === nodeId ? null : get().selectedNodeId,
    });
  },
}));

// Cycle detection using DFS
function checkCycle(nodes: ReactFlowNode[], edges: ReactFlowEdge[]): boolean {
  const graph: Record<string, string[]> = {};
  nodes.forEach(node => {
    graph[node.id] = [];
  });
  edges.forEach(edge => {
    if (!graph[edge.source]) graph[edge.source] = [];
    graph[edge.source].push(edge.target);
  });

  const visited = new Set<string>();
  const recStack = new Set<string>();

  const dfs = (nodeId: string): boolean => {
    if (recStack.has(nodeId)) return true;
    if (visited.has(nodeId)) return false;

    visited.add(nodeId);
    recStack.add(nodeId);

    const neighbors = graph[nodeId] || [];
    for (const neighbor of neighbors) {
      if (dfs(neighbor)) return true;
    }

    recStack.delete(nodeId);
    return false;
  };

  for (const nodeId of Object.keys(graph)) {
    if (!visited.has(nodeId)) {
      if (dfs(nodeId)) return true;
    }
  }

  return false;
}

