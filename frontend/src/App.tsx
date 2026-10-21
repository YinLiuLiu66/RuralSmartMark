import { Navigate, Route, Routes } from 'react-router-dom'

import TopNav from './components/TopNav'
import AgentWorkbench from './routes/AgentWorkbench'
import Sandbox from './routes/Sandbox'
import './App.css'

export default function App() {
  return (
    <div className="app-shell">
      <TopNav />
      <Routes>
        <Route path="/" element={<Sandbox />} />
        <Route path="/workbench" element={<AgentWorkbench />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}
