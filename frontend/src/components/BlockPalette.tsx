import { BlockType } from '../types';
import { useWorkflowStore } from '../state/useWorkflowStore';
import toast from 'react-hot-toast';

interface BlockItemProps {
  type: BlockType;
  label: string;
  icon: string;
}

function BlockItem({ type, label, icon }: BlockItemProps) {
  const addNode = useWorkflowStore((state) => state.addNode);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Add node at a default position (will be centered in canvas)
    // Account for left panel width (192px = 48 * 4) and right panel (320px) 
    const leftPanelWidth = 192; // w-48 = 12rem = 192px
    const rightPanelWidth = 320; // w-80 = 20rem = 320px
    const centerX = (window.innerWidth - leftPanelWidth - rightPanelWidth) / 2 + leftPanelWidth - 100;
    const centerY = (window.innerHeight - 200) / 2; // Account for header and run panel
    const nodeId = addNode(type, { x: centerX, y: centerY });
    console.log('Added node:', { type, nodeId, position: { x: centerX, y: centerY } });
    toast.success(`Added ${label} node`);
  };

  return (
    <div
      onClick={handleClick}
      className="p-3 mb-2 bg-white border-2 border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 hover:shadow-md transition-all active:scale-95"
    >
      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <span className="font-medium text-sm">{label}</span>
      </div>
    </div>
  );
}

export function BlockPalette() {
  const blocks: Array<{ type: BlockType; label: string; icon: string }> = [
    { type: BlockType.READ_CSV, label: 'Read CSV', icon: '📄' },
    { type: BlockType.FILTER, label: 'Filter', icon: '🔍' },
    { type: BlockType.ENRICH_LEAD, label: 'Enrich Lead', icon: '✨' },
    { type: BlockType.FIND_EMAIL, label: 'Find Email', icon: '📧' },
    { type: BlockType.SAVE_CSV, label: 'Save CSV', icon: '💾' },
  ];

  return (
    <div className="w-48 bg-gray-50 border-r border-gray-200 p-4 h-full overflow-y-auto">
      <h2 className="text-lg font-bold mb-4 text-gray-700">Blocks</h2>
      <p className="text-xs text-gray-500 mb-3">Click to add</p>
      <div className="space-y-2">
        {blocks.map((block) => (
          <BlockItem key={block.type} {...block} />
        ))}
      </div>
    </div>
  );
}

