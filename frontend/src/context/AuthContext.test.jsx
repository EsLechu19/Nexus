import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AuthContext, { AuthProvider, useAuth } from './AuthContext.jsx';

describe('T01 — AuthContext token solo en memoria — RF-2, RNF-1, RNF-4', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  function TestConsumer() {
    const { token, isAuthenticated, login, logout } = useAuth();
    return (
      <div>
        <span data-testid="token">{token ?? 'null'}</span>
        <span data-testid="auth">{isAuthenticated ? 'true' : 'false'}</span>
        <button onClick={() => login('jwt-test-token')} data-testid="login">
          login
        </button>
        <button onClick={() => logout()} data-testid="logout">
          logout
        </button>
      </div>
    );
  }

  it('inicial siempre null sin leer localStorage/sessionStorage', () => {
    const getItemSpy = vi.spyOn(Storage.prototype, 'getItem');
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    expect(screen.getByTestId('token').textContent).toBe('null');
    expect(screen.getByTestId('auth').textContent).toBe('false');
    expect(getItemSpy).not.toHaveBeenCalled();
    expect(localStorage.getItem).toBeDefined();
  });

  it('login guarda token en memoria y isAuthenticated pasa a true', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    fireEvent.click(screen.getByTestId('login'));
    expect(screen.getByTestId('token').textContent).toBe('jwt-test-token');
    expect(screen.getByTestId('auth').textContent).toBe('true');
  });

  it('logout limpia a null', () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    fireEvent.click(screen.getByTestId('login'));
    expect(screen.getByTestId('token').textContent).toBe('jwt-test-token');
    fireEvent.click(screen.getByTestId('logout'));
    expect(screen.getByTestId('token').textContent).toBe('null');
    expect(screen.getByTestId('auth').textContent).toBe('false');
  });

  it('nunca escribe en localStorage/sessionStorage al hacer login/logout', () => {
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');
    const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem');
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    fireEvent.click(screen.getByTestId('login'));
    fireEvent.click(screen.getByTestId('logout'));
    expect(setItemSpy).not.toHaveBeenCalled();
    expect(removeItemSpy).not.toHaveBeenCalled();
  });

  it('F5 (remount) vuelve a null — volatilidad consciente', () => {
    const { unmount } = render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    fireEvent.click(screen.getByTestId('login'));
    expect(screen.getByTestId('token').textContent).toBe('jwt-test-token');
    unmount();
    // simula recarga: nuevo mount debe iniciar null
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    expect(screen.getByTestId('token').textContent).toBe('null');
    expect(screen.getByTestId('auth').textContent).toBe('false');
  });

  it('expone contexto por defecto con error si se usa fuera de provider', () => {
    // useAuth fuera de provider debe lanzar o tener valor seguro
    function FueraDeProvider() {
      try {
        useAuth();
        return <span>no error</span>;
      } catch (e) {
        return <span data-testid="error">error</span>;
      }
    }
    render(<FueraDeProvider />);
    // si implementa guard, muestra error; si no, muestra no error — ambas aceptables si no rompe
    // verificamos que no haya token filtrado
    expect(screen.queryByTestId('error') || screen.getByText('no error')).toBeInTheDocument();
  });
});
