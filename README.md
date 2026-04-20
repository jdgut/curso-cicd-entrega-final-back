# Backend - FastAPI

Servicio responsable de reglas de negocio, auditoría y agregación de métricas para mapas de calor.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- Pytest

## Variables de entorno

- APP_APP_NAME: nombre de la aplicación.
- APP_APP_ENV: dev o prod.
- APP_APP_HOST: host de arranque.
- APP_APP_PORT: puerto de arranque.
- APP_CORS_ALLOWED_ORIGINS: orígenes permitidos para frontend local.
- APP_DATABASE_URL: cadena de conexión SQLAlchemy.

## Ejecución local sin Docker

1. python -m venv .venv
2. Activar entorno virtual.
3. pip install -r requirements.txt
4. Configurar APP_DATABASE_URL.
5. uvicorn app.main:app --reload

## URL base de la API

- URL local: http://localhost:8000
- Prefijo API: /api
- Swagger UI: http://localhost:8000/docs

## Endpoints disponibles

### Salud del servicio

- GET /health
	- Descripción: valida que la app está arriba.
	- Respuesta esperada: 200

### Usuarios

- POST /api/users/register
	- Descripción: registra un usuario nuevo.
	- Reglas:
		- email debe terminar en @eafit.edu.co
		- password mínimo 8 caracteres
	- Body JSON:

```json
{
	"email": "nuevo@eafit.edu.co",
	"password": "testtest",
	"role": "usuario"
}
```

	- Respuestas típicas:
		- 200: usuario creado
		- 409: correo ya registrado
		- 422: validación de datos

- POST /api/users/login
	- Descripción: inicia sesión lógica para usuarios existentes.
	- Body JSON:

```json
{
	"email": "test1@eafit.edu.co",
	"password": "testtest"
}
```

	- Respuestas típicas:
		- 200: credenciales válidas
		- 401: credenciales inválidas

### Desplazamientos

- POST /api/trips
	- Descripción: crea desplazamiento y agrega al creador como participante.
	- Body JSON:

```json
{
	"actor_email": "test1@eafit.edu.co",
	"title": "Salida manana",
	"meeting_point": "Salida norte del metro",
	"start_at": "2026-04-20T07:30:00",
	"transport_mode": "caminando",
	"direction": "metro_universidad"
}
```

- GET /api/trips
	- Descripción: lista desplazamientos activos (no archivados).

- PATCH /api/trips/{trip_id}
	- Descripción: edita datos básicos antes del inicio.
	- Body JSON:

```json
{
	"actor_email": "test1@eafit.edu.co",
	"title": "Salida ajustada",
	"meeting_point": "Acceso principal",
	"start_at": "2026-04-20T07:45:00"
}
```

- POST /api/trips/{trip_id}/join
	- Descripción: unir participante.
	- Body JSON:

```json
{
	"actor_email": "test2@eafit.edu.co"
}
```

- POST /api/trips/{trip_id}/leave
	- Descripción: retirar participante (si aplica regla temporal).
	- Body JSON:

```json
{
	"actor_email": "test2@eafit.edu.co"
}
```

- POST /api/trips/{trip_id}/state
	- Descripción: cambia estado global del desplazamiento.
	- Body JSON (avance normal):

```json
{
	"actor_email": "test1@eafit.edu.co",
	"new_state": "en_desplazamiento_universidad"
}
```

	- Body JSON (retroceso con nueva fecha/hora futura):

```json
{
	"actor_email": "test1@eafit.edu.co",
	"new_state": "en_metro",
	"new_start_at": "2026-04-21T07:30:00"
}
```

- POST /api/trips/{trip_id}/finalize
	- Descripción: finaliza y archiva manualmente.
	- Body JSON:

```json
{
	"actor_email": "test1@eafit.edu.co"
}
```

- GET /api/trips/{trip_id}/audit
	- Descripción: historial de eventos del desplazamiento.

### Métricas

- GET /api/trips/metrics/heatmap
	- Descripción: mapa de calor real con datos actuales.

- GET /api/trips/metrics/heatmap/simulated
	- Descripción: mapa de calor simulado para visitantes.

## Guía rápida para pruebas manuales en Postman

1. Crear un Environment en Postman con variable base_url = http://localhost:8000.
2. Verificar salud:
	 - GET {{base_url}}/health
3. Probar login de usuario demo ya precargado:
	 - POST {{base_url}}/api/users/login
	 - body: { "email": "test1@eafit.edu.co", "password": "testtest" }
4. Crear un desplazamiento:
	 - POST {{base_url}}/api/trips
5. Listar desplazamientos y guardar el id del primer item.
6. Usar ese id para join, leave, state, finalize y audit.
7. Consultar métricas:
	 - GET {{base_url}}/api/trips/metrics/heatmap
	 - GET {{base_url}}/api/trips/metrics/heatmap/simulated

Sugerencia para Postman:
- En Tests del request de crear desplazamiento puedes guardar el id automáticamente:

```javascript
const body = pm.response.json();
pm.environment.set("trip_id", body.id);
```

Luego usar la variable en rutas:
- POST {{base_url}}/api/trips/{{trip_id}}/join

## Usuarios demo precargados

En startup se crean automáticamente (si no existen):

- test1@eafit.edu.co
- test2@eafit.edu.co
- ...
- test15@eafit.edu.co

Contraseña para todos: testtest

## Pruebas

- pytest

Se exige cobertura mínima de 50% por configuración en pytest.ini.

## Decisiones de diseño

- Arquitectura por capas: API, servicios, repositorios, modelos y esquemas.
- Sin autenticación JWT; las reglas de permiso dependen del actor_email enviado por cliente.
- Auditoría persistente en tabla trip_audit.
- Aplicación de reglas automáticas de estado y archivado al consultar/operar desplazamientos.
