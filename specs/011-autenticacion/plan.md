# Plan 011 — Autenticación Básica

> Constitución: `docs/constitution.md` principios 1-6 | Spec: `specs/011-autenticacion/spec.md` RF-1..RF-5 (versión corregida con Impacto en specs existentes) | Convenciones: `AGENTS.md` | Integra protección retroactiva de `001-productos-catalogo`, `002-proveedores`, `003-movimientos-inventario`, `004-consulta-stock`

## 1. Estructura de módulos afectados — [Cubre RF-1..RF-5 + Impacto en 001-004]

Respetando arquitectura por capas `routers/ → services/ → models/ + schemas/` y principios 1 y 3 (routers solo HTTP, services solo negocio). No se toca cálculo de `stock_actual` (AGENTS.md 29).

| Capa | Archivo | Acción | RF cubiertos | Responsabilidad |
|------|---------|--------|--------------|-----------------|
| `models/` | `app/models/usuario.py` | **Crear** | RF-4 | Entidad `Usuario` (singular) tabla `usuarios` — solo `email` + `password_hash` |
| `schemas/` | `app/schemas/auth.py` | **Crear** | RF-1, RF-4 | Pydantic `LoginRequest` (`email`, `password`), `LoginResponse` (`access_token`, `token_type`), `TokenPayload` (`sub`, `exp`); nunca expone `password_hash` |
| `services/` | `app/services/auth_service.py` | **Crear** | RF-1, RF-4, RF-5, RNF-1–RNF-8 | Lógica de negocio: normalización email, validación, hasheo bcrypt, verificación, generación y validación JWT, manejo `exp` 8h |
| `services/` | `app/services/deps.py` | **Crear** | RF-2, RNF-8 | Dependency `get_current_user` / `requerir_autenticacion` — valida `Authorization: Bearer <token>` **antes** de cualquier acceso a BD/lock (orden exigido por spec corregida) |
| `routers/` | `app/routers/auth.py` | **Crear** | RF-1, RF-3 | Endpoint público `POST /api/v1/auth/login` — solo HTTP + delegación a `auth_service` |
| `routers/` | `app/routers/productos.py` | **Modificar** | RF-2 (Impacto 001) | Añadir `dependencies=[Depends(get_current_user)]` a `APIRouter` o a cada operación; sin tocar lógica interna |
| `routers/` | `app/routers/proveedores.py` | **Modificar** | RF-2 (Impacto 002) | Idem — proteger todo `/api/v1/proveedores` |
| `routers/` | `app/routers/movimientos.py` | **Modificar** | RF-2 (Impacto 003) | Idem — proteger `/api/v1/movimientos/*` |
| `routers/` | `app/routers/stock.py` | **Modificar** | RF-2 (Impacto 004) | Idem — proteger `/api/v1/stock` y `/api/v1/stock/{codigo}` |
| `app/` | `app/main.py` | **Modificar** | RF-1..RF-5 | Registrar `auth.router` con prefijo `/api/v1/auth`; registrar `stock`/`productos`/`proveedores`/`movimientos` ya existentes (no cambia orden de registro); configurar OpenAPI `securitySchemes` bearer (ver §8) |
| `app/` | `app/cli/crear_usuario.py` | **Crear** | RF-4 | Comando CLI administrativo fuera de HTTP para bootstrap (seed) — no es router, no es endpoint |
| `alembic/` | `alembic/versions/xxxx_crea_usuarios_011.py` | **Crear** | RF-4 | Migración que crea `usuarios` (ver §10) |
| `tests/` | `tests/conftest.py` | **Modificar** | RF-2 + Impacto 001-004 | Fixture compartido `auth_headers` que crea usuario de prueba y devuelve `Authorization` válido para reusar en integración |

> Verificación principio 1 y AGENTS.md 33: `ruff check .`, `mypy app`, `pytest -v` verde con token. Resto de detalles de implementación (nombres de funciones) no se fijan aquí — solo capas.

## 2. Modelo de datos — [Cubre RF-4, RNF-1, RNF-3]

### 2.1 Tabla `usuarios`
Modelo `Usuario` → tabla `usuarios` (plural, AGENTS.md 20). Sin relación FK saliente; es referenciada solo por validación de `email` en JWT, no por `movimientos_inventario` en este MVP (trazabilidad por usuario fuera de alcance).

| Columna | Tipo SQLAlchemy/PostgreSQL | Restricciones | Índice |
|---------|----------------------------|---------------|--------|
| `id` | `Integer` PK autoincrement | PK | PK |
| `email` | `VARCHAR(254)` | `NOT NULL`, `UNIQUE`, almacena valor normalizado `trim` + `lower` (misma normalización que `002` para proveedores), check `email ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'` o validación solo en `schemas` + `UNIQUE` en DB como salvaguarda | `UNIQUE INDEX ix_usuarios_email` |
| `password_hash` | `VARCHAR(72)` | `NOT NULL`, almacena hash bcrypt (60 chars, reserva 72) | — |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now()` | — |

RF: RF-4 (persistencia mínima), RNF-1 (solo hash), RNF-3 (unicidad + formato). No hay `nombre`, `rol`, `estado` (fuera de alcance).

**Índices:** solo `ix_usuarios_email` único. No se indexa `password_hash`.

**Checks:** `email` `UNIQUE` impide duplicado case-insensitive tras normalización en `auth_service` (ver §4); segunda barrera es `UNIQUE` DB con `IntegrityError` → mapeado a error de duplicado para CLI.

### 2.2 Ejemplo de fila representativa

`usuarios` (hash truncado intencionalmente, nunca un hash real completo):
```json
{
  "id": 1,
  "email": "admin@tienda.com",
  "password_hash": "$2b$12$abc...truncado...xyz",
  "created_at": "2026-09-20T10:00:00Z"
}
```
Con email normalizado: `  ADMIN@Tienda.COM ` → `admin@tienda.com` antes de persistir y antes de verificar. `password` en claro nunca se persiste ni se devuelve.

## 3. Diseño del JWT — [Cubre RF-1, RF-5, RNF-2, RNF-8]

**Claims exactos (única fuente, no en spec sino en plan):**
- `sub` : `email` normalizado (`admin@tienda.com`) — sujeto del token. Se usa `sub` y no `email` para cumplir estándar JWT (`sub` es claim registrado).
- `exp` : timestamp UTC seconds desde epoch, calculado como `iat + 8*3600`. `iat` implícito si la librería lo añade; no se añade `nbf`, `iss`, `aud` en MVP. No se incluyen roles/permisos (fuera de alcance, RNF-8).

**Algoritmo:** `HS256` (HMAC con SHA-256). Llave simétrica única.

**Gestión del secreto (AGENTS.md 30, RNF-1):**
- Variable de entorno `JWT_SECRET_KEY` (o `SECRET_KEY`) leída solo vía `os.getenv` / `pydantic-settings`, nunca hardcodeada ni commiteada, nunca logueada. Longitud mínima 32 bytes aleatorios. En tests se usa `JWT_SECRET_KEY=test-secret-no-usar-en-prod` vía `conftest`/`env` de test.
- `.env` local contiene `JWT_SECRET_KEY=...` y está en `.gitignore`; `.env.example` solo documenta la variable con valor ficticio.

**Duración:** `8 horas` fijas (`timedelta(hours=8)`). No hay `refresh_token` ni sliding window. Al expirar, el cliente descarta el token en memoria y vuelve a `POST /auth/login` (RF-5). El servidor no almacena revocación; `RNF-8` documenta que un token de usuario eliminado sigue válido hasta `exp`.

**Transporte:** `Authorization: Bearer <token>` — header único. No se acepta `query` ni `cookie`.

> RF-1 (generación), RF-5 (expiración), RNF-2 (stateless 8h), RNF-8 (validez residual).

## 4. Contrato de la API — [Cubre RF-1, RF-3, RNF-4]

Base: `/api/v1` (AGENTS.md 21). JSON `Content-Type: application/json`. Mensajes en español (RNF-4, RNF-7).

### RF-1 — Login `POST /api/v1/auth/login` (público)

**Request 200 (éxito):**
```json
POST /api/v1/auth/login
{
  "email": "admin@tienda.com",
  "password": "secreto123"
}
```
Normalización: `email` → `trim` + `lower` antes de buscar. `password` no se normaliza ni se hace `trim`.

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi50aWVuZGEuY29tIiwiZXhwIjoxNzI2ODM0MjQwMH0.truncado",
  "token_type": "bearer"
}
```
`token_type` siempre `bearer` en minúsculas.

**Error 422 — campos ausentes (regla de dos niveles, spec corregida):**
```json
POST /api/v1/auth/login
{}
→ 422
{
  "detail": [
    {"loc": ["body", "email"], "msg": "Field required", "type": "missing"},
    {"loc": ["body", "password"], "msg": "Field required", "type": "missing"}
  ]
}
```
También `{"email": "a@b.com"}` sin `password` → `422`. Validación estructural de Pydantic antes de lógica de negocio.

**Error 401 — cualquier otro caso (formato inválido, no existe, incorrecta):**
```json
POST /api/v1/auth/login
{"email": "no-existe@tienda.com", "password": "cualquiera"}
→ 401
{"detail": "Credenciales inválidas"}

POST /api/v1/auth/login
{"email": "sinarroba", "password": "x"}
→ 401
{"detail": "Credenciales inválidas"}

POST /api/v1/auth/login
{"email": "admin@tienda.com", "password": "errónea"}
→ 401
{"detail": "Credenciales inválidas"}
```
Mismo `401` sin distinción, para no revelar existencia (RNF-4). `email` con espacios extremos o mayúsculas que tras normalizar es válido pero no existe → `401` (no `422`).

**Errores adicionales RF-1:**
- Hash nunca expuesto: ninguna respuesta incluye `password` ni `password_hash` → verificado.

Cubre RF-1 completo y RF-3 (carácter público de este endpoint).

### RF-2/RF-3 — Endpoints protegidos (Impacto 001-004)

Ningún cambio de contrato para `/api/v1/productos`, `/proveedores`, `/movimientos/*`, `/stock` salvo que ahora requieren header. Ejemplo:

```
GET /api/v1/productos
Authorization: Bearer eyJ...
→ 200 [...]  (si token válido)
→ 401 {"detail": "Not authenticated"} o {"detail": "Credenciales inválidas"} si falta/inválido/expirado
```

Sin token → `401` (no `404`/`422` de negocio). El `401` se devuelve **antes** de validación de negocio (ver §5).

## 5. Diseño del dependency/middleware de protección — [Cubre RF-2, RF-3 + orden respecto a 003]

**Tipo:** `FastAPI dependency` (`Depends`) y no `BaseHTTPMiddleware`. Se elige dependency porque es idiomático FastAPI, permite `401` sin tocar `Session` y se aplica por `APIRouter`.

**Definición (sin código):**
- `get_current_user` es una dependency que: lee `Authorization`, valida prefijo `Bearer ` case-sensitive, extrae token, verifica firma `HS256` con `JWT_SECRET_KEY` y `exp` (UTC), extrae `sub` (email). Si falta/inválido/expirado → `HTTPException 401`. Si válido, retorna `email` (o `Usuario` mínimo) sin acceder a BD salvo opcional `SELECT` ligero para logging — pero **no bloquea**.
- Se inyecta como `dependencies=[Depends(get_current_user)]` en cada `APIRouter` de `productos`, `proveedores`, `movimientos`, `stock`. Alternativa de inyectar en `app.include_router(..., dependencies=[...])` también cumple, pero por router es más explícito y respeta `app/main.py` existente de `001`.

**Orden de ejecución (resuelve conflicto de lock de 003):**
- El dependency se ejecuta **antes** de entrar al `path operation function`, por tanto **antes** de que `services/movimiento_service.py` haga `SELECT ... FOR UPDATE` del producto. Un `401` nunca abre transacción ni toma lock. Esto satisface `RF-2` corregido y `003 RNF-3` sin crear lock innecesario.
- Orden documentado: `Request → CORSMiddleware → get_current_user (valida JWT, sin DB) → router handler → service (abre Session, FOR UPDATE si salida) → DB`. Si `get_current_user` falla, no se crea `Session`.

**Excepción de documentación (RF-3):**
- `/docs` y `/openapi.json` **no** llevan `Depends(get_current_user)`. Se montan por FastAPI fuera de `/api/v1`. Son públicos para visualización. `Try it out` falla con `401` porque la ejecución real sí pasa por el dependency del router protegido — no por la ruta de docs.

**Distinción de rutas públicas:**
- Solo `POST /api/v1/auth/login` y docs son públicos. Cualquier otra ruta bajo `/api/v1/*` sin token → `401`. No se usa `allow_origins` para bypass.

> RF-2 (protección y orden), RF-3 (excepción docs).

## 6. Diseño del comando CLI administrativo — [Cubre RF-4]

**Nombre del comando (propuesta para plan, no fijada en spec):**
`python -m app.cli.crear_usuario --email <email> --password <password>` o comando console script `crear-usuario` instalado vía `pyproject.toml`/`setup.py`. Se documentará en `plan.md` y `README`, no en `spec.md`.

**Ubicación:** `app/cli/crear_usuario.py` (fuera de `routers`/`services` HTTP, respeta Constitución §3 separación). Es script `__main__` que importa `auth_service` para reusar misma normalización y validación que el login.

**Hasheo:** Usa `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")` o `bcrypt` directo. Recibe `password` en claro vía arg `--password` o prompt interactivo sin echo, lo hashea con `bcrypt` (cost 12), nunca loguea el claro ni el hash completo en stdout.

**Validaciones que aplica (mismas que RF-4 EARS, actor CLI):**
- `email` tras `trim+lower` debe cumplir regex `002` (`local@dominio.tld`, TLD >=2, <=254, sin espacios); `email` único → consulta `SELECT` y si existe → error `Email ya existe` (no crea).
- `password` longitud `≥8` (`len(password) >=8` sin `trim`); si `<8` → error validación y no crea.
- Si ambas válidas y único → `INSERT` en `usuarios` con `email` normalizado y `password_hash`.
- Salida: `Usuario creado: admin@tienda.com` sin mostrar hash. Errores en español.

> RF-4 (creación fuera de API), RNF-1 (solo hash), RNF-3 (unicidad). No existe endpoint HTTP, por tanto no hay `404` de `POST /usuarios` — cualquier `POST /api/v1/usuarios` simplemente no está registrado y FastAPI responde `404` por defecto.

## 7. Cómo se actualiza el setup de tests existentes de 001–004 — [Cubre Impacto en specs existentes + RNF-6]

**Problema:** `001`–`004` tienen ~80 tests de integración con `TestClient` que hoy llaman `GET/POST /api/v1/...` sin token y esperan `200`/`201`. Con `011`, sin token esperan `401` — es cambio documentado, no regresión (ver Impacto).

**Solución — fixture compartido (no código aquí, solo diseño):**
- En `tests/conftest.py` (o `tests/fixtures/auth.py`) se crea fixture `auth_headers` / `usuario_admin` que: crea un usuario de prueba directamente vía `auth_service.crear_usuario` (o `INSERT` con hash) en la DB de test, luego llama `POST /api/v1/auth/login` con ese `email`/`password` y retorna `{"Authorization": "Bearer <token>"}`.
- Fixture `client_autenticado` opcional: `TestClient` preconfigurado con header `Authorization` por defecto.
- Cada `TestClient` existente de `001`–`004` se modifica en `setup_method`/`conftest` para incluir `headers=auth_headers` en cada `client.get/post/patch/delete`. Los tests de `001`–`004` que verifican `401` sin token se mantienen como nuevos tests de `011`, pero los existentes que esperan `200` se actualizan para enviar token.
- Aislamiento: cada test usa `function` scope con `db` rollback; el usuario de prueba se crea por test o por `module` con email único `test_011_{uuid}@tienda.com` para evitar colisión de `UNIQUE`.

**Verificación:** `pytest -v` con `auth_headers` debe volver a `verde` para `001`–`004` + nuevos tests de `011`. Un test de control `sin token → 401` confirma que la protección está activa.

> Cubre Impacto en specs existentes y RNF-6 (suite sigue verde con token).

## 8. Configuración de Swagger/OpenAPI para exigir token — [Cubre RF-3]

**Mecanismo:** FastAPI `HTTPBearer` + `securitySchemes`.

- En `app/main.py` y/o `app/routers/auth.py` se define `security = HTTPBearer()` y `app = FastAPI(..., swagger_ui_parameters={...})`.
- En `app/services/deps.py` se expone `oauth2_scheme = HTTPBearer(bearerFormat="JWT")`.
- Cada router protegido declara `dependencies=[Depends(oauth2_scheme)]` o `get_current_user` que internamente usa `HTTPBearer`. FastAPI genera en `openapi.json`:
```json
"securitySchemes": {
  "HTTPBearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
}
```
y cada operación bajo `/api/v1/*` incluye `"security": [{"HTTPBearer": []}]`, mientras `POST /api/v1/auth/login` y `GET /docs` no lo incluyen.

**Efecto:** En `/docs`, el botón `Authorize` (candado) pide `Bearer <token>` y `Try it out` sin token queda con `401` real del servidor, idéntico a `curl` sin header. Visualización de `/docs` sin token sigue permitida.

> RF-3 (docs Try it out protegido).

## 9. Decisiones técnicas justificadas — [Cubre RNF y AGENTS.md 28]

1.  **Librería JWT: `PyJWT` vs `python-jose`**
    - Elegida: **`PyJWT`** (`pyjwt[crypto]`).
    - Descartada: `python-jose` (`jose`).
    - Motivo: `PyJWT` es más pequeña, sin dependencias de `cryptography` opcionales complejas, API `jwt.encode/decode` con `algorithms=["HS256"]` explícito, mantenimiento activo y usada por `FastAPI` docs como ejemplo. `python-jose` está en modo mantenimiento y trae `ecdsa`/`rsa` no necesarios para `HS256` de MVP. Ambas cumplen `HS256`+`exp`, pero `PyJWT` tiene menos superficie y menos riesgo de CVE por `alg:none`. Para MVP con solo `HS256` y 8h, `PyJWT` es suficiente.
    - **Justificación de dependencia nueva pese a AGENTS.md 28:** `Constitución §1` solo permite `FastAPI+PostgreSQL+SQLAlchemy+Alembic` como stack base, pero `011` añade **autenticación** que no puede implementarse sin hasheo y JWT. Se añade `PyJWT` y `passlib[bcrypt]`+`bcrypt` (≈2 dependencias). Se considera **aprobación explícita de este plan** (como exige AGENTS.md 28 `preguntar antes`), documentada aquí y en el PR que referencia `011`. Sin ellas no hay `RF-1`/`RNF-1`/`RNF-2`. Se registra en `requirements.txt` con `pip freeze` y se verifica con `ruff/mypy`.

2.  **Hasheo: `passlib` + `bcrypt` vs `hashlib`**
    - Elegida: `passlib.context.CryptContext` con `bcrypt` (cost 12).
    - Descartada: `hashlib.sha256` o `hashlib.pbkdf2_hmac` directo.
    - Motivo: `bcrypt` es adaptativo, con salt automático y `work factor` configurable, estándar para passwords; `passlib` abstrae verificación `verify` y evita errores de comparación `==`. `hashlib` no es para passwords (rápido, sin salt).

3.  **Dependency `Depends` vs `Middleware`**
    - Elegida: `Depends(get_current_user)` por router.
    - Descartada: `BaseHTTPMiddleware` global que intercepta `/api/v1/*`.
    - Motivo: `Depends` respeta principio 3 (routers solo HTTP), permite `401` sin abrir `Session`, es testeable con `TestClient` sin levantar app completa, y no requiere parsear `request.url.path` manualmente para excluir `/docs`. Middleware global añadiría lógica de matching de rutas y riesgo de dejar `lock` si se ejecuta tarde.

4.  **Email normalizado en DB vs columna original + normalizada**
    - Elegida: almacenar `email` ya normalizado `lower` con `UNIQUE` (misma decisión que `002` para `codigo`).
    - Descartada: dos columnas `email_original` + `email_normalized`.
    - Motivo: unicidad case-insensitive garantizada por `UNIQUE` + normalización en `auth_service`; segunda columna innecesaria para MVP (RNF-3).

5.  **Token payload `sub` vs `email`**
    - Elegida: `sub` = `email` normalizado (claim estándar).
    - Descartada: `email` como claim custom.
    - Motivo: interoperable con `FastAPI` `get_current_user` examples y librerías que esperan `sub`.

## 10. Plan de migración Alembic — [Cubre RF-4]

**Revisión:** `alembic revision --autogenerate -m "crea usuarios 011"` → `alembic upgrade head` debe pasar sin errores (AGENTS.md 36, Constitución §5).

**Cambios (única migración de 011):**
- Crear tabla `usuarios` con columnas de §2.1, índice único `ix_usuarios_email`, sin FK saliente.
- No modifica `productos`, `proveedores`, `movimientos_inventario` (ya en migraciones `63276eeea69c`, `37840112ca70`, `9111dba96a53`); si `usuarios` ya existe, migración es no-op.
- Verificación: `alembic upgrade head` y `alembic downgrade -1` + `upgrade` sin pérdida; `psql \d usuarios` muestra `UNIQUE` y `NOT NULL`.

**Nota:** Migración inicial de `001` ya creó `productos` con `estado`; esta es migración incremental, no edita migraciones aplicadas (AGENTS.md 27).

## 11. Estrategia de tests — [Cubre RF-1..RF-5, RNF-1..RNF-8]

Sin escribir código de tests (Constitución §4: `pytest -v` 100% verde al finalizar).

**Unitarios — `services/auth_service.py` (mock `Session` / `sqlite:///:memory:` con `Base.metadata.create_all` + `TestSession`):**
- RF-4/RNF-1/RNF-3: `crear_usuario` con `email` válido/normalizado (`  ADMIN@Tienda.COM ` → `admin@tienda.com`) y `password` `≥8` → crea con `password_hash` distinto al claro y no igual a `bcrypt` de otro usuario con misma password (salt); `email` duplicado exacto/normalizado (`admin@tienda.com` vs ` ADMIN@tienda.com `) → error duplicado; `email` sin `@`/`sin punto`/`""`/`255` → validación; `password` 7/`""` → validación; `password_hash` nunca igual a claro.
- RF-1/RNF-2: `crear_token` con `email` → decodifica con `PyJWT` y verifica `sub==email` y `exp` ≈ `now+8h` (±60s); `exp` no es `None`.
- RF-1/RNF-4: `verificar_password` con `hash` correcto → `True`, incorrecto → `False`.
- RNF-8: `validar_token` con token emitido, luego borrado del usuario en DB, posterior validación del token sigue siendo válida hasta `exp` (no consulta DB para revocación).
- No se testea `SELECT FOR UPDATE` aquí (es de `movimiento_service`, ya cubierto en `003`).

**Integración — `routers/auth.py` + `routers/productos|proveedores|movimientos|stock` (`TestClient` + `TestSession` con `usuarios` creado via CLI/seed):**
- RF-1: `POST /api/v1/auth/login` con `email`/`password` correctos → `200` con `access_token` y `token_type=bearer`; con `email`/`password` ausentes → `422`; con `email` formato inválido/`no-existe`/`password` errónea → `401` `Credenciales inválidas` idéntico; verifica que respuesta no contiene `password_hash`.
- RF-2 (Impacto 001-004): `GET /api/v1/productos` sin header → `401`; con `Bearer` malformado/`Bearer` sin token/`Basic`/`firma alterada`/`exp` expirado (token con `exp` pasado manipulado en test) → `401`; con `Bearer` válido → `200` (productos), `200` (proveedores), `200` (movimientos historial), `200` (stock) — confirma que la lógica de negocio no cambió.
- RF-2 orden: test que envía `POST /api/v1/movimientos/salidas` con token inválido y `cantidad > stock` debe responder `401` y **no** dejar lock (verifica que no hay `SELECT FOR UPDATE` en logs de test y que posterior `salida` válida con token sí funciona).
- RF-3: `POST /api/v1/auth/login` → `200` sin token; `GET /docs` → `200` sin token; `GET /api/v1/productos` sin token desde `Try it out` → `401` (mismo que `curl`).
- RF-4: No existe `POST /api/v1/usuarios` → `404` (verifica que el router no está registrado); CLI no se testea vía HTTP.
- RF-5/RNF-2: token con `exp` futuro → `200`; con `exp` pasado → `401`; no hay `POST /logout` → `404`.
- RF-5/RNF-8: login, obtener token, borrar usuario vía `DELETE FROM usuarios` directo en test, usar token borrado para `GET /api/v1/productos` → `200` hasta `exp`.
- Transversal: mensajes en español, sin exponer modelos SQLAlchemy, `ruff`/`mypy` pasan, `GET /openapi.json` incluye `securitySchemes` bearer.

Cada test mapea explícitamente a su RF y a `RNF-1..RNF-8` y al `Impacto en specs existentes`.

## 12. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutilizado de `001`/`002`/`003`/`004` |
|---|---|---|---|
| Modelo `usuarios` `email` único + `password_hash` bcrypt | RF-4, RNF-1, RNF-3 | `email` duplicado → error CLI, `password` ≥8, hash != claro, `SELECT` con `UNIQUE` | Propia |
| `auth_service` hasheo/verificación + normalización `trim+lower` | RF-1, RF-4 | `bcrypt` con salt, `verify` ok/ko, `email` `  ADMIN@ ` → `admin@` | Propia + `002` regex |
| `auth_service` generación JWT `sub`+`exp` HS256 8h con `JWT_SECRET_KEY` | RF-1, RNF-2 | `exp` ≈ `now+8h`, `sub==email`, sin roles, `HS256` | Propia |
| `POST /api/v1/auth/login` 200/422/401 | RF-1, RNF-4 | `200` bearer, `422` ausente, `401` genérico formato/no-existe/errónea, sin `password_hash` | Propia |
| `get_current_user` dependency antes de DB/lock | RF-2 (incluye orden 003) | `401` sin token no abre `Session` ni `FOR UPDATE` | Propia + `003` |
| Protección `productos|proveedores|movimientos|stock` con `Depends` | RF-2 (Impacto 001-004) | sin `Bearer` → `401`, con `Bearer` válido → `200` misma lógica | Sí (001-004) + `011` |
| Docs `GET /docs` público pero `Try it out` protegido | RF-3 | `GET /docs` `200` sin token, `POST /productos` vía `Try it out` sin `Authorize` → `401` | Propia |
| CLI `crear_usuario` `--email --password` | RF-4 | `INSERT` solo `email`+`hash`, duplicado → rechazo, `<8` → validación, sin endpoint | Propia |
| Fixture `auth_headers` y actualización `001`–`004` | Impacto 001-004, RNF-6 | `conftest` crea usuario + login → `Authorization`, `001`–`004` vuelven a `200` con token | Propia |
| `openapi.json` `securitySchemes` HTTPBearer | RF-3 | `security: [{"HTTPBearer":[]}]` en operaciones `/api/v1/*` | Propia |
| `PyJWT`+`passlib[bcrypt]` como dependencias nuevas aprobadas | RNF-1, RNF-2, AGENTS.md 28 | `requirements.txt` con `PyJWT`+`passlib[bcrypt]`, `alembic upgrade` ok | Propia (aprobación explícita) |
| Migración `crea usuarios` | RF-4 | `usuarios` con `ix_usuarios_email` único | Propia |
| Tests unitarios `auth_service` | RF-1, RF-4, RNF-1–RNF-8 | hasheo, JWT, duplicado, `RNF-8` validez residual | Propia |
| Tests integración `auth` + protegidos | RF-1..RF-5 | login 200/422/401, protegido con/sin token, expirado, sin `POST /usuarios` → `404` | Propia + 001-004 |

## 13. Fuera de alcance del plan (confirmado, spec.md 93-101)

No se diseña registro público, recuperación/reset, roles/permisos, `refresh`/`logout` en servidor, rate limiting, complejidad de password >8, campos `nombre/rol/estado`, auditoría por usuario — tal como `spec.md:93-101`.

## 14. Dudas abiertas

- Ninguna bloqueante. Queda como `[NECESITA ACLARACIÓN]` para specs futuros si se debe añadir `nombre`/`estado` al usuario o si `rate limiting` debe ser por IP o email (ya marcado en spec).
