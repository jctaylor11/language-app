import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import VocabSession from './pages/VocabSession'
import Dashboard from './pages/Dashboard'
import SentenceSession from './pages/SentenceSession'
import './index.css'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<VocabSession />} />
          <Route path='/dashboard' element={<Dashboard />} />
          <Route path='/sentences' element={<SentenceSession />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
