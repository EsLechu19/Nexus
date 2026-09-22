import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = __dirname;
const expectedDirs = ['api', 'components', 'layout', 'pages', 'hooks', 'context'];

describe('T01 — estructura de carpetas frontend/src/', () => {
  for (const dir of expectedDirs) {
    it(`existe carpeta src/${dir}/`, () => {
      const full = path.join(srcDir, dir);
      const stat = fs.statSync(full);
      assert.ok(stat.isDirectory(), `${dir} debe ser directorio`);
    });

    it(`src/${dir}/ está vacía (sin código aún)`, () => {
      const full = path.join(srcDir, dir);
      const entries = fs.readdirSync(full).filter(e => !e.startsWith('.'));
      // ignorar archivos de test para no bloquear T03+
      const codeEntries = entries.filter(e => !e.endsWith('.test.jsx') && !e.endsWith('.test.js'));
      if (dir === 'layout') {
        assert.ok(codeEntries.length <= 3, `layout debe estar vacía o con AppLayout/NavLinkItem/Header en T03/013`);
        if (codeEntries.length > 0) {
          for (const e of codeEntries) assert.ok(['AppLayout.jsx', 'NavLinkItem.jsx', 'Header.jsx'].includes(e), `layout solo permite AppLayout/NavLinkItem/Header, encontrado ${e}`);
        }
      } else if (dir === 'pages') {
        // T04 + 006 T08-T12 crean páginas; 007 T08 añade Proveedores; 008 T07 añade Movimientos; 009 T05 añade Stock; 013 T04 añade Login; permitir hasta 7 archivos
        assert.ok(codeEntries.length <= 7, `pages debe estar vacía o con hasta 7 páginas en 006/007/008/009/013`);
        if (codeEntries.length > 0) {
          for (const e of codeEntries) assert.ok(['PlaceholderPage.jsx', 'NotFoundPage.jsx', 'Productos.jsx', 'Proveedores.jsx', 'Movimientos.jsx', 'Stock.jsx', 'Login.jsx'].includes(e), `pages solo permite Placeholder/NotFound/Productos/Proveedores/Movimientos/Stock/Login, encontrado ${e}`);
        }
      } else if (dir === 'api') {
        // T05-T07 + 006 T01-T02 crea cliente y productos; 007 T01-T02 añade proveedores; 008 T01 añade movimientos; 009 T01 añade stock; 013 T03 añade auth; permitir hasta 7 archivos
        assert.ok(codeEntries.length <= 7, `api debe estar vacía o con client/health/productos/proveedores/movimientos/stock/auth en 006/007/008/009/013`);
        if (codeEntries.length > 0) {
          for (const e of codeEntries) assert.ok(['client.js', 'health.js', 'productos.js', 'proveedores.js', 'movimientos.js', 'stock.js', 'auth.js'].includes(e), `api solo permite client/health/productos/proveedores/movimientos/stock/auth, encontrado ${e}`);
        }
      } else if (dir === 'components') {
        // T08-T11 + 006 Fase 2 crean componentes; 007 T04-T07 añade Proveedor*; 008 T04-T05 añade Movimientos*; 009 T03 añade StockTabla; 013 T05 añade ProtectedRoute; permitir hasta 14 archivos
        assert.ok(codeEntries.length <= 14, `components debe estar vacía o con hasta 14 componentes en 006/007/008/009/013`);
        if (codeEntries.length > 0) {
          for (const e of codeEntries) assert.ok(['Loading.jsx', 'EmptyState.jsx', 'ErrorMessage.jsx', 'ConfigErrorBanner.jsx', 'ProductoTabla.jsx', 'ProductoFormModal.jsx', 'ProductoBajaDialog.jsx', 'ProveedorTabla.jsx', 'ProveedorFormModal.jsx', 'ProveedorBajaDialog.jsx', 'MovimientosHistorial.jsx', 'MovimientoFormModal.jsx', 'StockTabla.jsx', 'ProtectedRoute.jsx'].includes(e), `components solo permite base + productos/proveedores/movimientos/stock/ProtectedRoute, encontrado ${e}`);
        }
      } else if (dir === 'hooks') {
        // T12 + 006 T03 crean hooks; 007 T03 añade useProveedores; 008 T03 añade useMovimientos; 009 T02 añade useStock; permitir hasta 5 archivos
        assert.ok(codeEntries.length <= 5, `hooks debe estar vacía o con useApiStatus/useProductos/useProveedores/useMovimientos/useStock en 006/007/008/009`);
        if (codeEntries.length > 0) {
          for (const e of codeEntries) assert.ok(['useApiStatus.js', 'useProductos.js', 'useProveedores.js', 'useMovimientos.js', 'useStock.js'].includes(e), `hooks solo permite useApiStatus/useProductos/useProveedores/useMovimientos/useStock, encontrado ${e}`);
        }
      } else if (dir === 'context') {
        // 013 T01 crea AuthContext; permitir solo AuthContext
        assert.ok(codeEntries.length <= 2, `context debe estar vacía o con AuthContext en 013`);
        if (codeEntries.length > 0) {
          for (const e of codeEntries) assert.ok(['AuthContext.jsx'].includes(e), `context solo permite AuthContext, encontrado ${e}`);
        }
      } else {
        assert.equal(codeEntries.length, 0, `${dir} debe estar vacía en T01-T03`);
      }
    });
  }

  it('existe README interno documentando la estructura', () => {
    const readme = path.join(srcDir, 'README.md');
    assert.ok(fs.existsSync(readme), 'src/README.md debe existir');
    const content = fs.readFileSync(readme, 'utf8');
    for (const dir of expectedDirs) {
      assert.ok(content.includes(dir), `README debe mencionar ${dir}`);
    }
    assert.ok(content.includes('RF-'), 'README debe referenciar RFs');
  });

  it('no existe código fuera de la estructura T01 (no hay jsx/js en src salvo tests/README)', () => {
    const entries = fs.readdirSync(srcDir, { withFileTypes: true });
    const allowed = new Set([...expectedDirs, 'README.md', 'structure.test.js', 'setupTests.js', 'router-deps.test.js', 'App.jsx', 'main.jsx', 'a11y.test.jsx', 'index.css', 'App.test.jsx', 'context']);
    for (const e of entries) {
      // permitir futuros archivos de test (*.test.js / *.test.jsx) sin romper T01
      if (e.name.endsWith('.test.js') || e.name.endsWith('.test.jsx')) continue;
      assert.ok(allowed.has(e.name), `archivo no esperado en src/: ${e.name}`);
    }
  });
});
