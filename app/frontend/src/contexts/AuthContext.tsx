import { createContext, useState, useEffect, type ReactNode } from 'react';
import api from '../api/axios';

export interface AuthContextType {
  token: string | null;
  login: (email: string, pw: string) => Promise<void>;
  logout: () => void;
  register: (fullName: string, email: string, pw: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    const t = localStorage.getItem('token');
    return t && t !== '' ? t : null;
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  const login = async (email: string, pw: string) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', pw);

    const res = await api.post('/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    setToken(res.data.access_token);
  };

  const register = async (fullName: string, email: string, pw: string) => {
    // Payload must match your RegisterInputStrict schema
    const res = await api.post('/register', {
      user: { full_name: fullName, email },
      password: pw,
    });
    setToken(res.data.access_token);
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}
