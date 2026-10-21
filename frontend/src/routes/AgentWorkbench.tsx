// Agent 工作台（decisions #24/#25/#26）：任务列表 + 发起 + 产出物三态编辑。
// REST 走 TanStack Query；WS 只做缓存失效；生成中/失败态都有明确文案。

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createAgentTask, fetchAgentTasks } from '../api/agents'
import { ApiError } from '../api/client'
import type { AgentStatus, AgentTask } from '../api/types'
import { connectWorldSocket } from '../api/ws'
import ArtifactEditor from '../components/ArtifactEditor'
import LoginDialog from '../components/LoginDialog'
import TraceQrCard from '../components/TraceQrCard'
import { useAuth } from '../stores/auth'

const TASK_STATUS: Record<AgentStatus, string> = {
  pending: '排队中',
  running: '生成中',
  done: '已完成',
  failed: '失败',
}

function TaskDetail({
  task,
  canFinalize,
  canEdit,
}: {
  task: AgentTask
  canFinalize: boolean
  canEdit: boolean
}) {
  const artifact = task.artifacts[0]
  return (
    <>
      <header className="wb-detail-head">
        <h2>任务 #{task.id}</h2>
        <span className={`wb-status ${task.status}`}>{TASK_STATUS[task.status]}</span>
      </header>
      <p className="wb-muted">
        由 {task.created_by} 发起 · {new Date(task.created_at).toLocaleString('zh-CN')}
      </p>
      {(task.status === 'pending' || task.status === 'running') && (
        <div className="wb-thinking">AI 正在生成，完成后自动出现（约 20 秒）…</div>
      )}
      {task.status === 'failed' && (
        <div className="form-error">生成失败。检查模型配置后可重新发起任务。</div>
      )}
      {artifact ? (
        <ArtifactEditor
          key={`${artifact.id}-${artifact.status}`}
          artifact={artifact}
          canFinalize={canFinalize}
          canEdit={canEdit}
        />
      ) : task.status === 'done' ? (
        <p className="wb-muted">任务完成但没有产出物。</p>
      ) : null}
    </>
  )
}

export default function AgentWorkbench() {
  const token = useAuth((s) => s.token)
  const role = useAuth((s) => s.role)
  const username = useAuth((s) => s.username)
  const logout = useAuth((s) => s.logout)
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loginOpen, setLoginOpen] = useState(false)
  const [qrOpen, setQrOpen] = useState(false)

  const tasksQuery = useQuery({
    queryKey: ['agent-tasks'],
    queryFn: fetchAgentTasks,
    enabled: Boolean(token),
    refetchInterval: 5000,
  })

  const authExpired =
    tasksQuery.error instanceof ApiError && tasksQuery.error.status === 401

  useEffect(() => {
    if (authExpired) logout()
  }, [authExpired, logout])

  const createMutation = useMutation({
    mutationFn: createAgentTask,
    onSuccess: (task) => {
      setSelectedId(task.id)
      void queryClient.invalidateQueries({ queryKey: ['agent-tasks'] })
    },
  })

  useEffect(() => {
    if (!token) return
    const handle = connectWorldSocket((event) => {
      if (event.type.startsWith('agent.')) {
        void queryClient.invalidateQueries({ queryKey: ['agent-tasks'] })
      }
    })
    return () => handle.close()
  }, [token, queryClient])

  const tasks = tasksQuery.data ?? []
  const busy = tasks.some(
    (t) =>
      (t.status === 'pending' || t.status === 'running') &&
      t.created_by === username,
  )
  const selected = tasks.find((t) => t.id === selectedId) ?? tasks[0] ?? null

  if (!token) {
    return (
      <main className="workbench">
        <div className="wb-empty">
          <h1>Agent 工作台</h1>
          <p>
            {authExpired
              ? '登录已过期，请重新登录。'
              : '登录后可发起故事/文案任务，并完成「AI 初稿 → 人工润色 → 定稿」。'}
          </p>
          <button type="button" onClick={() => setLoginOpen(true)}>
            登录
          </button>
        </div>
        {loginOpen && <LoginDialog onClose={() => setLoginOpen(false)} />}
      </main>
    )
  }

  return (
    <main className="workbench">
      <header className="wb-head">
        <div>
          <h1>Agent 工作台</h1>
          <p>AI 产出先落库；人工润色后定稿，答辩断网也能重放。</p>
        </div>
        <div className="wb-create">
          {role === 'operator' && (
            <button type="button" className="ghost" onClick={() => setQrOpen(true)}>
              溯源二维码
            </button>
          )}
          {busy && <span className="wb-muted">已有任务在生成…</span>}
          <button
            type="button"
            disabled={createMutation.isPending || busy}
            onClick={() => createMutation.mutate('story')}
          >
            生成品牌故事
          </button>
          <button
            type="button"
            className="primary"
            disabled={createMutation.isPending || busy}
            onClick={() => createMutation.mutate('copy')}
          >
            生成营销文案
          </button>
        </div>
      </header>

      {createMutation.isError && (
        <p className="form-error">
          {createMutation.error instanceof Error ? createMutation.error.message : '发起任务失败'}
        </p>
      )}

      <div className="wb-grid">
        <aside className="wb-list">
          {tasksQuery.isLoading && <p className="wb-muted">加载中…</p>}
          {tasksQuery.isError && <p className="form-error">读取任务失败</p>}
          {tasks.length === 0 && !tasksQuery.isLoading && (
            <p className="wb-muted">还没有任务，点右上角发起一个。</p>
          )}
          {tasks.map((task) => (
            <button
              type="button"
              key={task.id}
              className={`wb-task ${selected?.id === task.id ? 'active' : ''}`}
              onClick={() => setSelectedId(task.id)}
            >
              <span className="wb-task-title">
                #{task.id} {task.agent_type === 'story' ? '品牌故事' : '营销文案'}
              </span>
              <span className={`wb-status ${task.status}`}>{TASK_STATUS[task.status]}</span>
              <span className="wb-task-meta">
                {task.created_by} · {new Date(task.created_at).toLocaleTimeString('zh-CN', { hour12: false })}
              </span>
            </button>
          ))}
        </aside>

        <section className="wb-detail">
          {selected ? (
            <TaskDetail
              task={selected}
              canFinalize={role === 'operator'}
              canEdit={role === 'operator' || selected.created_by === username}
            />
          ) : (
            <p className="wb-muted">选择左侧任务查看产出物。</p>
          )}
        </section>
      </div>
      {qrOpen && <TraceQrCard onClose={() => setQrOpen(false)} />}
    </main>
  )
}
