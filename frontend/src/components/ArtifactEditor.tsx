// 产出物编辑器：草稿 → 润色 → 定稿（decisions #25 权限）。
// 运营方可流转状态；合作社只能改自己草稿内容，由父组件传入 canFinalize。

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { updateAgentArtifact } from '../api/agents'
import type { AgentArtifact } from '../api/types'

const STATUS_LABEL: Record<string, string> = {
  draft: 'AI 初稿',
  polished: '已润色',
  final: '已定稿',
}

export default function ArtifactEditor({
  artifact,
  canFinalize,
  canEdit,
}: {
  artifact: AgentArtifact
  canFinalize: boolean
  canEdit: boolean
}) {
  const queryClient = useQueryClient()
  const [content, setContent] = useState(artifact.content ?? '')
  const [notice, setNotice] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (patch: { content?: string; status?: 'polished' | 'final' }) =>
      updateAgentArtifact(artifact.id, patch),
    onSuccess: (data) => {
      setNotice(`已保存：${STATUS_LABEL[data.status] ?? data.status}`)
      void queryClient.invalidateQueries({ queryKey: ['agent-tasks'] })
    },
    onError: (e) => setNotice(e instanceof Error ? e.message : '保存失败'),
  })

  const locked =
    artifact.status === 'final' ||
    !canEdit ||
    (!canFinalize && artifact.status !== 'draft')
  const dirty = content !== (artifact.content ?? '')

  return (
    <section className="wb-editor">
      <header>
        <h3>{artifact.kind === 'story' ? '品牌故事' : '营销文案'}</h3>
        <span className={`wb-status ${artifact.status}`}>{STATUS_LABEL[artifact.status]}</span>
      </header>
      {!canEdit && <p className="wb-muted">合作社只能编辑自己发起的草稿。</p>}
      {artifact.status === 'final' && <p className="wb-muted">定稿后不可修改。</p>}
      <textarea
        value={content}
        readOnly={locked}
        onChange={(e) => setContent(e.target.value)}
        spellCheck={false}
        rows={18}
        placeholder="产出物内容"
      />
      <div className="wb-actions">
        <button
          type="button"
          disabled={locked || mutation.isPending || !dirty}
          onClick={() => mutation.mutate({ content })}
        >
          保存内容
        </button>
        {canFinalize && artifact.status === 'draft' && (
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate({ content, status: 'polished' })}
          >
            标记润色完成
          </button>
        )}
        {canFinalize && !locked && (
          <button
            type="button"
            className="primary"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate({ content, status: 'final' })}
          >
            定稿
          </button>
        )}
        {notice && <span className="wb-notice">{notice}</span>}
      </div>
    </section>
  )
}
