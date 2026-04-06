# Hand-off Desarrollador: Track 2 (Infraestructura y Seguridad)

Este documento contiene las instrucciones y los **Prompts exactos** que debés copiar y pegar en tu Asistente de IA (Cursor, GitHub Copilot, Gemini, etc.) para que construya toda la capa de infraestructura del ERP Industrial.

**⚠️ Pre-requisitos:** 
1. Tu Asistente de IA debe tener en su contexto el archivo `Documentacion_Completa_ERP.md`.
2. **El desarrollador arranca desde cero y SOLO tiene Docker instalado.** No hay Python local, ni bases de datos locales. Todo el desarrollo y ejecución de comandos debe hacerse a través de contenedores.

---

## Prompts para el Asistente de IA

Copia y pega estos prompts uno por uno, validando que el código generado funcione antes de pasar al siguiente.

### Prompt 0: Setup del Entorno de Desarrollo (100% Docker)
> "Actuá como un Arquitecto DevOps. El desarrollador que va a construir este sistema empieza desde cero y SOLO tiene instalado Docker en su máquina (no tiene Python local). 
> 1. Creá un `requirements.txt` con las dependencias iniciales: fastapi, sqlmodel, uvicorn, alembic, pyjwt, passlib, asyncpg o asyncmy.
> 2. Creá un `Dockerfile.dev` configurado específicamente para desarrollo local, garantizando que soporte recarga en vivo (hot-reload) de FastAPI.
> 3. Creá un `docker-compose.yml` que levante dos servicios: la base de datos (PostgreSQL/MariaDB) y la API (montando el volumen del código fuente local hacia el contenedor para poder editar el código y ver los cambios al instante).
> 4. Generá las instrucciones exactas de consola (`docker compose up...`) para que el desarrollador pueda levantar este entorno vacío."

### Prompt 1: Setup de Base de Datos y ORM
> "Actuá como un Arquitecto Backend Senior en Python. Ya tenemos el entorno Docker levantado. Basándote en el `Documentacion_Completa_ERP.md` (Track 2), necesito que configures la base del proyecto. 
> 1. Creá la configuración para conectar a una base de datos MariaDB/PostgreSQL usando `SQLModel` asíncrono (con `ext.asyncio`).
> 2. Creá el archivo `database.py` con el motor (`create_async_engine`) y la dependencia `get_session` para inyectar en FastAPI.
> 3. Generá las instrucciones exactas para inicializar `alembic` en este proyecto para el manejo de migraciones."

### Prompt 2: Autenticación JWT y Roles (RBAC)
> "Ahora vamos a implementar la capa de seguridad del Track 2.
> 1. Creá un modelo SQLModel llamado `Usuario` con los campos: `id`, `email`, `password_hash` y `rol` (String).
> 2. Implementá la lógica para generar y validar JSON Web Tokens (JWT) usando `PyJWT` y `passlib` para los hashes.
> 3. Creá el endpoint `POST /api/v1/auth/login` que valide credenciales y devuelva el token.
> 4. (¡Muy Importante!) Creá una dependencia de FastAPI llamada `require_role(roles_permitidos: list[str])` que extraiga el JWT del header, valide el rol del usuario, y arroje un 403 Forbidden si no coincide."

### Prompt 3: Estandarización de Respuestas (Wrappers REST)
> "Necesitamos que toda la API devuelva un formato JSON consistente, sin importar qué endpoint del Track 1 se llame.
> 1. Escribí un Custom Response o Middleware en FastAPI que intercepte las respuestas exitosas y las envuelva en la estructura: `{"success": true, "data": <payload_original>}`.
> 2. Escribí los `ExceptionHandlers` globales para capturar `HTTPException` y excepciones generales, devolviendo: `{"success": false, "error": {"code": "HTTP_ERROR", "message": "...", "details": []}}`.
> 3. Asegurate de que esto se aplique globalmente en `main.py`."

### Prompt 4: Dockerización para Producción
> "Vamos a preparar esta infraestructura para producción.
> 1. Escribí un `Dockerfile` multi-stage optimizado para ejecutar esta aplicación FastAPI con Uvicorn/Gunicorn.
> 2. Escribí un `docker-compose.yml` que levante el servicio de la API y un contenedor de MariaDB. Asegurate de configurar correctamente las variables de entorno (`.env`) entre los contenedores."

### Prompt 5: Pruebas en Postman
> "Para finalizar el Track 2, generá un resumen en Markdown con:
> 1. El comando exacto para levantar la aplicación localmente o con Docker.
> 2. El comando `cURL` o el JSON exacto para crear un usuario de prueba en la BD (o un script de seed).
> 3. El comando `cURL` o el JSON exacto para hacer POST a `/api/v1/auth/login`.
> 4. Instrucciones claras de cómo configurar Postman para usar el JWT devuelto en las siguientes peticiones."