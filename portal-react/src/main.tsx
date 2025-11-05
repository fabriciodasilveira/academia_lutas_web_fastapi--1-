// portal-react/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import 'bootstrap/dist/css/bootstrap.min.css'; // <-- ADICIONE AQUI
import { AuthProvider } from './context/AuthContext'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider> {/* Envolve o App com o provedor de auth */}
      <App />
    </AuthProvider>
  </React.StrictMode>,
)