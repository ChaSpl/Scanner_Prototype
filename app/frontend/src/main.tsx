// src/main.tsx
import './index.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';  // ← import it

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>         {/* ← wrap here */}
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
