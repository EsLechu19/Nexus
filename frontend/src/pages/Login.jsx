import React, { useState } from 'react';
import { Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { login as loginApi } from '../api/auth.js';

/**
 * Pantalla de login — RF-1, RF-2.
 * Validación local solo Campo requerido, sin validar formato.
 */
export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errores, setErrores] = useState({ email: null, password: null, form: null });
  const [cargando, setCargando] = useState(false);
  const cargandoRef = React.useRef(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mensajeExterno, setMensajeExterno] = useState(location.state?.mensaje || null);

  if (isAuthenticated) {
    return <Navigate to="/productos" replace />;
  }

  React.useEffect(() => {
    if (location.state?.mensaje) {
      setMensajeExterno(location.state.mensaje);
      if (location.state.mensaje === 'Sesión cerrada correctamente') {
        const t = setTimeout(() => setMensajeExterno(null), 3000);
        return () => clearTimeout(t);
      }
    }
  }, [location.state]);

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    if (mensajeExterno === 'Sesión expirada, inicia sesión nuevamente') {
      setMensajeExterno(null);
    }
  };

  const handlePasswordChange = (e) => {
    setPassword(e.target.value);
    if (mensajeExterno === 'Sesión expirada, inicia sesión nuevamente') {
      setMensajeExterno(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (cargandoRef.current) return;

    const emailTrimCheck = email.trim();
    const passCheck = password;
    const nuevosErrores = { email: null, password: null, form: null };
    let hasError = false;
    if (!emailTrimCheck) {
      nuevosErrores.email = 'Campo requerido';
      hasError = true;
    }
    if (!passCheck || !passCheck.trim()) {
      // contraseña vacía también tras trim? spec dice vacío incluyendo solo espacios
      if (!password || !password.trim()) {
        nuevosErrores.password = 'Campo requerido';
        hasError = true;
      }
    }
    if (hasError) {
      setErrores(nuevosErrores);
      return;
    }

    setErrores({ email: null, password: null, form: null });
    setCargando(true);
    cargandoRef.current = true;
    try {
      const res = await loginApi({ email: emailTrimCheck, password });
      // éxito: guardar token solo en memoria
      login(res.access_token);
      const destino = location.state?.from?.pathname || '/productos';
      navigate(destino, { replace: true });
    } catch (err) {
      if (err && err.status === 401) {
        setErrores({ email: null, password: null, form: 'Credenciales inválidas' });
      } else if (err && err.status === 422) {
        // 422 array o string tal cual (delegado a client, pero Login muestra primer mensaje)
        setErrores({ email: null, password: null, form: err.mensaje || 'Error de validación' });
      } else if (err && err.tipo === 'conexion') {
        setErrores({ email: null, password: null, form: err.mensaje });
      } else if (err && err.mensaje) {
        setErrores({ email: null, password: null, form: err.mensaje });
      } else {
        setErrores({ email: null, password: null, form: 'Error de conexión con el servidor' });
      }
    } finally {
      setCargando(false);
      cargandoRef.current = false;
    }
  };

  const handleReintentar = () => {
    if (cargandoRef.current) return;
    // reintentar es re-ejecutar submit con valores actuales si no hay error de validación local
    const fakeEvent = { preventDefault: () => {} };
    handleSubmit(fakeEvent);
  };

  const mostrarReintentar = errores.form === 'Error de conexión con el servidor';

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-neutral-0">
      {mensajeExterno && (
        <div
          role="status"
          aria-live="polite"
          className={
            mensajeExterno === 'Sesión cerrada correctamente'
              ? 'bg-success-50 border border-success-600 text-success-600 p-4 rounded text-sm mb-4 w-full max-w-md'
              : 'bg-error-50 border border-error-600 text-error-600 p-4 rounded text-sm mb-4 w-full max-w-md'
          }
        >
          {mensajeExterno}
        </div>
      )}
      <form onSubmit={handleSubmit} className="w-full max-w-md flex flex-col gap-4 bg-white p-6 rounded border border-neutral-200" noValidate>
        <h1 className="text-xl font-semibold text-neutral-900">Iniciar sesión</h1>

        <div className="flex flex-col gap-1">
          <label htmlFor="email" className="text-sm font-medium text-neutral-900">
            Email
          </label>
          <input
            id="email"
            type="text"
            value={email}
            onChange={handleEmailChange}
            autoComplete="email"
            disabled={cargando}
            className="border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none disabled:bg-neutral-100"
          />
          {errores.email && (
            <span role="alert" className="text-sm text-error-600">
              {errores.email}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="text-sm font-medium text-neutral-900">
            Contraseña
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={handlePasswordChange}
            autoComplete="current-password"
            disabled={cargando}
            className="border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none disabled:bg-neutral-100"
          />
          {errores.password && (
            <span role="alert" className="text-sm text-error-600">
              {errores.password}
            </span>
          )}
        </div>

        {errores.form && (
          <div role="alert" aria-live="assertive" className="bg-error-50 border border-error-600 text-error-600 p-3 rounded text-sm">
            {errores.form}
            {mostrarReintentar && (
              <button type="button" onClick={handleReintentar} disabled={cargando} className="ml-2 underline disabled:opacity-50">
                Reintentar
              </button>
            )}
          </div>
        )}

        <button
          type="submit"
          disabled={cargando}
          className="bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed"
        >
          {cargando ? 'Cargando...' : 'Iniciar sesión'}
        </button>
      </form>
    </div>
  );
}
