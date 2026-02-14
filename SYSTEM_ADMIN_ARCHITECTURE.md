# System Admin Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ADMIN DASHBOARD                          │
│                    (SaaS Platform Control Center)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   OVERVIEW    │          │   TENANTS     │          │   BILLING     │
│               │          │               │          │               │
│ • KPIs        │          │ • List        │          │ • Subscriptions│
│ • Metrics     │          │ • Suspend     │          │ • Invoices    │
│ • Health      │          │ • Activate    │          │ • Payments    │
│ • Alerts      │          │ • Create      │          │ • Coupons     │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   FEATURES    │          │   SECURITY    │          │  MONITORING   │
│               │          │               │          │               │
│ • Flags       │          │ • Audit Logs  │          │ • Health      │
│ • Toggle      │          │ • Incidents   │          │ • Jobs        │
│ • Rollout     │          │ • Suspicious  │          │ • Webhooks    │
│ • Per-tenant  │          │ • API Keys    │          │ • Metrics     │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   SUPPORT     │          │   SETTINGS    │          │               │
│               │          │               │          │               │
│ • Tickets     │          │ • Email/SMS   │          │               │
│ • Priority    │          │ • Storage     │          │               │
│ • SLA         │          │ • Security    │          │               │
│ • Status      │          │ • Retention   │          │               │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │      BACKEND API          │
                    │  /api/v1/sysadmin/*       │
                    │                           │
                    │  • require_system_admin   │
                    │  • Audit logging          │
                    │  • RLS policies           │
                    └───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │      SUPABASE DB          │
                    │                           │
                    │  • subscriptions          │
                    │  • invoices               │
                    │  • payments               │
                    │  • feature_flags          │
                    │  • security_incidents     │
                    │  • audit_logs             │
                    │  • support_tickets        │
                    │  • system_health_metrics  │
                    │  • background_jobs        │
                    │  • platform_settings      │
                    └───────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│ System Admin │
│    User      │
└──────┬───────┘
       │
       │ 1. Login with system_admin role
       ▼
┌──────────────────┐
│  JWT Token       │
│  role: system_admin
└──────┬───────────┘
       │
       │ 2. Access /dashboard/sysadmin
       ▼
┌──────────────────┐
│  Sidebar         │
│  (Role-based)    │
└──────┬───────────┘
       │
       │ 3. Navigate to page
       ▼
┌──────────────────┐
│  Frontend Page   │
│  (React)         │
└──────┬───────────┘
       │
       │ 4. authFetch() with JWT
       ▼
┌──────────────────┐
│  Backend API     │
│  require_system_admin()
└──────┬───────────┘
       │
       │ 5. Verify role
       ▼
┌──────────────────┐
│  RLS Policy      │
│  Check JWT role  │
└──────┬───────────┘
       │
       │ 6. Query data
       ▼
┌──────────────────┐
│  Supabase DB     │
│  Return data     │
└──────┬───────────┘
       │
       │ 7. Log action
       ▼
┌──────────────────┐
│  Audit Log       │
│  Record action   │
└──────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────┐
│         Layer 1: Authentication         │
│  JWT token with system_admin role       │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Layer 2: Authorization          │
│  require_system_admin() dependency      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Layer 3: RLS Policies           │
│  Database-level access control          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Layer 4: Audit Logging          │
│  All actions logged with metadata       │
└─────────────────────────────────────────┘
```

## Module Relationships

```
                    ┌─────────────┐
                    │  TENANTS    │
                    │  (Core)     │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   BILLING     │  │   FEATURES    │  │   SECURITY    │
│               │  │               │  │               │
│ • Subscriptions│  │ • Flags       │  │ • Audit Logs  │
│ • Invoices    │  │ • Rollout     │  │ • Incidents   │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  MONITORING │
                    │  (Health)   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   SUPPORT   │
                    │  (Tickets)  │
                    └─────────────┘
```

## Tenant Lifecycle

```
┌─────────────┐
│   CREATE    │  System Admin creates tenant
│   TENANT    │  • Name, code, plan
└──────┬──────┘  • Region, currency
       │
       ▼
┌─────────────┐
│   TRIAL     │  30-day trial period
│   PERIOD    │  • Limited features
└──────┬──────┘  • Usage tracking
       │
       ▼
┌─────────────┐
│   ACTIVE    │  Paid subscription
│ SUBSCRIPTION│  • Full features
└──────┬──────┘  • Billing active
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│  SUSPENDED  │   │   EXPIRED   │
│             │   │             │
│ • Payment   │   │ • Sub ended │
│   failure   │   │ • Grace     │
│ • Violation │   │   period    │
└──────┬──────┘   └──────┬──────┘
       │                 │
       └────────┬────────┘
                ▼
         ┌─────────────┐
         │  DELETED    │  Hard delete after retention
         │             │  • Data exported
         └─────────────┘  • Audit logged
```

## Feature Flag Rollout

```
┌─────────────┐
│   CREATE    │  Create new feature flag
│    FLAG     │  • Name, description
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   STAGING   │  Enable in staging
│    TEST     │  • Test thoroughly
└──────┬──────┘  • Monitor errors
       │
       ▼
┌─────────────┐
│  ROLLOUT    │  Gradual production rollout
│    10%      │  • 10% of tenants
└──────┬──────┘  • Monitor metrics
       │
       ▼
┌─────────────┐
│  ROLLOUT    │  Increase rollout
│    50%      │  • 50% of tenants
└──────┬──────┘  • Check performance
       │
       ▼
┌─────────────┐
│  ROLLOUT    │  Full rollout
│   100%      │  • All tenants
└──────┬──────┘  • Monitor stability
       │
       ▼
┌─────────────┐
│   STABLE    │  Feature is stable
│   REMOVE    │  • Remove flag
└─────────────┘  • Clean up code
```

## Monitoring Flow

```
┌─────────────────────────────────────────┐
│         Application Metrics             │
│  • API response time                    │
│  • Error rate                           │
│  • Request count                        │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         System Health Metrics           │
│  • Database health                      │
│  • Queue status                         │
│  • Storage health                       │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Background Jobs                 │
│  • Job status                           │
│  • Failures                             │
│  • Retries                              │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Monitoring Dashboard            │
│  • Real-time display                    │
│  • Auto-refresh (30s)                   │
│  • Alerts                               │
└─────────────────────────────────────────┘
```

## Support Ticket Flow

```
┌─────────────┐
│   TENANT    │  Tenant reports issue
│   REPORTS   │  • Via email/portal
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   CREATE    │  System creates ticket
│   TICKET    │  • Auto ticket number
└──────┬──────┘  • Set priority/SLA
       │
       ▼
┌─────────────┐
│   ASSIGN    │  Assign to support agent
│   AGENT     │  • Based on category
└──────┬──────┘  • Based on priority
       │
       ▼
┌─────────────┐
│   WORK      │  Agent works on ticket
│   TICKET    │  • Add messages
└──────┬──────┘  • Update status
       │
       ▼
┌─────────────┐
│   RESOLVE   │  Ticket resolved
│   TICKET    │  • Mark resolved
└──────┬──────┘  • Notify tenant
       │
       ▼
┌─────────────┐
│   CLOSE     │  Ticket closed
│   TICKET    │  • After confirmation
└─────────────┘  • Archive
```

---

**Legend:**
- ┌─┐ = Module/Component
- │ = Connection
- ▼ = Data flow direction
- • = Feature/Action
