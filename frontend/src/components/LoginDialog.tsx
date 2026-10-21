// 登录弹窗（M4）：演示双账号一键填入，避免答辩现场敲密码。

import { useState } from 'react'

import { useAuth } from '../stores/auth'

export default function LoginDialog({ onClose }: { onClose: () => void }) {
  const login = useAuth((s) => s.login)
  const [username, setUsername] = useState('operator')
  const [password, setPassword] = useState('operator-demo')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (u = username, p = password) => {
    setBusy(true)
    setError(null)
    try {
      await login(u, p)
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : '登录失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <h2>登录</h2>
        <p className="modal-note">演示账号已预置：operator / coop</p>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            void submit()
          }}
        >
          <label>
            账号
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </label>
          <label>
            密码
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="ghost" onClick={onClose}>
              取消
            </button>
            <button type="submit" disabled={busy}>
              {busy ? '登录中…' : '登录'}
            </button>
          </div>
        </form>
        <div className="quick-login">
          <button type="button" className="ghost" disabled={busy} onClick={() => void submit('operator', 'operator-demo')}>
            用运营方账号
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => void submit('coop', 'coop-demo')}>
            用合作社账号
          </button>
        </div>
      </div>
    </div>
  )
}
