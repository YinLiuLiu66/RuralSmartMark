// Agent 任务 REST（03 §3.2）：工作台用 TanStack Query 管缓存，WS 只触发失效。

import { authHeaders, request } from './client'
import type { AgentArtifact, AgentTask } from './types'

export function fetchAgentTasks(): Promise<AgentTask[]> {
  return request<AgentTask[]>('/api/agent-tasks', { headers: authHeaders() })
}

export function createAgentTask(agentType: 'story' | 'copy'): Promise<AgentTask> {
  return request<AgentTask>('/api/agent-tasks', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ agent_type: agentType }),
  })
}

export function updateAgentArtifact(
  id: number,
  patch: { content?: string; status?: 'polished' | 'final' },
): Promise<AgentArtifact> {
  return request<AgentArtifact>(`/api/agent-artifacts/${id}`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify(patch),
  })
}
