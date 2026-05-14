# MS CRUD - PPG Monitoring Storage API

## Descripcion

Este repositorio corresponde al microservicio CRUD de almacenamiento del sistema PPG. Su responsabilidad es persistir y exponer datos de negocio relacionados con:

- usuarios,
- ubicacion geografica,
- historial de salud,
- wearables,
- sesiones de monitoreo,
- muestras PPG,
- metricas,
- alertas,
- estados de computo.

Este servicio no autentica usuarios ni valida contrasenas. La autenticacion ocurre en `ms-auth`, que emite un JWT. Luego este servicio valida ese JWT localmente para autorizar acceso a recursos protegidos.

La ubicacion geografica sigue la jerarquia:

- `country`
- `region`
- `city`

`APP_USER` persiste solo `id_city`; la region y el pais se obtienen por relacion.

---

## Modelo de datos actualizado

La base de datos sigue siendo unica, pero ahora separa identidad y credenciales:

- `APP_USER`: datos de dominio del usuario
- `AUTH_CREDENTIAL`: credenciales de autenticacion

### Que usa este servicio

MS CRUD solo trabaja con `APP_USER` y con las tablas de dominio relacionadas.

Para usuarios, este servicio solo maneja:

- `email`
- `first_name`
- `last_name`
- `birth_date`
- `id_city` (opcional al registrarse; se puede completar despues)

### Que no usa este servicio

MS CRUD:

- no lee `AUTH_CREDENTIAL`
- no escribe `AUTH_CREDENTIAL`
- no guarda `password`
- no guarda `password_hash`
- no valida credenciales

La autenticacion se realiza exclusivamente en `ms-auth`.

---

## Cambio nuevo: integracion JWT y control por usuario

Se anadio autenticacion basada en Bearer JWT para proteger recursos sensibles.

### Modulo agregado

- `dependencies/auth_guard.py`

Ese modulo:

- lee `Authorization: Bearer <token>`
- valida firma con `JWT_SECRET_KEY`
- valida algoritmo con `JWT_ALGORITHM`
- valida expiracion del token
- extrae `user_id` desde `sub`
- extrae `email`
- devuelve el usuario autenticado desde el token
- responde `401` si el token no existe, es invalido o expiro

### Regla base de autorizacion

MS CRUD solo confia en:

- `user_id` obtenido del JWT

No confia en `id_user` enviado por request.

En todas las operaciones protegidas, el `user_id` efectivo sale del token.

---

## Endpoints protegidos

Quedaron protegidas las rutas de:

- usuarios
- registros de salud
- wearables
- sesiones de monitoreo
- mediciones
- muestras PPG
- alertas

En concreto:

- `/App_users`
- `/health-records`
- `/wearables`
- `/monitoring_sessions`
- `/Measurements`
- `/ppg_samples`
- `/alerts`

---

## Reglas de acceso aplicadas

El servicio ahora aplica control de acceso por propietario:

- un usuario solo puede ver y modificar su propio perfil en `APP_USER`
- un usuario solo puede ver sus propios registros de salud
- un usuario solo puede ver sus propios wearables
- un usuario solo puede ver sus propias sesiones
- un usuario solo puede ver mediciones de sus propias sesiones
- un usuario solo puede ver alertas de sus propias sesiones
- un usuario solo puede ver muestras PPG de sus propias sesiones

Si el recurso existe pero pertenece a otro usuario, la API responde `403 Forbidden`.

Si no hay token o el token es invalido o expiro, la API responde `401 Unauthorized`.

---

## Relacion con los otros microservicios

### `ms-auth`

`ms-auth` es el servicio que:

- registra usuarios
- autentica credenciales
- crea `APP_USER`
- crea y gestiona `AUTH_CREDENTIAL`
- emite JWT

El JWT esperado por este servicio debe incluir al menos:

- `sub`: `user_id`
- `email`
- `exp`

### `ms-mid`

Si `ms-mid` llama a este servicio en nombre de un usuario, debe reenviar el mismo token:

```http
Authorization: Bearer <token>
```

MS CRUD no consulta a `ms-auth` en cada request. La validacion del JWT es local y desacoplada.

---

## Requisitos

- Python 3.8+
- PostgreSQL

Dependencias principales:

- FastAPI
- Uvicorn
- SQLAlchemy
- psycopg2-binary
- Pydantic
- python-dotenv
- PyJWT

---

## Variables de entorno

Este servicio necesita:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/PPG_DB
JWT_SECRET_KEY=replace-with-the-shared-jwt-secret
JWT_ALGORITHM=HS256
```

### Descripcion

- `DATABASE_URL`: cadena de conexion a PostgreSQL del servicio CRUD
- `JWT_SECRET_KEY`: secreto compartido con `ms-auth` para validar JWT
- `JWT_ALGORITHM`: algoritmo de firma del token; el valor esperado es `HS256`

Usa [.env.example](C:\Users\andre\Downloads\Noveno%20Semestre\LibroSUE\API\ppg-monitoring-api\.env.example) como base para crear tu `.env`.

---

## Instalacion

### 1. Crear entorno virtual

En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

En Linux/Mac:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requeriment.txt
```

### 3. Crear el archivo `.env`

Copia `.env.example` a `.env` y ajusta valores reales:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/PPG_DB
JWT_SECRET_KEY=the-same-secret-used-by-ms-auth
JWT_ALGORITHM=HS256
```

### 4. Verificar la base de datos

Este proyecto no incluye migraciones formales. Debes tener:

- PostgreSQL ejecutandose
- la base de datos creada
- las tablas compatibles con los modelos definidos en `DTO/models.py`

Importante:

- `APP_USER` ya no debe contener `password_hash`
- `AUTH_CREDENTIAL` existe en la misma base, pero este servicio no la toca

---

## Como ejecutar el servicio

Con el entorno virtual activo y el `.env` configurado:

```bash
uvicorn main:app --reload
```

Por defecto la API quedara disponible en:

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

Documentacion automatica:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Como probar la autenticacion

## 1. Obtener un token desde `ms-auth`

Ejemplo de login contra `ms-auth`:

```bash
curl -X POST http://127.0.0.1:8002/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"ana@example.com\",\"password\":\"Secret123!\"}"
```

Respuesta esperada:

```json
{
  "access_token": "JWT_AQUI",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 2. Consumir endpoints protegidos del CRUD

Perfil del usuario autenticado:

```bash
curl http://127.0.0.1:8000/App_users/1 \
  -H "Authorization: Bearer JWT_AQUI"
```

Registros de salud:

```bash
curl http://127.0.0.1:8000/health-records \
  -H "Authorization: Bearer JWT_AQUI"
```

Wearables:

```bash
curl http://127.0.0.1:8000/wearables \
  -H "Authorization: Bearer JWT_AQUI"
```

Sesiones:

```bash
curl http://127.0.0.1:8000/monitoring_sessions \
  -H "Authorization: Bearer JWT_AQUI"
```

Alertas:

```bash
curl http://127.0.0.1:8000/alerts \
  -H "Authorization: Bearer JWT_AQUI"
```

Muestras PPG:

```bash
curl http://127.0.0.1:8000/ppg_samples \
  -H "Authorization: Bearer JWT_AQUI"
```

Mediciones:

```bash
curl http://127.0.0.1:8000/Measurements \
  -H "Authorization: Bearer JWT_AQUI"
```

---

## Estructura del proyecto

```text
ppg-monitoring-api/
├── main.py
├── README.md
├── requeriment.txt
├── .env.example
├── config/
│   └── environment.py
├── DAO/
│   └── database.py
├── DTO/
│   └── models.py
├── ORM/
│   └── schemas.py
├── routes/
│   ├── alert.py
│   ├── app_user.py
│   ├── city.py
│   ├── compute_status.py
│   ├── country.py
│   ├── health_record.py
│   ├── measurement.py
│   ├── metric_type.py
│   ├── monitoring_session.py
│   ├── ppg_sample.py
│   ├── severity_level.py
│   ├── wearable.py
│   └── wearable_model.py
├── dependencies/
│   └── auth_guard.py
└── utils/
    └── query_builder.py
```

### Componentes clave

- `main.py`: punto de entrada FastAPI
- `config/environment.py`: variables de entorno
- `DAO/database.py`: conexion y sesion de base de datos
- `DTO/models.py`: modelos SQLAlchemy
- `ORM/schemas.py`: schemas Pydantic
- `routes/`: endpoints por entidad
- `dependencies/auth_guard.py`: validacion JWT local
- `utils/query_builder.py`: filtros, ordenamiento y paginacion

---

## Endpoints principales

## Publicos

Actualmente siguen publicos los modulos no protegidos por este cambio:

- `/countries`
- `/regions`
- `/cities`
- `/wearable-models`
- `/metric-types`
- `/severity-levels`
- `/compute_statuses`

## Protegidos con JWT

- `/App_users`
- `/health-records`
- `/wearables`
- `/monitoring_sessions`
- `/Measurements`
- `/ppg_samples`
- `/alerts`

---

## Comportamiento de autorizacion por recurso

### Perfil de usuario (`APP_USER`)

- `POST /App_users`: ya no crea usuarios; responde que el registro se hace en `ms-auth`
- `GET /App_users`: devuelve solo el usuario autenticado
- `GET /App_users/{id_user}`: solo permite consultar el propio usuario
- `PUT /App_users/{id_user}`: solo permite actualizar el propio perfil y puede completar `id_city`
- `DELETE /App_users/{id_user}`: solo permite eliminar el propio perfil

### Registros de salud

- `GET /health-records`: devuelve solo registros del usuario autenticado
- `GET /health-records/{id}`: solo si el registro le pertenece
- `POST /health-records`: crea el registro con el `user_id` del token
- `PUT /health-records/{id}`: solo si el registro le pertenece
- `DELETE /health-records/{id}`: solo si el registro le pertenece

### Wearables

- `GET /wearables`: devuelve solo wearables del usuario autenticado
- `GET /wearables/user/{id_user}`: solo permite consultar el propio `id_user`
- `GET /wearables/{id}`: solo si el wearable le pertenece
- `POST /wearables`: crea el wearable con el `user_id` del token
- `PUT /wearables/{id}`: solo si el wearable le pertenece
- `DELETE /wearables/{id}`: solo si el wearable le pertenece

### Sesiones

- `GET /monitoring_sessions`: devuelve solo sesiones del usuario autenticado
- `GET /monitoring_sessions/{id}`: solo si la sesion le pertenece
- `GET /monitoring_sessions/user/{id_user}`: solo permite consultar su propio `id_user`
- `POST /monitoring_sessions`: crea sesion usando el `user_id` del token
- `PUT /monitoring_sessions/{id}`: solo si la sesion le pertenece
- `DELETE /monitoring_sessions/{id}`: solo si la sesion le pertenece

### Mediciones

- `GET /Measurements`: devuelve solo mediciones asociadas a sesiones del usuario
- `GET /Measurements/{id}`: solo si pertenecen a una sesion del usuario
- `GET /Measurements/session/{id_session}`: solo si la sesion es del usuario
- `POST /Measurements`: solo permite crear mediciones sobre sesiones propias
- `PUT /Measurements/{id}`: solo si el recurso es del usuario y la sesion destino tambien
- `DELETE /Measurements/{id}`: solo si el recurso es del usuario

### Muestras PPG

- `GET /ppg_samples`: devuelve solo muestras de sesiones propias
- `GET /ppg_samples/session/{id_session}`: solo si la sesion es del usuario
- `POST /ppg_samples`: solo en sesiones propias
- `POST /ppg_samples/bulk`: valida cada sesion contra el usuario autenticado
- `PUT /ppg_samples/{id}`: solo si la muestra pertenece al usuario
- `DELETE /ppg_samples/{id}`: solo si la muestra pertenece al usuario

### Alertas

- `GET /alerts`: devuelve solo alertas de sesiones propias
- `GET /alerts/{id}`: solo si la alerta pertenece al usuario
- `GET /alerts/session/{id_session}`: solo si la sesion es del usuario
- `POST /alerts`: solo en sesiones propias
- `PUT /alerts/{id}`: solo si la alerta pertenece al usuario y la sesion destino tambien
- `DELETE /alerts/{id}`: solo si la alerta pertenece al usuario

---

## Notas importantes

- este servicio no guarda contrasenas
- este servicio no valida passwords
- este servicio no lee ni escribe `AUTH_CREDENTIAL`
- este servicio no implementa Basic Auth
- este servicio no consulta a `ms-auth` por request
- la validez del acceso depende de compartir el mismo `JWT_SECRET_KEY` y `JWT_ALGORITHM` con `ms-auth`
- el registro de usuario autenticable se hace exclusivamente en `ms-auth`

---

## Estado actual y limitaciones

- no hay migraciones automaticas
- no hay tests automatizados incluidos
- el nombre del archivo de dependencias sigue siendo `requeriment.txt`
- algunos prefijos de ruta mantienen naming heredado, por ejemplo `/Measurements` con mayuscula
- la creacion de usuarios autenticables ya no ocurre en este servicio

---

## Recomendaciones operativas

Para que esto funcione bien entre servicios:

1. Usa exactamente el mismo `JWT_SECRET_KEY` en `ms-auth`, `ms-mid` y `ms-crud`.
2. Mantén `JWT_ALGORITHM=HS256` en los tres servicios.
3. Haz que frontend y `ms-mid` reenvien siempre el token del usuario.
4. No intentes reconstruir identidad desde parametros como `id_user`; el origen de verdad ahora es el JWT.

---

## Resumen rapido

Antes:

- el CRUD aceptaba acceso sin JWT en usuarios, salud, wearables, sesiones, alertas, metricas y muestras
- `APP_USER` estaba mezclado con datos de autenticacion

Ahora:

- esas rutas requieren Bearer token
- el token se valida localmente
- el acceso queda restringido al dueno del recurso
- `APP_USER` ya no contiene contrasenas
- `AUTH_CREDENTIAL` queda fuera del alcance de este servicio
- el servicio sigue desacoplado de `ms-auth`
