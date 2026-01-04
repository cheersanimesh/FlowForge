import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BlockPalette } from './components/BlockPalette';
import { FlowCanvas } from './components/FlowCanvas';
import { NodeInspector } from './components/NodeInspector';
import { SettingsPanel } from './components/SettingsPanel';
import { RunPanel } from './components/RunPanel';
import flowForgeLogo from './images/flow_forge_logo.png';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen flex flex-col">
        <header className="bg-blue-600 text-white px-6 py-3 shadow-md">
          <div className="flex items-center gap-3">
            <img src={flowForgeLogo} alt="FlowForge Logo" className="h-8 w-auto" />
            <h1 className="text-xl font-bold">FlowForge</h1>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <BlockPalette />
          <FlowCanvas />
          <div className="flex flex-col">
            <SettingsPanel />
            <NodeInspector />
          </div>
        </div>
        <RunPanel />
      </div>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}

export default App;

