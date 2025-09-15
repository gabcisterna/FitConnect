Plataforma SaaS para Gimnasios (Web + futura App)

Plataforma multi-gimnasio para:

Informativa: páginas de “quiénes somos”, actividades, horarios y contacto.

Reservas: agenda con cupos, reprogramaciones/cancelaciones.

Pagos en línea: pagar reservas y/o mensualidades desde la web.

Notificaciones: a dueños (nuevas reservas/pagos) y a clientes (vencimientos, recordatorios).

Multi-tenant: múltiples gimnasios aislados entre sí, cada uno con su propio panel.

Objetivo: sentar bases sólidas para escalar a app móvil (Android/iOS) sin reescribir lógica.

🚀 Stack sugerido

Frontend: Next.js (React, App Router), TypeScript

UI: Tailwind CSS + shadcn/ui

Autenticación cliente/dueño: NextAuth (JWT/OAuth)

Backend: NestJS (Node.js + TypeScript)

REST/GraphQL (inicialmente REST)

Validación: Zod/DTOs

DB: PostgreSQL (multi-tenant por tenant_id)

ORM: Prisma

Pagos (AR): Mercado Pago (extensible a Stripe/PayPal)

Notificaciones:

Email (SMTP/SendGrid)

WhatsApp (Meta Cloud API / Twilio) o Email/SMS como fallback

Push (más adelante, para la app)

Infra/DevOps:

Monorepo con pnpm workspaces

Docker para desarrollo y producción

CI/CD: GitHub Actions

Deploy: Railway/Fly.io/Render/Heroku (backend) + Vercel (frontend)

🏗️ Arquitectura & Multitenancy

Modelo multi-tenant “single DB, shared schema”:
Todas las tablas clave incluyen tenant_id (gimnasio).

Middleware de backend inyecta tenant_id en cada consulta según:

subdominio (boxfit.miapp.com)

o encabezado/claim del usuario autenticado (dueño/admin).

Aislamiento lógico: ningún recurso se consulta sin tenant_id.

Futuro: migrar a “schema per tenant” si la escala lo requiere.

📦 Estructura de carpetas (monorepo)
gimnasio-saas/
├─ apps/
│  ├─ web/            # Next.js (cliente + panel dueño)
│  └─ api/            # NestJS (REST API)
├─ packages/
│  ├─ ui/             # componentes compartidos (opc.)
│  ├─ config/         # eslint, tsconfig, tailwind config compartidos
│  └─ types/          # tipos compartidos (zod/ts)
├─ infra/
│  ├─ docker/         # Dockerfiles, compose
│  └─ ci/             # workflows de GitHub Actions
├─ docs/              # diagramas, decisiones (ADR), ERD
└─ README.md

🗄️ Esquema inicial de Base de Datos (ERD simplificado)

Tenants

tenants(id, name, slug, owner_user_id, created_at)

Usuarios & Roles

users(id, name, email, phone, password_hash, created_at)

user_roles(id, user_id, tenant_id, role)
Roles: OWNER, STAFF, CLIENT

Clientes

clients(id, tenant_id, name, email, phone, status, created_at)

memberships(id, tenant_id, client_id, plan_id, start_date, end_date, status)

plans(id, tenant_id, name, price, duration_days, description)

Actividades & Turnos

activities(id, tenant_id, name, description)

classes(id, tenant_id, activity_id, starts_at, ends_at, capacity, instructor_id)

bookings(id, tenant_id, class_id, client_id, status, paid, created_at)
status: CONFIRMED|CANCELLED|WAITLIST

Pagos

payments(id, tenant_id, client_id, booking_id?, membership_id?, provider, provider_ref, amount, currency, status, created_at)

Notificaciones

notifications(id, tenant_id, type, to, payload_json, status, scheduled_at, sent_at)

Reglas clave:

Índices por (tenant_id, ...) en todas las tablas.

Restricciones FK incluyen tenant_id para evitar mezclas entre gimnasios.

🔐 Autenticación & Autorización

NextAuth en apps/web (OAuth/JWT).

API Keys por tenant para integraciones.

RBAC (Owner/Staff/Client) aplicado en API con guards/policies.

💳 Flujo de pago (ejemplo Mercado Pago)

Cliente inicia reserva → backend crea preferencia con MP.

Redirección a checkout → al aprobar, webhook → payments.status = approved.

Marca bookings.paid = true o genera/renueva memberships.

Emite comprobante simple (PDF/Email).

🔔 Notificaciones

Dueña/Staff: email/WhatsApp al crear/cancelar reserva y pago aprobado.

Clientes:

recordatorio de clase (24h/2h antes)

aviso de vencimiento de membresía (7 días antes + día de vencimiento).

Cola de trabajos programados (NestJS + BullMQ/Redis).

🔌 Endpoints (borrador)
POST   /auth/login
GET    /me

# Tenancy
GET    /tenants/:slug/config

# Clientes
GET    /clients
POST   /clients
GET    /clients/:id
PATCH  /clients/:id

# Planes & Membresías
GET    /plans
POST   /plans
POST   /memberships
GET    /memberships?client_id=

# Actividades & Clases
GET    /activities
POST   /activities
GET    /classes?activity_id=&from=&to=
POST   /classes
POST   /bookings
PATCH  /bookings/:id/cancel

# Pagos
POST   /payments/checkout (booking_id|membership_id)
POST   /payments/webhook   # proveedor → API
GET    /payments/:id

# Notificaciones
POST   /notifications/test

⚙️ Variables de entorno (ejemplo)

apps/api/.env

DATABASE_URL=postgresql://user:pass@localhost:5432/gimnasio
JWT_SECRET=changeme
MP_ACCESS_TOKEN=xxxx
SMTP_HOST=smtp.example.com
SMTP_USER=no-reply@example.com
SMTP_PASS=xxxx
WHATSAPP_TOKEN=xxxx
BASE_URL_API=http://localhost:3001


apps/web/.env.local

NEXTAUTH_SECRET=changeme
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3001

🧑‍💻 Desarrollo local

Requisitos: Node 20+, pnpm, Docker, Git.

# 1) Clonar y preparar
git clone <repo-url> gimnasio-saas
cd gimnasio-saas
pnpm install

# 2) Levantar Postgres/Redis (dev)
docker compose -f infra/docker/compose.dev.yml up -d

# 3) Migrar Prisma (API)
cd apps/api
pnpm prisma migrate dev

# 4) Correr API y Web
pnpm -w dev
# api en :3001, web en :3000

🧭 Roadmap (MVP → MLP)

MVP (semana 1–3)

 Tenancy base (tenant_id en todo)

 Auth dueña/staff/cliente

 CRUD actividades/clases

 Reservas con cupo

 Checkout con Mercado Pago (booking)

 Email a dueña + recordatorio de clase

 Panel simple para dueña

MLP (semana 4–6)

 Membresías/planes y vencimientos

 Notificaciones de vencimiento (job scheduler)

 Historial de pagos/facturación simple

 Modo “multi-sede” por tenant (opcional)

 Auditoría (quién hizo qué)

Siguientes

 Lista de espera en clases

 App móvil (React Native/Capacitor) con push

 KPI/Analytics por tenant

 Marketplace de integraciones (Stripe/PayPal/Telegram)

🧩 Backlog sugerido (para crear como Issues)

Base monorepo + pnpm

Esquema Prisma con multitenancy

Auth y roles (owner/staff/client)

CRUD actividades/clases

Reservas con cupos y estado

Integración Mercado Pago + webhook

Emails transaccionales (Nodemailer/SendGrid)

Recordatorios de clase (BullMQ/Redis)

Membresías + planes + avisos de vencimiento

Panel dueña: dashboard, clases, clientes, pagos

Landing info pública por subdominio del tenant

End-to-end tests básicos (Playwright)

CI/CD con GitHub Actions

Dockerización y deploy (API + Web)

📝 Decisiones de diseño (ADR)

Registrar en docs/adr/:

ADR-001: estrategia de multitenancy

ADR-002: proveedor de pagos por región (MP primero)

ADR-003: formato de notificaciones y canal por defecto

ADR-004: política de retención de datos

🔒 Seguridad & Privacidad

Encriptar contraseñas (Argon2/BCrypt), rotación de secretos.

Validación de entrada exhaustiva (DTO/Zod).

Registros de acceso y auditoría por tenant.

Política de backups y restauración.

🧪 Tests

Unit: servicios NestJS, utils compartidos.

Integration: endpoints críticos (auth, bookings, payments).

E2E: flujos reserva/pago con datos mock.

🧾 Licencia

MIT (ajustable según el negocio).

🤝 Contribuir

Crear Issue con descripción y criterios de aceptación.

PR con checklist de tests y documentación afectada.

Respetar convención de commits y linters.

Comandos útiles (monorepo)
pnpm -w dev           # levantar web y api en paralelo
pnpm -w build         # build general
pnpm -w lint          # lint
pnpm -w test          # tests
