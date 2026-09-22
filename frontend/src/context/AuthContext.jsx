import React, { createContext, useContext, useState, useMemo, useEffect } from 'react';
import { setAuthTokenGetter, setOnUnauthorized } from '../api/client.js';

/**
 * Estado de sesión volátil — token solo en memoria.
 * RF-2, RF-3, RF-5, RNF-1, RNF-4. Inicial siempre null, sin localStorage/sessionStorage.
 * Expone token/isAuthenticated/login/logout y registra getter/interceptor en client.js.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);

  const login = (newToken) => {
    setToken(newToken);
  };

  const logout = () => {
    setToken(null);
  };

  // Registra getter para que client.js inyecte Bearer sin importar React (RF-4)
  useEffect(() => {
    setAuthTokenGetter(() => token);
    return () => setAuthTokenGetter(null);
  }, [token]);

  // Registra interceptor de 401 global con exclusión de login (RF-5)
  useEffect(() => {
    setOnUnauthorized(() => {
      setToken(null);
    });
    return () => setOnUnauthorized(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      isAuthenticated: !!token,
      login,
      logout,
    }),
    [token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return ctx;
}

export default AuthContext;
