import { useEffect, useState, useRef } from 'react';
import { useWorkflowStore } from '../state/useWorkflowStore';
import {
  BlockType,
  FilterParams,
  ReadCsvParams,
  EnrichLeadParams,
  FindEmailParams,
  SaveCsvParams,
  FilterOperator,
  FilterRule,
} from '../types';
import { uploadCsvFile } from '../api/client';

export function NodeInspector() {
  const { nodes, selectedNodeId, updateNodeParams } = useWorkflowStore();
  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  if (!selectedNode) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-200 p-4 flex-1 overflow-y-auto">
        <h2 className="text-lg font-bold mb-4 text-gray-700">Inspector</h2>
        <p className="text-sm text-gray-500">Select a node to configure</p>
      </div>
    );
  }

  const nodeType = selectedNode.data.nodeType;
  const params = selectedNode.data.params;

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 p-4 flex-1 overflow-y-auto">
      <h2 className="text-lg font-bold mb-4 text-gray-700">Inspector</h2>
      <div className="mb-2 text-sm text-gray-600">
        <strong>{selectedNode.data.label}</strong>
      </div>

      {nodeType === BlockType.READ_CSV && (
        <ReadCsvInspector
          params={params as ReadCsvParams}
          nodeId={selectedNode.id}
          onUpdate={updateNodeParams}
        />
      )}
      {nodeType === BlockType.FILTER && (
        <FilterInspector
          params={params as FilterParams}
          nodeId={selectedNode.id}
          onUpdate={updateNodeParams}
        />
      )}
      {nodeType === BlockType.ENRICH_LEAD && (
        <EnrichLeadInspector
          params={params as EnrichLeadParams}
          nodeId={selectedNode.id}
          onUpdate={updateNodeParams}
        />
      )}
      {nodeType === BlockType.FIND_EMAIL && (
        <FindEmailInspector
          params={params as FindEmailParams}
          nodeId={selectedNode.id}
          onUpdate={updateNodeParams}
        />
      )}
      {nodeType === BlockType.SAVE_CSV && (
        <SaveCsvInspector
          params={params as SaveCsvParams}
          nodeId={selectedNode.id}
          onUpdate={updateNodeParams}
        />
      )}
    </div>
  );
}

function ReadCsvInspector({
  params,
  nodeId,
  onUpdate,
}: {
  params: ReadCsvParams;
  nodeId: string;
  onUpdate: (nodeId: string, params: any) => void;
}) {
  const [path, setPath] = useState(params.path || '');
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync state when params change from outside (e.g., when switching nodes)
  useEffect(() => {
    setPath(params.path || '');
    setUploadedFileName(null);
  }, [params.path]);

  useEffect(() => {
    onUpdate(nodeId, { path });
  }, [path, nodeId, onUpdate]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const result = await uploadCsvFile(file);
      setPath(result.path);
      setUploadedFileName(result.filename);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert(`Error uploading file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
      // Reset the file input so the same file can be selected again if needed
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          CSV File
        </label>
        <div className="space-y-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv"
            className="hidden"
          />
          <button
            type="button"
            onClick={handleUploadClick}
            disabled={isUploading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed text-left"
          >
            {isUploading ? 'Uploading...' : uploadedFileName || 'Choose CSV file'}
          </button>
          {uploadedFileName && (
            <p className="text-xs text-gray-500">
              Uploaded: {uploadedFileName}
            </p>
          )}
        </div>
      </div>
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-gray-50 px-2 text-gray-500">Or</span>
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          CSV Path
        </label>
        <input
          type="text"
          value={path}
          onChange={(e) => {
            setPath(e.target.value);
            setUploadedFileName(null);
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          placeholder="input.csv or uploads/..."
        />
      </div>
    </div>
  );
}

function FilterInspector({
  params,
  nodeId,
  onUpdate,
}: {
  params: FilterParams;
  nodeId: string;
  onUpdate: (nodeId: string, params: any) => void;
}) {
  const [mode, setMode] = useState(params.mode || 'rules');
  const [rules, setRules] = useState<FilterRule[]>(params.rules || []);
  const [combine, setCombine] = useState<'and' | 'or'>(params.combine || 'and');
  const [expr, setExpr] = useState(params.expr || '');

  useEffect(() => {
    if (mode === 'rules') {
      onUpdate(nodeId, { mode, rules, combine });
    } else {
      onUpdate(nodeId, { mode, expr });
    }
  }, [mode, rules, combine, expr, nodeId, onUpdate]);

  const addRule = () => {
    setRules([...rules, { col: '', op: FilterOperator.CONTAINS, value: '' }]);
  };

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  const updateRule = (index: number, updates: Partial<FilterRule>) => {
    setRules(rules.map((r, i) => (i === index ? { ...r, ...updates } : r)));
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Mode
        </label>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as 'rules' | 'expr')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="rules">Rules</option>
          <option value="expr">Expression</option>
        </select>
      </div>

      {mode === 'rules' && (
        <>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Rules
              </label>
              <button
                onClick={addRule}
                className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                + Add Rule
              </button>
            </div>
            {rules.map((rule, index) => (
              <div key={index} className="mb-3 p-3 bg-white border rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-medium">Rule {index + 1}</span>
                  <button
                    onClick={() => removeRule(index)}
                    className="text-xs text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                </div>
                <div className="space-y-2">
                  <input
                    type="text"
                    value={rule.col}
                    onChange={(e) => updateRule(index, { col: e.target.value })}
                    placeholder="Column"
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                  <select
                    value={rule.op}
                    onChange={(e) =>
                      updateRule(index, { op: e.target.value as FilterOperator })
                    }
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    {Object.values(FilterOperator).map((op) => (
                      <option key={op} value={op}>
                        {op}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={rule.value || ''}
                    onChange={(e) => updateRule(index, { value: e.target.value })}
                    placeholder="Value"
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                </div>
              </div>
            ))}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Combine
            </label>
            <select
              value={combine}
              onChange={(e) => setCombine(e.target.value as 'and' | 'or')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="and">AND</option>
              <option value="or">OR</option>
            </select>
          </div>
        </>
      )}

      {mode === 'expr' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Expression
          </label>
          <textarea
            value={expr}
            onChange={(e) => setExpr(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            rows={3}
            placeholder="e.g., company == 'Tech'"
          />
        </div>
      )}
    </div>
  );
}

function EnrichLeadInspector({
  params,
  nodeId,
  onUpdate,
}: {
  params: EnrichLeadParams;
  nodeId: string;
  onUpdate: (nodeId: string, params: any) => void;
}) {
  const [leadMapping, setLeadMapping] = useState(params.lead_mapping || {});
  const [struct, setStruct] = useState(params.struct || {});
  const [researchPlan, setResearchPlan] = useState(params.research_plan || '');
  const [outputPrefix, setOutputPrefix] = useState(params.output_prefix || 'enrich_');
  const [editingKeys, setEditingKeys] = useState<Record<string, string>>({});

  // Sync state when params change from outside
  useEffect(() => {
    setLeadMapping(params.lead_mapping || {});
    setStruct(params.struct || {});
    setResearchPlan(params.research_plan || '');
    setOutputPrefix(params.output_prefix || 'enrich_');
    setEditingKeys({});
  }, [params.lead_mapping, params.struct, params.research_plan, params.output_prefix]);

  useEffect(() => {
    onUpdate(nodeId, {
      lead_mapping: leadMapping,
      struct,
      research_plan: researchPlan,
      output_prefix: outputPrefix,
    });
  }, [leadMapping, struct, researchPlan, outputPrefix, nodeId, onUpdate]);

  const updateMapping = (key: string, value: string) => {
    setLeadMapping({ ...leadMapping, [key]: value });
  };

  const updateStruct = (key: string, value: string) => {
    setStruct({ ...struct, [key]: value });
  };

  const removeStruct = (key: string) => {
    const { [key]: _, ...rest } = struct;
    setStruct(rest);
    // Clean up editing state
    const { [key]: __, ...restEditing } = editingKeys;
    setEditingKeys(restEditing);
  };

  const handleStructKeyChange = (oldKey: string, newKey: string) => {
    // Update the editing state to show what the user is typing
    setEditingKeys({ ...editingKeys, [oldKey]: newKey });
  };

  const handleStructKeyBlur = (oldKey: string) => {
    const editedKey = editingKeys[oldKey];
    if (editedKey !== undefined) {
      // Clean up editing state first
      const { [oldKey]: _, ...restEditing } = editingKeys;
      setEditingKeys(restEditing);
      
      // If the edited key is valid and different, update the struct
      if (editedKey && editedKey !== oldKey) {
        // Check if the new key already exists (and it's not the same as oldKey)
        if (struct[editedKey] && editedKey !== oldKey) {
          // Key already exists, revert
          return;
        }
        // Update the struct with the new key
        const { [oldKey]: oldValue, ...rest } = struct;
        setStruct({ ...rest, [editedKey]: oldValue });
      }
      // If editedKey is empty or same as oldKey, just clean up (no change needed)
    }
  };

  const standardFields = ['name', 'company', 'linkedin', 'email', 'domain'];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lead Mapping
        </label>
        {standardFields.map((field) => (
          <div key={field} className="mb-2">
            <label className="block text-xs text-gray-600 mb-1 capitalize">
              {field}
            </label>
            <input
              type="text"
              value={leadMapping[field] || ''}
              onChange={(e) => updateMapping(field, e.target.value)}
              placeholder={`Column name for ${field}`}
              className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Struct Fields
          </label>
          <button
            onClick={() => {
              const newKey = `field_${Object.keys(struct).length + 1}`;
              updateStruct(newKey, '');
            }}
            className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            + Add Field
          </button>
        </div>
        {Object.entries(struct).map(([key, value]) => {
          const displayKey = editingKeys[key] !== undefined ? editingKeys[key] : key;
          return (
            <div key={key} className="mb-2 p-2 bg-white border rounded">
              <div className="flex justify-between items-center mb-1">
                <input
                  type="text"
                  value={displayKey}
                  onChange={(e) => handleStructKeyChange(key, e.target.value)}
                  onBlur={() => handleStructKeyBlur(key)}
                  placeholder="Field name"
                  className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm mr-2"
                />
                <button
                  onClick={() => removeStruct(key)}
                  className="text-xs text-red-600 hover:text-red-800"
                >
                  ×
                </button>
              </div>
              <input
                type="text"
                value={value}
                onChange={(e) => updateStruct(key, e.target.value)}
                placeholder="Instruction"
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          );
        })}
        {Object.keys(struct).length === 0 && (
          <p className="text-xs text-gray-500 italic">No struct fields added yet</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Research Plan (optional)
        </label>
        <textarea
          value={researchPlan}
          onChange={(e) => setResearchPlan(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Output Prefix
        </label>
        <input
          type="text"
          value={outputPrefix}
          onChange={(e) => setOutputPrefix(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        />
      </div>
    </div>
  );
}

function FindEmailInspector({
  params,
  nodeId,
  onUpdate,
}: {
  params: FindEmailParams;
  nodeId: string;
  onUpdate: (nodeId: string, params: any) => void;
}) {
  const [leadMapping, setLeadMapping] = useState(params.lead_mapping || {});
  const [mode, setMode] = useState<'PROFESSIONAL' | 'PERSONAL'>(
    params.mode || 'PROFESSIONAL'
  );
  const [outputPrefix, setOutputPrefix] = useState(params.output_prefix || 'email_');

  useEffect(() => {
    onUpdate(nodeId, {
      lead_mapping: leadMapping,
      mode,
      output_prefix: outputPrefix,
    });
  }, [leadMapping, mode, outputPrefix, nodeId, onUpdate]);

  const updateMapping = (key: string, value: string) => {
    setLeadMapping({ ...leadMapping, [key]: value });
  };

  const fields = ['name', 'company', 'linkedin', 'domain'];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lead Mapping
        </label>
        {fields.map((field) => (
          <div key={field} className="mb-2">
            <label className="block text-xs text-gray-600 mb-1 capitalize">
              {field}
            </label>
            <input
              type="text"
              value={leadMapping[field] || ''}
              onChange={(e) => updateMapping(field, e.target.value)}
              placeholder={`Column name for ${field}`}
              className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Mode
        </label>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as 'PROFESSIONAL' | 'PERSONAL')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="PROFESSIONAL">Professional</option>
          <option value="PERSONAL">Personal</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Output Prefix
        </label>
        <input
          type="text"
          value={outputPrefix}
          onChange={(e) => setOutputPrefix(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        />
      </div>
    </div>
  );
}

function SaveCsvInspector({
  params,
  nodeId,
  onUpdate,
}: {
  params: SaveCsvParams;
  nodeId: string;
  onUpdate: (nodeId: string, params: any) => void;
}) {
  const [path, setPath] = useState(params.path || 'runs/{run_id}/output.csv');

  // Sync state when params change from outside (e.g., when switching nodes)
  useEffect(() => {
    setPath(params.path || 'runs/{run_id}/output.csv');
  }, [params.path]);

  useEffect(() => {
    onUpdate(nodeId, { path });
  }, [path, nodeId, onUpdate]);

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Output Path
        </label>
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          placeholder="runs/{run_id}/output.csv"
        />
        <p className="text-xs text-gray-500 mt-1">
          Use {'{run_id}'} to insert the run ID
        </p>
      </div>
    </div>
  );
}

