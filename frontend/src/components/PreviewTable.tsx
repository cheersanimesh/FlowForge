import { usePreview } from '../api/runs';
import type { PreviewData } from '../types';

interface PreviewTableProps {
  previewPath?: string;
}

export function PreviewTable({ previewPath }: PreviewTableProps) {
  const { data, isLoading, error } = usePreview(previewPath);

  if (!previewPath) {
    return (
      <div className="p-4 text-sm text-gray-500">
        No preview available. Select a node with preview data.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-gray-500">Loading preview...</div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-600">
        Error loading preview: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-4 text-sm text-gray-500">No preview data available</div>
    );
  }

  const { columns, preview, rows } = data as PreviewData;

  return (
    <div className="overflow-auto max-h-96">
      <div className="mb-2 text-sm text-gray-600">
        Showing {preview.length} of {rows} rows
      </div>
      <table className="min-w-full border-collapse border border-gray-300 text-sm">
        <thead>
          <tr className="bg-gray-100">
            {columns.map((col) => (
              <th
                key={col}
                className="border border-gray-300 px-3 py-2 text-left font-semibold"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {preview.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td
                  key={col}
                  className="border border-gray-300 px-3 py-2 text-left"
                >
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

