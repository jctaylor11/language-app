import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import App from './pages/App'
import Dashboard from './pages/Dashboard'
import Sentences from './pages/Sentences'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path='/' element={<App />} />
        <Route path='/dashboard' element={<Dashboard />} />
        <Route path='/sentences' element={<Sentences />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
