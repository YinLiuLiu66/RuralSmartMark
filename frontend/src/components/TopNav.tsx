// 顶部导航（decisions #24）：沙盘 / 工作台平级，右侧登录态。

import { useState } from 'react'
import { NavLink } from 'react-router-dom'

import LoginDialog from './LoginDialog'
import { useAuth } from '../stores/auth'

export default function TopNav() {
  const token = useAuth((s) => s.token)
  const role = useAuth((s) => s.role)
  const username = useAuth((s) => s.username)
  const logout = useAuth((s) => s.logout)
  const [open, setOpen] = useState(false)

  return (
    <nav className="top-nav">
      <span className="brand">RuralSmartMark</span>
      <div className="nav-links">
        <NavLink to="/" end>
          3D 沙盘
        </NavLink>
        <NavLink to="/workbench">Agent 工作台</NavLink>
      </div>
      <div className="nav-auth">
        {token ? (
          <>
            <span className="who">
              {username}
              <i>{role === 'operator' ? '运营方' : '合作社'}</i>
            </span>
            <button type="button" className="ghost" onClick={logout}>
              退出
            </button>
          </>
        ) : (
          <button type="button" onClick={() => setOpen(true)}>
            登录
          </button>
        )}
      </div>
      {open && <LoginDialog onClose={() => setOpen(false)} />}
    </nav>
  )
}
