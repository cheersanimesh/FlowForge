import { useMutation, useQuery } from '@tanstack/react-query';
import { runWorkflow, fetchPreview, healthCheck } from './client';
import type { WorkflowSpec, PreviewData } from '../types';

export function useRunWorkflow() {
  return useMutation({
    mutationFn: (spec: WorkflowSpec) => runWorkflow(spec),
  });
}

export function usePreview(previewPath: string | undefined) {
  return useQuery<PreviewData>({
    queryKey: ['preview', previewPath],
    queryFn: () => fetchPreview(previewPath!),
    enabled: !!previewPath,
  });
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
  });
}

