// src/components/PrivateRoute.tsx
import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

export default function PrivateRoute({ children }: { children: JSX.Element }) {
  const auth = useContext(AuthContext);
  if (!auth?.token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
