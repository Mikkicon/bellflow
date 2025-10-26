import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Provider } from "./components/ui/provider"
import './index.css'
import App from './App.jsx'
import AnalysisPage from './pages/AnalysisPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Provider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/analysis/:id" element={<AnalysisPage />} />
        </Routes>
      </BrowserRouter>
    </Provider>
  </StrictMode>,
)
