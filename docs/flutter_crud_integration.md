# Integracion de MS CRUD en Flutter

Este documento explica como consumir `MS CRUD` desde una app Flutter para consultar datos persistidos del sistema y mostrarlos en interfaz.

## 1. Rol de MS CRUD

`MS CRUD` es el microservicio responsable de persistir y exponer datos de negocio del sistema PPG, incluyendo:

- usuarios
- sesiones de monitoreo
- mediciones
- muestras PPG
- alertas

Tambien expone otras entidades auxiliares del dominio, pero para la app Flutter normalmente las consultas principales seran sobre los recursos anteriores.

## 2. Relacion con MS AUTH y MS MID

La responsabilidad de cada microservicio queda separada asi:

- `MS AUTH`: autentica al usuario, valida credenciales y emite el JWT.
- `MS CRUD`: no hace login ni valida contrasenas; solo valida el JWT recibido y usa su `sub` para decidir que datos puede ver el usuario.
- `MS MID`: puede actuar como servicio intermedio para capturar, procesar o reenviar datos, pero cuando consulta `MS CRUD` en nombre del usuario debe reenviar el mismo token Bearer.

Flujo tipico:

1. Flutter inicia sesion contra `MS AUTH`.
2. `MS AUTH` responde con un access token JWT.
3. Flutter guarda ese token de forma segura.
4. Flutter llama a `MS CRUD` enviando `Authorization: Bearer <token>`.
5. `MS CRUD` responde solo con recursos del usuario autenticado.

## 3. Autenticacion

`MS CRUD` protege los endpoints sensibles con autenticacion Bearer. El backend espera este header:

```http
Authorization: Bearer <token>
```

El token debe venir emitido por `MS AUTH` y contener al menos:

- `sub`: id del usuario autenticado
- `email`
- `exp`

Importante:

- `MS CRUD` no confia en un `id_user` enviado desde Flutter para decidir propiedad.
- el usuario efectivo sale del token JWT
- si el token no existe, es invalido o expiro, la respuesta sera `401`
- si el token es valido pero intenta acceder a recursos de otro usuario, la respuesta sera `403`

## 4. Como enviar el token en Flutter

Con el paquete [`http`](https://pub.dev/packages/http), el token se envia en los headers:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<void> fetchSessions(String token) async {
  final uri = Uri.parse('http://127.0.0.1:8000/monitoring_sessions');

  final response = await http.get(
    uri,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body);
    print(data);
    return;
  }

  throw Exception('Error ${response.statusCode}: ${response.body}');
}
```

## 5. Endpoints principales

Estos endpoints son los mas relevantes para consultar informacion persistida desde Flutter:

### `GET /App_users`

Devuelve solo el usuario autenticado. Aunque la respuesta es una lista, por las reglas actuales del backend normalmente llegara un unico elemento.

Ejemplo:

```http
GET /App_users
Authorization: Bearer <token>
```

### `GET /monitoring_sessions`

Devuelve solo las sesiones del usuario autenticado.

Parametros opcionales soportados:

- `query`
- `limit`
- `offset`
- `orderBy`
- `sort`

Ejemplo:

```http
GET /monitoring_sessions?orderBy=date_time&sort=desc&limit=20
Authorization: Bearer <token>
```

### `GET /Measurements`

Devuelve las mediciones asociadas a sesiones del usuario autenticado.

Importante:

- la ruta real usa `M` mayuscula: `/Measurements`

Ejemplo:

```http
GET /Measurements
Authorization: Bearer <token>
```

Para filtrar por sesion es mejor usar:

```http
GET /Measurements/session/{id_session}
Authorization: Bearer <token>
```

### `GET /alerts`

Devuelve alertas de sesiones del usuario autenticado.

Ejemplo:

```http
GET /alerts?orderBy=created_at&sort=desc
Authorization: Bearer <token>
```

### `GET /ppg_samples`

Devuelve muestras PPG de sesiones del usuario autenticado.

Ejemplo:

```http
GET /ppg_samples
Authorization: Bearer <token>
```

Para cargar muestras de una sesion concreta:

```http
GET /ppg_samples/session/{id_session}
Authorization: Bearer <token>
```

## 6. Ejemplos en Flutter con `http.get`

### Consultar perfil

```dart
final response = await http.get(
  Uri.parse('$baseUrl/App_users'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
);
```

### Consultar sesiones

```dart
final response = await http.get(
  Uri.parse('$baseUrl/monitoring_sessions?orderBy=date_time&sort=desc'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
);
```

### Consultar mediciones por sesion

```dart
final response = await http.get(
  Uri.parse('$baseUrl/Measurements/session/$sessionId'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
);
```

### Consultar alertas

```dart
final response = await http.get(
  Uri.parse('$baseUrl/alerts'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
);
```

## 7. Clase `CrudService`

Una forma practica de encapsular el acceso a `MS CRUD` es crear un servicio dedicado.

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  final int statusCode;
  final String body;

  ApiException(this.statusCode, this.body);

  @override
  String toString() => 'ApiException($statusCode): $body';
}

class CrudService {
  final String baseUrl;
  final Future<String?> Function() getToken;
  final http.Client client;

  CrudService({
    required this.baseUrl,
    required this.getToken,
    http.Client? client,
  }) : client = client ?? http.Client();

  Future<Map<String, String>> _headers() async {
    final token = await getToken();
    if (token == null || token.isEmpty) {
      throw Exception('No hay token disponible');
    }

    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  Future<dynamic> _getJson(String path) async {
    final response = await client.get(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
    );

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    }

    throw ApiException(response.statusCode, response.body);
  }

  Future<AppUser> getUserProfile() async {
    final data = await _getJson('/App_users') as List<dynamic>;
    if (data.isEmpty) {
      throw Exception('El backend no devolvio perfil de usuario');
    }
    return AppUser.fromJson(data.first as Map<String, dynamic>);
  }

  Future<List<MonitoringSession>> getSessions() async {
    final data = await _getJson('/monitoring_sessions') as List<dynamic>;
    return data
        .map((item) => MonitoringSession.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Measurement>> getMeasurements(int sessionId) async {
    final data =
        await _getJson('/Measurements/session/$sessionId') as List<dynamic>;
    return data
        .map((item) => Measurement.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<AlertItem>> getAlerts() async {
    final data = await _getJson('/alerts') as List<dynamic>;
    return data
        .map((item) => AlertItem.fromJson(item as Map<String, dynamic>))
        .toList();
  }
}
```

## 8. Modelo de datos clave

### `APP_USER`

Representa el perfil del usuario dentro del dominio de negocio.

Campos relevantes:

- `id_user`
- `id_city`
- `email`
- `first_name`
- `last_name`
- `birth_date`
- `created_at`
- `updated_at`

### `MONITORING_SESSION`

Representa una sesion de monitoreo realizada por un usuario.

Campos relevantes:

- `id_session`
- `id_user`
- `id_compute_status`
- `date_time`
- `created_at`
- `updated_at`
- `is_delta_encoded`

### `MEASUREMENT`

Representa una metrica calculada o almacenada para una sesion.

Campos relevantes:

- `id_measurement`
- `id_metric_type`
- `id_session`
- `value`
- `error_message`
- `recorded_at`

### `METRIC_TYPE`

Define como debe interpretarse una medicion.

Campos relevantes:

- `id_metric_type`
- `name`
- `unit`
- `min_value`
- `max_value`
- `is_derived`

`MEASUREMENT` no trae el detalle del tipo de metrica embebido; solo trae `id_metric_type`. Por eso, en frontend conviene tener un catalogo local o una consulta previa al recurso de tipos de metrica si la app necesita mostrar nombre, unidad o rango.

## 9. Como reconstruir metricas en Flutter

Para mostrar resultados por sesion en la UI:

1. consulta sesiones con `GET /monitoring_sessions`
2. para cada sesion visible, consulta `GET /Measurements/session/{id_session}`
3. agrupa las mediciones por `id_session`
4. usa `id_metric_type` para interpretar cada `value`

Ejemplo conceptual:

- `id_metric_type = 1` podria representar frecuencia cardiaca
- `id_metric_type = 2` podria representar SpO2
- `id_metric_type = 3` podria representar una metrica derivada

La interpretacion exacta depende del catalogo de `METRIC_TYPE`.

Ejemplo de agrupacion:

```dart
Map<int, List<Measurement>> groupMeasurementsBySession(
  List<Measurement> measurements,
) {
  final Map<int, List<Measurement>> grouped = {};

  for (final measurement in measurements) {
    grouped.putIfAbsent(measurement.idSession, () => []);
    grouped[measurement.idSession]!.add(measurement);
  }

  return grouped;
}
```

Y luego resolver significado por tipo:

```dart
String metricLabel(int metricTypeId) {
  switch (metricTypeId) {
    case 1:
      return 'Frecuencia cardiaca';
    case 2:
      return 'SpO2';
    default:
      return 'Metrica $metricTypeId';
  }
}
```

## 10. Ejemplo de respuesta y parsing en Dart

### Respuesta de `GET /monitoring_sessions`

```json
[
  {
    "id_session": 12,
    "id_user": 4,
    "id_compute_status": 1,
    "date_time": "2026-05-05T09:30:00",
    "created_at": "2026-05-05T09:30:10",
    "updated_at": "2026-05-05T09:30:10",
    "is_delta_encoded": false
  }
]
```

### Respuesta de `GET /Measurements/session/12`

```json
[
  {
    "id_measurement": 101,
    "id_metric_type": 1,
    "id_session": 12,
    "value": 78.5,
    "error_message": null,
    "recorded_at": "2026-05-05T09:31:00"
  },
  {
    "id_measurement": 102,
    "id_metric_type": 2,
    "id_session": 12,
    "value": 97.2,
    "error_message": null,
    "recorded_at": "2026-05-05T09:31:00"
  }
]
```

### Modelos Dart sugeridos

```dart
class AppUser {
  final int idUser;
  final int idCity;
  final String email;
  final String firstName;
  final String lastName;
  final DateTime birthDate;
  final DateTime createdAt;
  final DateTime updatedAt;

  AppUser({
    required this.idUser,
    required this.idCity,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.birthDate,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      idUser: json['id_user'] as int,
      idCity: json['id_city'] as int,
      email: json['email'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      birthDate: DateTime.parse(json['birth_date'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}

class MonitoringSession {
  final int idSession;
  final int idUser;
  final int idComputeStatus;
  final DateTime dateTime;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool isDeltaEncoded;

  MonitoringSession({
    required this.idSession,
    required this.idUser,
    required this.idComputeStatus,
    required this.dateTime,
    required this.createdAt,
    required this.updatedAt,
    required this.isDeltaEncoded,
  });

  factory MonitoringSession.fromJson(Map<String, dynamic> json) {
    return MonitoringSession(
      idSession: json['id_session'] as int,
      idUser: json['id_user'] as int,
      idComputeStatus: json['id_compute_status'] as int,
      dateTime: DateTime.parse(json['date_time'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      isDeltaEncoded: json['is_delta_encoded'] as bool,
    );
  }
}

class Measurement {
  final int idMeasurement;
  final int idMetricType;
  final int idSession;
  final double? value;
  final String? errorMessage;
  final DateTime recordedAt;

  Measurement({
    required this.idMeasurement,
    required this.idMetricType,
    required this.idSession,
    required this.value,
    required this.errorMessage,
    required this.recordedAt,
  });

  factory Measurement.fromJson(Map<String, dynamic> json) {
    return Measurement(
      idMeasurement: json['id_measurement'] as int,
      idMetricType: json['id_metric_type'] as int,
      idSession: json['id_session'] as int,
      value: (json['value'] as num?)?.toDouble(),
      errorMessage: json['error_message'] as String?,
      recordedAt: DateTime.parse(json['recorded_at'] as String),
    );
  }
}

class AlertItem {
  final int idAlert;
  final int idSession;
  final int idSeverityLevel;
  final String description;
  final DateTime createdAt;
  final DateTime updatedAt;

  AlertItem({
    required this.idAlert,
    required this.idSession,
    required this.idSeverityLevel,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AlertItem.fromJson(Map<String, dynamic> json) {
    return AlertItem(
      idAlert: json['id_alert'] as int,
      idSession: json['id_session'] as int,
      idSeverityLevel: json['id_severity_level'] as int,
      description: json['description'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
```

## 11. Manejo de errores

Los casos mas importantes en Flutter son estos:

### `401 Unauthorized`

Ocurre cuando:

- no se envio token
- el token es invalido
- el token expiro

En este backend, el mensaje esperado es similar a:

```json
{
  "detail": "Invalid or expired token"
}
```

Accion recomendada en Flutter:

- limpiar sesion local
- redirigir a login
- pedir renovacion de token o nuevo inicio de sesion

### `403 Forbidden`

Ocurre cuando el token es valido, pero el usuario intenta acceder a recursos que no le pertenecen.

Ejemplo:

- consultar una sesion de otro usuario
- consultar mediciones de una sesion ajena

Accion recomendada:

- no reintentar automaticamente
- mostrar mensaje de acceso denegado
- revisar que el flujo UI no este usando ids ajenos

### Token expirado

Aunque el backend responde `401`, en frontend conviene tratarlo como un caso especifico de sesion vencida:

```dart
Future<T> guardApiCall<T>(Future<T> Function() action) async {
  try {
    return await action();
  } on ApiException catch (e) {
    if (e.statusCode == 401) {
      // limpiar token, notificar expiracion y navegar a login
      rethrow;
    }
    if (e.statusCode == 403) {
      // mostrar acceso denegado
      rethrow;
    }
    rethrow;
  }
}
```

## 12. Buenas practicas en Flutter

### Cache local opcional

Para recursos de lectura frecuente, puedes guardar temporalmente:

- perfil de usuario
- listado de sesiones
- ultimas mediciones mostradas

Esto mejora percepcion de velocidad y reduce llamadas repetidas.

### Evitar llamadas innecesarias

Recomendaciones:

- no recargues el perfil en cada pantalla si ya esta en memoria
- al abrir detalle de sesion, consulta solo las mediciones de esa sesion
- usa `limit` y `offset` si el volumen de sesiones o muestras crece
- evita cargar `ppg_samples` completos si solo necesitas resumen de metricas

### Manejo de estados

Usa un patron claro de estado para cada pantalla:

- `loading`
- `success`
- `empty`
- `error`
- `unauthorized`

Con Provider, Riverpod, Bloc o cualquier manejador de estado, lo importante es que la UI distinga entre:

- error tecnico
- sesion expirada
- acceso prohibido
- sin datos

## 13. Recomendacion de flujo de consulta

Para una pantalla de dashboard o historial, un flujo razonable es:

1. cargar `getUserProfile()`
2. cargar `getSessions()`
3. cuando el usuario seleccione una sesion, llamar `getMeasurements(sessionId)`
4. cargar `getAlerts()` o `GET /alerts/session/{id_session}` si el detalle es por sesion
5. cargar `GET /ppg_samples/session/{id_session}` solo cuando realmente se necesite la senal cruda

Esto evita sobrecargar la app con datos grandes desde el inicio.

## 14. Resumen

Desde Flutter, `MS CRUD` debe consumirse siempre con token Bearer emitido por `MS AUTH`. Los recursos principales para mostrar datos persistidos son `/App_users`, `/monitoring_sessions`, `/Measurements`, `/alerts` y `/ppg_samples`.

La clave para una integracion limpia es:

- centralizar llamadas HTTP en una clase `CrudService`
- adjuntar siempre `Authorization: Bearer <token>`
- agrupar mediciones por `id_session`
- interpretar cada valor usando `id_metric_type`
- manejar correctamente `401`, `403` y expiracion de sesion

Con esa base, la app Flutter puede reconstruir historial, metricas, alertas y detalle de sesiones de forma consistente con las reglas del backend.
