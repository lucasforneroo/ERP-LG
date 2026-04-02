# Compras.md — Arquitectura de API REST
### ERP-LG · Microservicio de Compras · v1.0

---

## Metadata

| Campo | Valor |
|---|---|
| Versión | 1.0.0 (draft) |
| Estado | En diseño |
| Responsable | Equipo de Compras |
| Integraciones | Desarrollo → **Compras** → Pañol |
| Base URL | `/api/v1/compras` |
| Autenticación | JWT Bearer Token |
| Protocolo de eventos | RabbitMQ / Kafka (Message Bus) |

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Contexto e integraciones](#2-contexto-e-integraciones)
3. [Modelos de datos](#3-modelos-de-datos)
4. [Endpoints](#4-endpoints)
5. [Máquina de estados — Orden de Compra](#5-máquina-de-estados--orden-de-compra)
6. [Autenticación y control de acceso](#6-autenticación-y-control-de-acceso)
7. [Códigos de respuesta HTTP](#7-códigos-de-respuesta-http)
8. [Paginación y filtros](#8-paginación-y-filtros)
9. [Consideraciones técnicas](#9-consideraciones-técnicas)
10. [Versionado](#10-versionado)

---

## 1. Resumen Ejecutivo

El microservicio de **Compras** es el núcleo del ciclo de abastecimiento dentro del ERP-LG. Su responsabilidad principal es gestionar el proceso completo desde la recepción de una **Solicitud de Materiales (SM)** —originada en el módulo de Desarrollo— hasta la recepción física de los bienes y su derivación automática al módulo de **Pañol**.

Este servicio opera bajo una arquitectura REST stateless, publica eventos al Message Bus ante cada cambio de estado relevante, y expone endpoints seguros mediante JWT. Todas las operaciones están auditadas y trazadas.

---

## 2. Contexto e Integraciones

### 2.1 Flujo principal

```
┌─────────────┐     SM creada      ┌─────────────┐    Evento recepción    ┌─────────────┐
│  Desarrollo │ ─────────────────► │   Compras   │ ──────────────────────► │    Pañol    │
│             │                    │             │                          │             │
│ Genera SM   │                    │ OC → Aprob. │                          │ Ingresa     │
│ por proyecto│                    │ → Recepción │                          │ stock       │
└─────────────┘                    └─────────────┘                          └─────────────┘
```

**Pasos del flujo:**

1. **Desarrollo** genera una Solicitud de Materiales (SM) asociada a un proyecto u orden de producción.
2. **Compras** recibe la SM, la convierte en una Orden de Compra (OC), gestiona proveedores, aprobaciones y recepciones.
3. Al recepcionar los bienes, **Compras** publica un evento que **Pañol** consume para registrar el ingreso de stock automáticamente.

### 2.2 Eventos publicados al Message Bus

| Evento | Tópico | Consumidor principal |
|---|---|---|
| `compras.oc.creada` | `compras.events` | Administración (auditoría) |
| `compras.oc.aprobada` | `compras.events` | Desarrollo, Logística |
| `compras.oc.rechazada` | `compras.events` | Desarrollo (notificación) |
| `compras.oc.cancelada` | `compras.events` | Desarrollo, Administración |
| `compras.recepcion.total` | `compras.events` | **Pañol** (ingreso de stock) |
| `compras.recepcion.parcial` | `compras.events` | **Pañol** (ingreso parcial) |
| `compras.proveedor.nuevo` | `compras.events` | Administración |

### 2.3 Eventos consumidos desde el Message Bus

| Evento | Origen | Acción en Compras |
|---|---|---|
| `desarrollo.sm.creada` | Desarrollo | Registra SM disponible para procesar |
| `desarrollo.sm.cancelada` | Desarrollo | Cancela OC asociadas si es posible |

---

## 3. Modelos de Datos

### 3.1 Solicitud de Materiales (SM)

Entidad originada en el módulo de Desarrollo. Compras la consume como entrada para generar Órdenes de Compra.

```json
{
  "id":               integer,
  "numero_sm":        string,
  "proyecto_id":      integer,
  "solicitante_id":   integer,
  "fecha_solicitud":  date,
  "estado":           "PENDIENTE | EN_PROCESO | COMPLETADA | CANCELADA",
  "prioridad":        "BAJA | MEDIA | ALTA | URGENTE",
  "items": [
    {
      "id":                integer,
      "material_codigo":   string,
      "descripcion":       string,
      "cantidad":          integer,
      "unidad_medida":     string,
      "cantidad_aprobada": integer,
      "observaciones":     string
    }
  ],
  "observaciones": string,
  "adjuntos":      ["url_archivo"],
  "created_at":    date
}
```

**Estados de la SM:**

| Estado | Descripción |
|---|---|
| `PENDIENTE` | SM recibida, aún sin OC generada |
| `EN_PROCESO` | Al menos una OC generada |
| `COMPLETADA` | Todos los ítems recepcionados |
| `CANCELADA` | Cancelada por Desarrollo o Compras |

---

### 3.2 Proveedor

```json
{
  "id":           integer,
  "razon_social": string,
  "cuit":         string,
  "categoria":    "MATERIA_PRIMA | INSUMO | SERVICIO | HERRAMIENTA",
  "contacto": {
    "nombre":   string,
    "email":    string,
    "telefono": string
  },
  "direccion": {
    "calle":     string,
    "ciudad":    string,
    "provincia": string,
    "pais":      string,
    "cp":        string
  },
  "condicion_pago": string,
  "moneda":         string,
  "calificacion":   float,
  "activo":         boolean,
  "created_at":     date,
  "updated_at":     date,
  "deleted_at":     date
}
```

---

### 3.3 Orden de Compra (OC)

```json
{
  "id":           integer,
  "numero_oc":    string,
  "sm_id":        integer,
  "proveedor_id": integer,
  "comprador_id": integer,
  "estado":       "BORRADOR | PENDIENTE_APROBACION | APROBADA | ENVIADA | EN_TRANSITO | RECIBIDA_PARCIAL | RECIBIDA_TOTAL | CANCELADA",
  "fecha_emision":           date,
  "fecha_entrega_estimada":  date,
  "fecha_entrega_real":      date,
  "moneda":         string,
  "tipo_cambio":    float,
  "condicion_pago": string,
  "items": [
    {
      "id":               integer,
      "sm_item_id":       integer,
      "material_codigo":  string,
      "descripcion":      string,
      "cantidad":         integer,
      "unidad_medida":    string,
      "precio_unitario":  float,
      "subtotal":         float,
      "cantidad_recibida": integer
    }
  ],
  "subtotal":   float,
  "impuestos":  float,
  "total":      float,
  "aprobado_por":     integer | null,
  "fecha_aprobacion": date | null,
  "observaciones": string,
  "adjuntos":      [string],
  "created_at":    date,
  "updated_at":    date
}
```

---

### 3.4 Recepción de Mercadería

```json
{
  "id":          integer,
  "oc_id":       integer,
  "receptor_id": integer,
  "fecha":       date,
  "tipo":        "TOTAL | PARCIAL",
  "remito_numero": string,
  "items": [
    {
      "oc_item_id":         integer,
      "cantidad_recibida":  integer,
      "cantidad_rechazada": integer,
      "motivo_rechazo":     string,
      "lote":               string,
      "ubicacion_panol":    string
    }
  ],
  "observaciones": string,
  "adjuntos":      [string],
  "created_at":    date
}
```

> **Nota:** Al persistir una recepción, el servicio publica automáticamente `compras.recepcion.total` o `compras.recepcion.parcial` al Message Bus. Pañol consume este evento para crear el movimiento de ingreso de stock sin intervención manual.

---

### 3.5 Calificación de Proveedor

```json
{
  "id":            integer,
  "proveedor_id":  integer,
  "oc_id":         integer,
  "calificador_id":integer,
  "fecha":         date,
  "puntaje":       integer,
  "dimensiones": {
    "calidad":        integer,
    "tiempo_entrega": integer,
    "precio":         integer,
    "comunicacion":   integer
  },
  "comentario": string
}
```

---

## 4. Endpoints

> **Base URL:** `/api/v1/compras`
> **Header requerido:** `Authorization: Bearer <jwt>`

---

### 4.1 Solicitudes de Materiales

Compras consume las SM generadas por Desarrollo. Son de solo lectura en este servicio (la creación pertenece al módulo de Desarrollo).

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/solicitudes` | Listar SM recibidas de Desarrollo |
| `GET` | `/solicitudes/{id}` | Obtener SM con ítems y trazabilidad |
| `PATCH` | `/solicitudes/{id}/estado` | Actualizar estado de la SM |
| `GET` | `/solicitudes/{id}/ordenes-compra` | Ver OC generadas a partir de una SM |

#### `GET /solicitudes`

**Query params:**

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `estado` | string | No | `PENDIENTE \| EN_PROCESO \| COMPLETADA \| CANCELADA` |
| `prioridad` | string | No | `BAJA \| MEDIA \| ALTA \| URGENTE` |
| `proyecto_id` | uuid | No | Filtrar por proyecto de Desarrollo |
| `desde` | date | No | Fecha inicio ISO 8601 |
| `hasta` | date | No | Fecha fin ISO 8601 |
| `page` | integer | No | Página (default: 1) |
| `limit` | integer | No | Registros por página (default: 20, max: 100) |

**Response `200 OK`:**
```json
{
  "data": [ /* array de SM */ ],
  "pagination": {
    "page": integer,
    "limit": integer,
    "total": integer,
    "total_pages": integer,
    "has_next": boolean,
    "has_prev": boolean
  }
}
```

#### `PATCH /solicitudes/{id}/estado`

**Body:**
```json
{
  "estado": "EN_PROCESO",
  "observaciones": "string"
}
```

---

### 4.2 Proveedores

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/proveedores` | Listar proveedores activos |
| `POST` | `/proveedores` | Registrar nuevo proveedor |
| `GET` | `/proveedores/{id}` | Obtener detalle de proveedor |
| `PUT` | `/proveedores/{id}` | Actualizar datos completos |
| `PATCH` | `/proveedores/{id}` | Actualización parcial |
| `DELETE` | `/proveedores/{id}` | Dar de baja lógica |
| `GET` | `/proveedores/{id}/historial` | Historial de OC y calificaciones |
| `POST` | `/proveedores/{id}/calificacion` | Registrar calificación post-recepción |

#### `GET /proveedores`

**Query params:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `categoria` | string | `MATERIA_PRIMA \| INSUMO \| SERVICIO \| HERRAMIENTA` |
| `calificacion_min` | float | Calificación mínima (0–5) |
| `activo` | boolean | Default: `true` |
| `q` | string | Búsqueda por razón social o CUIT |
| `page` | integer | Página (default: 1) |
| `limit` | integer | Default: 20, max: 100 |

#### `POST /proveedores`

**Body:**
```json
{
  "razon_social": string,
  "cuit":         string,
  "categoria":    string,
  "contacto": {
    "nombre":   string,
    "email":    string,
    "telefono": string
  },
  "direccion": {
    "calle":     string,
    "ciudad":    string,
    "provincia": string,
    "pais":      string,
    "cp":        string
  },
  "condicion_pago": string,
  "moneda":         string
}
```

**Validaciones:**
- `cuit` debe ser único en el sistema.
- `email` debe tener formato válido.
- `categoria` debe ser uno de los valores permitidos.

**Response `201 Created`:** Objeto proveedor completo.

#### `POST /proveedores/{id}/calificacion`

**Body:**
```json
{
  "oc_id":    in    teger,
  "puntaje":  integer,
  "dimensiones": {
    "calidad":        integer,
    "tiempo_entrega": integer,
    "precio":         integer,
    "comunicacion":   integer
  },
  "comentario": string
}
```

---

### 4.3 Órdenes de Compra

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/ordenes` | Listar OC con filtros |
| `POST` | `/ordenes` | Crear OC desde una SM |
| `GET` | `/ordenes/{id}` | Obtener OC completa |
| `PUT` | `/ordenes/{id}` | Editar OC en estado BORRADOR |
| `DELETE` | `/ordenes/{id}` | Cancelar OC |
| `POST` | `/ordenes/{id}/enviar` | Enviar a aprobación |
| `POST` | `/ordenes/{id}/aprobar` | Aprobar OC |
| `POST` | `/ordenes/{id}/rechazar` | Rechazar OC con motivo |
| `PATCH` | `/ordenes/{id}/confirmar-envio` | Confirmar despacho del proveedor |
| `GET` | `/ordenes/{id}/pdf` | Generar PDF de la OC |
| `GET` | `/ordenes/{id}/recepciones` | Listar recepciones de una OC |

#### `GET /ordenes`

**Query params:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `estado` | string | Ver estados en sección 5 |
| `proveedor_id` | uuid | Filtrar por proveedor |
| `sm_id` | uuid | Filtrar por SM origen |
| `comprador_id` | uuid | Filtrar por comprador |
| `desde` | date | Fecha de emisión desde |
| `hasta` | date | Fecha de emisión hasta |
| `moneda` | string | `ARS \| USD` |
| `page` | integer | Default: 1 |
| `limit` | integer | Default: 20, max: 100 |

#### `POST /ordenes`

**Body:**
```json
{
  "sm_id":                   integer,
  "proveedor_id":            integer,
  "fecha_entrega_estimada":  date,
  "moneda":                  string,
  "tipo_cambio":             float,
  "condicion_pago":          string,
  "items": [
    {
      "sm_item_id":      integer,
      "cantidad":        integer,
      "precio_unitario": float
    }
  ],
  "observaciones": string
}
```

**Validaciones:**
- `sm_id` debe existir y estar en estado `PENDIENTE` o `EN_PROCESO`.
- `proveedor_id` debe estar activo.
- `items` no puede estar vacío.
- `cantidad` debe ser mayor a 0.
- `precio_unitario` debe ser mayor a 0.
- `fecha_entrega_estimada` debe ser futura.

**Response `201 Created`:** OC completa. Publica evento `compras.oc.creada`.

#### `POST /ordenes/{id}/aprobar`

**Rol requerido:** `JEFE_COMPRAS` o `ADMIN`

**Body:**
```json
{
  "observaciones": "string"
}
```

**Response `200 OK`:** OC actualizada con `estado: APROBADA`. Publica `compras.oc.aprobada`.

#### `POST /ordenes/{id}/rechazar`

**Rol requerido:** `JEFE_COMPRAS` o `ADMIN`

**Body:**
```json
{
  "motivo": "Precio fuera de rango de mercado.",
  "observaciones": "string"
}
```

**Response `200 OK`:** OC con `estado: RECHAZADA`. Publica `compras.oc.rechazada`.

#### `PATCH /ordenes/{id}/confirmar-envio`

**Body:**
```json
{
  "fecha_envio_proveedor": date,
  "numero_seguimiento":    string,
  "transportista":         string,
  "observaciones":         string
}
```

#### `GET /ordenes/{id}/pdf`

Genera y retorna el PDF de la OC listo para enviar al proveedor.

**Response `200 OK`:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="OC-2024-0001.pdf"
```

---

### 4.4 Recepciones de Mercadería

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/recepciones` | Listar todas las recepciones |
| `POST` | `/recepciones` | Registrar recepción total o parcial |
| `GET` | `/recepciones/{id}` | Obtener detalle de recepción |
| `PATCH` | `/recepciones/{id}/ajuste` | Corregir recepción (dentro de las 24hs) |

#### `GET /recepciones`

**Query params:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `oc_id` | uuid | Filtrar por OC |
| `tipo` | string | `TOTAL \| PARCIAL` |
| `receptor_id` | uuid | Filtrar por receptor |
| `desde` | date | Fecha desde |
| `hasta` | date | Fecha hasta |
| `page` | integer | Default: 1 |
| `limit` | integer | Default: 20, max: 100 |

#### `POST /recepciones`

**Header recomendado:** `Idempotency-Key: {uuid}`

**Body:**
```json
{
  "oc_id":         integer,
  "remito_numero": string,
  "fecha":         date,
  "items": [
    {
      "oc_item_id":         integer,
      "cantidad_recibida":  integer,
      "cantidad_rechazada": integer,
      "motivo_rechazo":     string,
      "lote":               string,
      "ubicacion_panol":    string
    }
  ],
  "observaciones": "string",
  "adjuntos":      [string]
}
```

**Validaciones:**
- `oc_id` debe estar en estado `APROBADA`, `ENVIADA`, `EN_TRANSITO` o `RECIBIDA_PARCIAL`.
- `cantidad_recibida + cantidad_rechazada` no puede superar la cantidad pendiente de recepción del ítem.
- Si todos los ítems quedan `cantidad_recibida == cantidad OC`, el tipo se setea `TOTAL` automáticamente.

**Response `201 Created`:**
```json
{
  "data": { /* objeto recepción */ },
  "evento_publicado": "compras.recepcion.total",
  "payload_panol": {
    "recepcion_id":  integer,
    "oc_id":         integer,
    "items":         [ /* ítems con lote y ubicacion_panol */ ]
  }
}
```

> **Eventos publicados automáticamente:**
> - `compras.recepcion.total` → si todos los ítems de la OC están completos.
> - `compras.recepcion.parcial` → si quedan ítems pendientes.

#### `PATCH /recepciones/{id}/ajuste`

Solo disponible dentro de las 24hs de creada la recepción. Corrige errores de carga.

**Body:**
```json
{
  "items": [
    {
      "oc_item_id":         integer,
      "cantidad_recibida":  integer,
      "cantidad_rechazada": integer,
      "motivo_rechazo":     string,
      "lote":               string
    }
  ],
  "motivo_ajuste": string
}
```

---

### 4.5 Reportes y Consultas Analíticas

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/reportes/oc-por-estado` | Resumen de OC agrupadas por estado |
| `GET` | `/reportes/gasto-por-proveedor` | Monto total comprado por proveedor en un período |
| `GET` | `/reportes/tiempos-entrega` | Desvío entre fecha estimada y real de entrega |
| `GET` | `/reportes/recepciones-rechazos` | Cantidad y motivos de ítems rechazados |
| `GET` | `/reportes/sm-pendientes` | SM sin OC generada, ordenadas por prioridad |
| `GET` | `/reportes/stock-en-transito` | Materiales comprados aún no recepcionados |

#### `GET /reportes/oc-por-estado`

**Query params:** `desde`, `hasta`, `proveedor_id`

**Response `200 OK`:**
```json
{
  "periodo": { "desde": date, "hasta": date },
  "resumen": [
    { "estado": "APROBADA",        "cantidad": integer, "total_ars": float },
    { "estado": "RECIBIDA_TOTAL",  "cantidad": integer, "total_ars": float },
    { "estado": "PENDIENTE_APROBACION", "cantidad": integer, "total_ars": float }
  ]
}
```

#### `GET /reportes/tiempos-entrega`

**Query params:** `desde`, `hasta`, `proveedor_id`

**Response `200 OK`:**
```json
{
  "promedio_desvio_dias": 2.3,
  "proveedores": [
    {
      "proveedor_id":    integer,
      "razon_social":    string,
      "oc_evaluadas":    integer,
      "desvio_promedio": float,
      "puntualidad_pct": float
    }
  ]
}
```

---

## 5. Máquina de Estados — Orden de Compra

```
                     ┌─────────────────────────────────────────────────────────┐
                     │                                                         │
              POST /ordenes                                              CANCELADA
                     │                                                         ▲
                     ▼                                                         │
               ┌──────────┐   POST /enviar   ┌──────────────────┐             │
               │ BORRADOR │ ───────────────► │ PEND_APROBACION  │             │
               └──────────┘                  └──────────────────┘             │
                     │                          │            │                 │
              DELETE /ordenes           aprobar │    rechazar │                │
                     │                          ▼            ▼                 │
                     └──────────────────► ┌──────────┐  ┌──────────┐         │
                                          │ APROBADA │  │RECHAZADA │         │
                                          └──────────┘  └──────────┘         │
                                               │                              │
                                    PATCH /confirmar-envio                    │
                                               │                              │
                                               ▼                              │
                                          ┌─────────┐    DELETE ──────────────┘
                                          │ ENVIADA │
                                          └─────────┘
                                               │
                                      evento proveedor
                                               │
                                               ▼
                                         ┌──────────┐
                                         │EN_TRANSITO│
                                         └──────────┘
                                          │        │
                              parcial     │        │  total
                                ▼                  ▼
                      ┌─────────────────┐   ┌──────────────┐
                      │ RECIBIDA_PARCIAL │   │RECIBIDA_TOTAL│
                      └─────────────────┘   └──────────────┘
                               │
                    recepción final
                               │
                               ▼
                       ┌──────────────┐
                       │RECIBIDA_TOTAL│
                       └──────────────┘
```

### Tabla de transiciones

| Estado origen | Estado destino | Acción | Rol requerido |
|---|---|---|---|
| — | `BORRADOR` | `POST /ordenes` | `COMPRADOR` |
| `BORRADOR` | `PENDIENTE_APROBACION` | `POST /ordenes/{id}/enviar` | `COMPRADOR` |
| `BORRADOR` | `CANCELADA` | `DELETE /ordenes/{id}` | `COMPRADOR` |
| `PENDIENTE_APROBACION` | `APROBADA` | `POST /ordenes/{id}/aprobar` | `JEFE_COMPRAS` |
| `PENDIENTE_APROBACION` | `RECHAZADA` | `POST /ordenes/{id}/rechazar` | `JEFE_COMPRAS` |
| `APROBADA` | `ENVIADA` | `PATCH /ordenes/{id}/confirmar-envio` | `COMPRADOR` |
| `APROBADA` | `CANCELADA` | `DELETE /ordenes/{id}` | `JEFE_COMPRAS` |
| `ENVIADA` | `EN_TRANSITO` | Evento proveedor / manual | `COMPRADOR` |
| `EN_TRANSITO` | `RECIBIDA_PARCIAL` | `POST /recepciones` | `RECEPTOR` |
| `EN_TRANSITO` | `RECIBIDA_TOTAL` | `POST /recepciones` | `RECEPTOR` |
| `RECIBIDA_PARCIAL` | `RECIBIDA_TOTAL` | `POST /recepciones` | `RECEPTOR` |

> Cualquier transición no listada en esta tabla retorna `HTTP 422 Unprocessable Entity`.

---

## 6. Autenticación y Control de Acceso

### 6.1 Autenticación

Todos los endpoints requieren un JWT Bearer Token emitido por el **Auth Service** central del ERP-LG.

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Payload del JWT:**
```json
{
  "sub":    "uuid-del-usuario",
  "nombre": string,
  "roles":  [string],
  "tenant": string,
  "iat":    integer,
  "exp":    integer
}
```

### 6.2 Roles definidos en este microservicio

| Rol | Descripción |
|---|---|
| `ADMIN` | Acceso total, puede operar en nombre de cualquier rol |
| `JEFE_COMPRAS` | Aprobación/rechazo de OC, gestión completa de proveedores |
| `COMPRADOR` | Crear y editar OC, gestionar proveedores, confirmar envíos |
| `RECEPTOR` | Registrar recepciones y calificar proveedores |
| `SOLO_LECTURA` | Solo GET en todos los recursos, acceso a reportes |

### 6.3 Matriz de permisos

| Operación | ADMIN | JEFE_COMPRAS | COMPRADOR | RECEPTOR | SOLO_LECTURA |
|---|:---:|:---:|:---:|:---:|:---:|
| Ver SM / OC / Recepciones | ✓ | ✓ | ✓ | ✓ | ✓ |
| Crear / editar OC | ✓ | ✓ | ✓ | — | — |
| Enviar OC a aprobación | ✓ | ✓ | ✓ | — | — |
| Aprobar / rechazar OC | ✓ | ✓ | — | — | — |
| Cancelar OC aprobada | ✓ | ✓ | — | — | — |
| Gestionar proveedores | ✓ | ✓ | ✓ | — | — |
| Registrar recepción | ✓ | ✓ | ✓ | ✓ | — |
| Ajustar recepción | ✓ | ✓ | — | — | — |
| Calificar proveedor | ✓ | ✓ | ✓ | ✓ | — |
| Ver reportes | ✓ | ✓ | ✓ | — | ✓ |
| Exportar PDF de OC | ✓ | ✓ | ✓ | — | — |
| Incluir registros eliminados | ✓ | — | — | — | — |

---

## 7. Códigos de Respuesta HTTP

| Código | Estado | Cuándo se usa |
|---|---|---|
| `200` | OK | Lectura o acción exitosa |
| `201` | Created | Recurso creado correctamente |
| `204` | No Content | Eliminación lógica exitosa |
| `400` | Bad Request | Payload inválido, campos requeridos ausentes |
| `401` | Unauthorized | JWT ausente, expirado o con firma inválida |
| `403` | Forbidden | Token válido pero el rol no tiene permiso |
| `404` | Not Found | Recurso no encontrado |
| `409` | Conflict | CUIT duplicado, SM ya completada, OC ya aprobada |
| `422` | Unprocessable Entity | Transición de estado inválida |
| `429` | Too Many Requests | Rate limiting superado |
| `500` | Internal Server Error | Error no controlado del servicio |

### 7.1 Estructura de respuesta de error

```json
{
  "error": {
    "code":    "OC_TRANSICION_INVALIDA",
    "message": "No se puede rechazar una OC en estado APROBADA.",
    "details": {
      "estado_actual":    "APROBADA",
      "transicion_pedida": "RECHAZADA",
      "transiciones_validas": ["ENVIADA", "CANCELADA"]
    },
    "trace_id": "uuid-para-correlacion-de-logs"
  }
}
```

### 7.2 Códigos de error de negocio

| Code | HTTP | Descripción |
|---|---|---|
| `SM_NO_ENCONTRADA` | 404 | La SM referenciada no existe |
| `SM_ESTADO_INVALIDO` | 409 | La SM está en estado CANCELADA o COMPLETADA |
| `OC_TRANSICION_INVALIDA` | 422 | Transición de estado no permitida |
| `OC_NO_EDITABLE` | 422 | OC no está en BORRADOR |
| `PROVEEDOR_INACTIVO` | 409 | El proveedor está dado de baja |
| `CUIT_DUPLICADO` | 409 | Ya existe un proveedor con ese CUIT |
| `RECEPCION_EXCEDE_CANTIDAD` | 422 | Suma de recepciones supera cantidad de OC |
| `RECEPCION_FUERA_PLAZO` | 422 | Ajuste de recepción fuera de las 24hs |
| `IDEMPOTENCY_REPLAY` | 200 | Petición repetida detectada por Idempotency-Key |

---

## 8. Paginación y Filtros

Todos los endpoints de listado implementan paginación por offset.

### Request

```
GET /api/v1/compras/ordenes?estado=APROBADA&desde=2024-01-01&page=2&limit=20
```

### Response

```json
{
  "data": [ /* array de recursos */ ],
  "pagination": {
    "page":        integer,
    "limit":       integer,
    "total":       integer,
    "total_pages": integer,
    "has_next":    boolean,
    "has_prev":    boolean
  },
  "filters_applied": {
    "estado": string,
    "desde":  date
  }
}
```

### Ordenamiento

Todos los endpoints de listado aceptan:

| Parámetro | Valores | Default |
|---|---|---|
| `sort_by` | Campo del modelo | `created_at` |
| `sort_order` | `asc \| desc` | `desc` |

---

## 9. Consideraciones Técnicas

### 9.1 Idempotencia

Los endpoints `POST /recepciones` y `POST /ordenes` soportan el header `Idempotency-Key`.

```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

Si se envía la misma key dos veces, el servidor retorna la respuesta original (`HTTP 200` con code `IDEMPOTENCY_REPLAY`) sin ejecutar la operación nuevamente. Las keys expiran a las 24hs.

### 9.2 Auditoría

Cada operación de escritura registra automáticamente:

```json
{
  "audit": {
    "usuario_id":     integer,
    "usuario_nombre": string,
    "accion":         string,
    "timestamp":      date,
    "ip_origen":      string,
    "estado_anterior":string,
    "estado_nuevo":   string,
    "trace_id":       string
  }
}
```

Esta información se publica en el evento al Message Bus y es consumida por el módulo de Administración para el log de auditoría centralizado.

### 9.3 Soft Delete

Los recursos nunca se eliminan físicamente de la base de datos.

```json
{
  "deleted_at": date,
  "deleted_by": integer
}
```

- Las consultas por defecto excluyen registros con `deleted_at != null`.
- Se pueden incluir con `?include_deleted=true` (solo rol `ADMIN`).
- Los proveedores dados de baja conservan su historial de OC.

### 9.4 Rate Limiting

| Grupo de endpoints | Límite | Ventana |
|---|---|---|
| Lectura (`GET`) | 300 req | por minuto / por usuario |
| Escritura (`POST`, `PUT`, `PATCH`) | 60 req | por minuto / por usuario |
| `POST /recepciones` | 20 req | por minuto / por usuario |
| `GET /reportes/*` | 10 req | por minuto / por usuario |

**Headers de respuesta:**
```
X-RateLimit-Limit:     300
X-RateLimit-Remaining: 247
X-RateLimit-Reset:     1700000060
```

### 9.5 Timeouts y reintentos

| Operación | Timeout | Reintentos |
|---|---|---|
| Endpoints REST | 30s | Sin reintento automático (cliente decide) |
| Publicación al Message Bus | 5s | 3 reintentos con backoff exponencial |
| Generación de PDF | 60s | Sin reintento |

### 9.6 Health checks

| Endpoint | Descripción |
|---|---|
| `GET /health` | Estado general del servicio |
| `GET /health/ready` | Listo para recibir tráfico (DB conectada, bus conectado) |
| `GET /health/live` | Proceso activo |

**Response `GET /health`:**
```json
{
  "status":    "healthy",
  "version":   "1.0.0",
  "timestamp": date,
  "checks": {
    "database":    "ok",
    "message_bus": "ok",
    "auth_service":"ok"
  }
}
```

---

## 10. Versionado

La API usa versionado en la URL (`/api/v1/`).

| Tipo de cambio | Incrementa versión | Ejemplo |
|---|---|---|
| Nuevo endpoint | No | `GET /ordenes/{id}/timeline` |
| Nuevo campo opcional en response | No | Agregar `"numero_seguimiento"` |
| Nuevo campo requerido en request | **Sí** | Hacer `proveedor_id` obligatorio |
| Cambio en nombre de campo | **Sí** | Renombrar `total` → `total_ars` |
| Eliminación de endpoint | **Sí** | Deprecar `GET /ordenes/legacy` |
| Cambio en lógica de estados | **Sí** | Agregar estado `EN_REVISION` |

**Política de deprecación:**
- Al publicar `/api/v2/`, la versión anterior (`v1`) se mantiene activa por **mínimo 6 meses**.
- Se notifica a los consumidores con al menos 60 días de anticipación vía el header `Deprecation: true` en todas las respuestas de la versión deprecada.

---

*ERP-LG · Módulo Compras · v1.0 draft · Confidencial*