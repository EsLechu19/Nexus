import '@testing-library/jest-dom';

// Buenas prácticas — TDD: tests primero, suprimir warnings esperados de React Router en tests
// Los warnings de future flags ya están optados en src/main.jsx con future={{v7_startTransition, v7_relativeSplatPath}}
// En tests se suprimen para mantener salida limpia; en navegador ya no aparecen tras el fix
const originalWarn = console.warn;
console.warn = (...args) => {
  if (typeof args[0] === 'string' && args[0].includes('React Router Future Flag Warning')) return;
  if (typeof args[0] === 'string' && args[0].includes('ReactDOMTestUtils.act')) return;
  originalWarn(...args);
};
