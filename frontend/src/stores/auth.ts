// 登录态（M4）：token/角色落 localStorage，Zustand 供导航与工作台共享。

import { create } from 'zustand'

import { getSession, login as apiLogin, logout as apiLogout } from '../api/client'

interface AuthState {
  token: string | null
  role: string | null
  username: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuth = create<AuthState>((set) => ({
  ...getSession(),
  login: async (username, password) => {
    const session = await apiLogin(username, password)
    set({
      token: session.access_token,
      role: session.role,
      username: session.username,
    })
  },
  logout: () => {
    apiLogout()
    set({ token: null, role: null, username: null })
  },
}))
