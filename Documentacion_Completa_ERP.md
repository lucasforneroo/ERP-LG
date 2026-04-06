# Documentación Completa del Proyecto: API REST ERP Industrial

Este documento consolida toda la planificación estratégica, la arquitectura de dominio, los endpoints, la división de responsabilidades (Tracks) y las instrucciones de ejecución paso a paso para el desarrollo del ERP Industrial basado en DDD (Domain-Driven Design). 

---

## ÍNDICE
1. **Planificación Estratégica (Arquitectura General)**
2. **Arquitectura de Endpoints (Flujo del Negocio)**
3. **División de Trabajo - Track 1: Dominio y Negocio**
4. **División de Trabajo - Track 2: Infraestructura y Seguridad**
5. **Ejecución Paso a Paso - Track 2 (Infraestructura)**
6. **Ejecución Paso a Paso - Track 1 (Negocio)**
7. **Anexo: Información Adicional (Cliente)**

---

<br>

# 1. Planificación Estratégica (Arquitectura General)

## Visión General y Filosofía
Acá la regla es clara: **CONCEPTS > CODE**. No vamos a armar un rejunte de endpoints sin sentido; vamos a diseñar un sistema robusto basado en **Domain-Driven Design (DDD)**. Cada nodo que vimos en tu esquema (Comercial, Desarrollo, Compras, etc.) representa un *Bounded Context* (Contexto Delimitado). 

Además, habiendo analizado la **Orden de Fabricación (OF 1128)**, ya tenemos claro qué nivel de detalle manejan: plazos, fletes, contactos técnicos, garantías y especificaciones (como pintura y anexos). Esa OF es un *Aggregate Root* espectacular para empezar.

Esta es la hoja de ruta para definir los métodos, requests/responses, el CRUD y los estándares REST de nuestra API.

### Fase 1: Identificación de Dominios y Entidades (Semana 1)
Antes de definir URLs, definimos qué cosas existen en nuestro mundo.

**Restricción Técnica (Punto Cero): Entorno 100% Dockerizado**
El desarrollo parte absolutamente desde cero. Los desarrolladores **NO tienen instalado Python, ni Node, ni bases de datos locales**. La única herramienta instalada en sus máquinas es **Docker**. Por lo tanto, toda la arquitectura (desde el servidor de desarrollo de FastAPI con hot-reload hasta las migraciones de BD) debe ejecutarse exclusivamente dentro de contenedores.

1. **Dominio Comercial:** `Cliente`, `OrdenFabricacion` (OF), `Anticipo`.
2. **Dominio Administración:** `Factura`, `AutorizacionDespacho`, `TransaccionFinanciera`.
3. **Dominio Desarrollo (Ingeniería):** `Plano`, `ListaMateriales` (BOM), `EspecificacionTecnica`.
4. **Dominio Compras:** `PedidoCompra` (OC), `Proveedor`.
5. **Dominio Pañol (Inventario):** `Material`, `Stock`, `MovimientoStock`.
6. **Dominio Producción:** `LoteProduccion`, `ParteDiario`.
7. **Dominio Logística:** `Despacho`, `Remito`, `Transportista`.

### Fase 2: Definición del Estándar REST y CRUD Básico (Semana 1-2)
Acá seteamos las reglas del juego para que todos los endpoints hablen el mismo idioma.
- **Convención de URLs:** Sustantivos en plural, minúsculas, separados por guiones. Ej: `/api/v1/ordenes-fabricacion`.
- **Verbos HTTP (CRUD):** `GET`, `POST`, `PUT`, `PATCH`, `DELETE` lógico.
- **Respuestas (Status Codes):** 200, 201, 400, 401, 403, 404, 500.

### Fase 3: Diseño de Endpoints Contractuales (Flujos del Negocio) (Semana 2-3)
Mapeamos las flechas del diagrama a endpoints de negocio reales.
*(Nota: El detalle exhaustivo se encuentra en la sección 2 "Arquitectura de Endpoints")*

### Fase 4: Arquitectura de Peticiones y Respuestas (Semana 3)
Para mantener consistencia, diseñaremos un "Wrapper" para todas las peticiones (Success y Error estandarizados).

### Fase 5: Seguridad, Roles y Trazabilidad (Semana 4)
- **Autenticación:** Uso de JWT (JSON Web Tokens).
- **Autorización (RBAC):** Roles basados en los nodos (Comercial, Pañol, etc.).
- **Trazabilidad (Audit Trail):** Registro de `user_id`, `timestamp` y campos modificados.

---

<br>

# 2. Arquitectura de Endpoints (Flujo del Negocio)

Este detalle refleja la arquitectura de endpoints REST basada estrictamente en los flujos (flechas) del diagrama de procesos del ERP.

### 2.1. Dominio Comercial (`/api/v1/comercial`)
- `POST /clientes`: Alta de un nuevo cliente en el sistema.
- `POST /ordenes-fabricacion`: Emite la Orden de Fabricación (OF) y notifica al dominio de **Desarrollo**.
- `POST /anticipos`: Registra los datos del cliente y el anticipo financiero, enviándolos a **Administración**.

### 2.2. Dominio Administración (`/api/v1/administracion`)
- `PUT /anticipos/{anticipo_id}/validar`: Valida los datos y el pago del anticipo, respondiendo a **Comercial**.
- `PUT /despachos/{despacho_id}/aprobar`: Evalúa la "Autorización de despacho" recibida de Logística y emite la aprobación final.

### 2.3. Dominio Desarrollo (`/api/v1/desarrollo`)
- `POST /pedidos-material`: En base a la OF, genera el listado de materiales necesarios y lo envía a **Compras**.
- `POST /planos`: Envía los planos técnicos finalizados al área de **Producción**.

### 2.4. Dominio Compras (`/api/v1/compras`)
- `POST /facturas`: Registra la compra de los materiales y envía la información al **Pañol** para el ingreso físico.

### 2.5. Dominio Pañol (`/api/v1/panol`)
- `POST /ingresos`: Registra el ingreso de materiales basado en la "Factura Compra" de Compras.
- `POST /movimientos/produccion`: Despacha el stock físico de materiales hacia **Producción**.

### 2.6. Dominio Producción (`/api/v1/produccion`)
- `POST /lotes-terminados`: Una vez que la producción se completa (usando Planos y Stock), transfiere el producto a **Logística**.

### 2.7. Dominio Logística (`/api/v1/logistica`)
- `POST /despachos/{despacho_id}/solicitar-autorizacion`: Envía a **Administración** la solicitud para despachar.
- `POST /despachos/{despacho_id}/ejecutar`: Registra la salida física del equipo hacia el cliente (solo si fue aprobado).

---

<br>

# 3. División de Trabajo - Track 1: Dominio y Negocio

## Visión General
Nuestro objetivo en este track es modelar la realidad industrial de la planta. Nos enfocaremos en **qué** hace el sistema y cómo fluye la información entre los distintos sectores.

## Responsabilidades de Implementación
Para cada endpoint mencionado en la sección de Arquitectura (Sección 2), el equipo de Track 1 debe definir:
1. **Modelos Pydantic (Schemas):** Los payloads exactos de Request y Response (ej. los campos requeridos en la OF 1128).
2. **Lógica de Validación:** Reglas de negocio (ej. "No se puede emitir una OF sin plazo de entrega").
3. **Máquinas de Estado:** Cómo cambia el estado de la OF o del Lote a medida que avanza por los dominios.

---

<br>

# 4. División de Trabajo - Track 2: Infraestructura y Seguridad

## Visión General
Mientras el Track 1 se enfoca en *qué* hace el sistema (el negocio), el Track 2 se enfoca en *cómo* lo hace de forma segura, escalable y mantenible. Somos los dueños de los **Cross-Cutting Concerns**.

## Responsabilidades de Implementación
1. **Estándares REST y Wrappers:** Diseñar interceptores para envolver los payloads de éxito/error de manera consistente.
2. **Persistencia:** Configuración de SQLModel, Alembic, Transaccionalidad y Soft Deletes.
3. **Seguridad (RBAC):** Sistema JWT y middlewares como `@require_role(["COMERCIAL"])`.
4. **Trazabilidad (Audit Trail):** Intercepción de base de datos para loguear auditorías.
5. **Arquitectura de Integración:** Herramientas HTTP síncronas o colas asíncronas para conectar los dominios.

---

<br>

# 5. Ejecución Paso a Paso - Track 2 (Infraestructura)

## 🎯 Objetivo
Construir los cimientos del ERP desde cero.
**Hito de finalización:** El sistema debe poder levantarse localmente y el usuario debe poder abrir **Postman**, hacer un `POST` al endpoint de Login, recibir un JWT, y tener el sistema listo para ser empaquetado en Docker.

### 🛠️ Paso 1: Setup Base y Conexión a Base de Datos
1. **SQLModel Asíncrono:** Conectar FastAPI a MariaDB/PostgreSQL (`.env`).
2. **Manejo de Sesiones:** Inyección de dependencia `get_session`.
3. **Migraciones:** Inicializar Alembic.

### 🛡️ Paso 2: Seguridad, JWT y Roles (RBAC)
1. **Modelo:** Crear la entidad `Usuario` (email, password_hash, rol).
2. **Autenticación:** Crear `POST /api/v1/auth/login`.
3. **Roles:** Programar la dependencia `@require_role(["ROL"])`.

### 📦 Paso 3: Estándares REST (Wrappers y Errores)
1. **Success:** Middleware para devolver `{ "success": true, "data": {...} }`.
2. **Error:** Interceptor para devolver `{ "success": false, "error": {...} }`.

### 🐳 Paso 4: Preparación para Producción
1. **Dockerfile:** Multi-stage build para FastAPI.
2. **Docker Compose:** Orquestar API + BD.

---

<br>

# 6. Ejecución Paso a Paso - Track 1 (Negocio)

## 🎯 Objetivo
Construir el flujo de negocio del ERP basado en DDD.
**Hito de finalización:** El usuario podrá abrir **Postman** y simular el ciclo de vida completo de la Orden de Fabricación 1128 cruzando todos los departamentos.

### 🏗️ Paso 1: Modelado de Datos (SQLModel)
Definir las tablas y los Pydantic Schemas para:
`Cliente`, `OrdenFabricacion`, `Anticipo`, `Factura`, `PedidoCompra`, `Material`, `Despacho`.

### 🤝 Paso 2: Endpoints - Fase Inicial
1. **Comercial:** Implementar `POST /api/v1/comercial/ordenes-fabricacion`. (Requiere rol COMERCIAL).
2. **Administración:** Implementar `PUT /api/v1/administracion/anticipos/{id}/validar`. (Requiere rol ADMINISTRACION).

### ⚙️ Paso 3: Endpoints - Fase Media
1. **Desarrollo:** `POST /api/v1/desarrollo/planos` y `POST /api/v1/desarrollo/pedidos-material`.
2. **Compras:** `POST /api/v1/compras/facturas`.
3. **Pañol:** `POST /api/v1/panol/ingresos` y `POST /api/v1/panol/movimientos/produccion`. (Requiere rol PANOL).

### 🏭 Paso 4: Endpoints - Fase Final
1. **Producción:** Implementar `POST /api/v1/produccion/lotes-terminados`. Validar stock previo.
2. **Logística:** Implementar `POST /api/v1/logistica/despachos/{id}/ejecutar`. Validar aprobación de Administración.

---

<br>

# 7. Anexo: Información Adicional (Cliente)

Estructura JSON de ejemplo para una preventa/cliente:
```json
[
  {
    "preventa": {
      "id": 1,
      "razon_social": "Cliente de Ejemplo SA",
      "cuit": 30123456789,
      "direccion": "Ruta Nacional 34 Km 200"
    }
  }
]
```