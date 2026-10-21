import { Navigate, Route, Routes, useLocation } from 'react-router-dom'

import TopNav from './components/TopNav'
import AgentWorkbench from './routes/AgentWorkbench'
import Sandbox from './routes/Sandbox'
import Trace from './routes/Trace'
import './App.css'

export default function App() {
  const isTrace = useLocation().pathname.startsWith('/t/')
  return (
    <div className={isTrace ? 'app-shell trace-shell' : 'app-shell'}>
      {!isTrace && <TopNav />}
      <Routes>
        <Route path="/" element={<Sandbox />} />
        <Route path="/workbench" element={<AgentWorkbench />} />
        <Route path="/t/:code" element={<Trace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}
