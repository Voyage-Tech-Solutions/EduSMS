# System Admin Dashboard - Complete Implementation

## Overview

The System Admin dashboard is the **SaaS control center** for EduCore. It manages platform-level operations, NOT school operations. This is the "I control the universe" role.

## Purpose

System Admin manages:
- ✅ Tenants (schools) lifecycle
- ✅ Subscription + billing + entitlements
- ✅ Users and roles (platform-level)
- ✅ Security policies + audit trails
- ✅ Uptime/health + logs
- ✅ Support tickets + incidents
- ✅ Feature flags + releases
- ✅ Data retention + backups

## Architecture

### Backend Structure

```
backend/
├── app/api/v1/
│   └── sysadmin.py          # Complete SaaS API
├── database/
│   └── system_admin_schema.sql  # Database schema
```

### Frontend Structure

```
frontend/src/app/dashboard/sysadmin/
├── page.tsx                 # Overview/Dashboard
├── tenants/
│   └── page.tsx            # Tenant management
├── billing/
│   └── page.tsx            # Subscriptions & invoices
├── features/
│   └── page.tsx            # Feature flags
├── security/
│   └── page.tsx            # Audit logs & incidents
├── monitoring/
│   └── page.tsx            # System health
└── support/
    └── page.tsx            # Support tickets
```

## Database Schema

### Core Tables

1. **Subscriptions** - Tenant billing plans
2. **Invoices** - Billing invoices
3. **Payments** - Payment attempts and history
4. **Coupons** - Discount codes
5. **Feature Flags** - Feature rollout control
6. **Tenant Features** - Per-tenant feature enablement
7. **Plan Entitlements** - Plan limits and features
8. **Security Incidents** - Security event tracking
9. **API Keys** - Tenant API access
10. **System Health Metrics** - Performance monitoring
11. **Background Jobs** - Async job tracking
12. **Webhook Deliveries** - Webhook event tracking
13. **Support Tickets** - Customer support
14. **Ticket Messages** - Support conversations
15. **Platform Settings** - Global configuration

### Enhanced Tables

- **schools** - Added plan_type, max_students, features, subscription_status, etc.
- **audit_logs** - Added severity, ip_address, user_agent, metadata

## API Endpoints

### Overview Module
```
GET /api/v1/sysadmin/overview
```
Returns platform KPIs: active tenants, MRR/ARR, users, uptime, incidents

### Tenants Module
```
GET    /api/v1/sysadmin/tenants
GET    /api/v1/sysadmin/tenants/{tenant_id}
POST   /api/v1/sysadmin/tenants
POST   /api/v1/sysadmin/tenants/{tenant_id}/suspend
POST   /api/v1/sysadmin/tenants/{tenant_id}/activate
```

### Billing Module
```
GET    /api/v1/sysadmin/billing/subscriptions
GET    /api/v1/sysadmin/billing/invoices
GET    /api/v1/sysadmin/billing/payments
```

### Feature Flags Module
```
GET    /api/v1/sysadmin/features/flags
POST   /api/v1/sysadmin/features/flags
PATCH  /api/v1/sysadmin/features/flags/{flag_id}/toggle
```

### Security Module
```
GET    /api/v1/sysadmin/security/audit-logs
GET    /api/v1/sysadmin/security/incidents
GET    /api/v1/sysadmin/security/suspicious-activity
```

### Monitoring Module
```
GET    /api/v1/sysadmin/monitoring/health
GET    /api/v1/sysadmin/monitoring/jobs
```

### Support Module
```
GET    /api/v1/sysadmin/support/tickets
POST   /api/v1/sysadmin/support/tickets
```

## Frontend Pages

### 1. Overview (Command Center)

**Route:** `/dashboard/sysadmin`

**Features:**
- KPI strip: Active tenants, users, MRR/ARR, uptime
- Tenant health snapshot table
- System health metrics
- Churn rate, payment failures, incidents

**Components:**
- StatCard for KPIs
- Table for tenant health
- Cards for additional metrics

### 2. Tenants

**Route:** `/dashboard/sysadmin/tenants`

**Features:**
- List all tenants with filters (status, plan, search)
- View tenant details
- Suspend/activate tenants
- Create new tenants
- Usage stats (students, users, storage)

**Actions:**
- View tenant detail
- Suspend (requires reason + confirmation)
- Activate
- Create tenant

### 3. Billing

**Route:** `/dashboard/sysadmin/billing`

**Features:**
- Subscriptions tab: Active subscriptions, plan details
- Invoices tab: All invoices, payment status
- Payments tab: Payment attempts, failures

**Actions:**
- Manage subscription
- View invoice PDF
- Retry failed payment
- Apply coupon

### 4. Features

**Route:** `/dashboard/sysadmin/features`

**Features:**
- List all feature flags
- Toggle flags globally
- View rollout percentage
- See tenant enablement count

**Actions:**
- Create feature flag
- Toggle global enable/disable
- Configure rollout percentage
- Enable for specific tenants

**Best Practices:**
1. Test in staging first
2. Use gradual rollout (10% → 50% → 100%)
3. Monitor error rates
4. Remove flags after full rollout

### 5. Security

**Route:** `/dashboard/sysadmin/security`

**Features:**
- Audit logs: Platform-wide activity tracking
- Incidents: Security event management
- Suspicious activity: Automated detection

**Tabs:**
- Audit Logs: All platform actions with severity
- Incidents: Open/resolved security incidents
- Suspicious Activity: Failed logins, unusual patterns

**Actions:**
- View audit log details
- Investigate incident
- Block IP address
- Create incident

### 6. Monitoring

**Route:** `/dashboard/sysadmin/monitoring`

**Features:**
- System health dashboard
- Service status (DB, Queue, Storage, API)
- Background jobs tracking
- Webhook deliveries

**Metrics:**
- API uptime
- Average response time
- Error rate
- Active connections

**Auto-refresh:** Every 30 seconds

### 7. Support

**Route:** `/dashboard/sysadmin/support`

**Features:**
- Support ticket management
- Priority filtering
- Status tracking
- SLA monitoring

**Ticket Stats:**
- Open tickets
- In progress
- Critical priority
- Resolved (7d)

**Actions:**
- Create ticket
- View ticket details
- Assign to agent
- Update status

## Security & RBAC

### Row-Level Security (RLS)

All system admin tables have RLS policies:
```sql
CREATE POLICY system_admin_only ON table_name
    FOR ALL USING (auth.jwt() ->> 'role' = 'system_admin');
```

### Backend Security

```python
from app.core.security import require_system_admin

@router.get("/endpoint")
async def endpoint(current_user: dict = Depends(require_system_admin)):
    # Only system_admin role can access
```

### Frontend Protection

Sidebar automatically shows system admin navigation only for `system_admin` role:

```typescript
const items = profile?.role === 'system_admin' ? systemAdminNavItems : ...
```

## Non-Negotiable Rules

1. **Every destructive action requires confirmation + reason**
   - Suspend tenant
   - Delete tenant
   - Revoke keys
   - Refund

2. **Everything writes to Audit Logs**
   - All actions logged with severity
   - IP address and user agent tracked
   - Metadata stored for context

3. **Impersonation must be time-limited + logged**
   - Requires reason
   - Shows banner
   - Auto-expires
   - Fully audited

4. **Separation of duties**
   - Billing admin ≠ security admin
   - Read-only auditor role available

5. **Soft delete first, hard delete last**
   - Suspended tenants retain data
   - Deletion requires multi-step confirmation

6. **Environment separation**
   - Staging flags ≠ production flags
   - Environment badge in UI

## Setup Instructions

### 1. Database Setup

Run the schema:
```bash
psql -h your-db-host -U postgres -d your-db -f backend/database/system_admin_schema.sql
```

Or in Supabase SQL Editor:
- Copy contents of `system_admin_schema.sql`
- Run in SQL Editor

### 2. Backend Setup

The router is already registered in `app/api/v1/__init__.py`:
```python
from app.api.v1.sysadmin import router as sysadmin_router
api_router.include_router(sysadmin_router)
```

### 3. Frontend Setup

All pages are created in `/dashboard/sysadmin/`

Sidebar automatically shows correct navigation based on role.

### 4. Create System Admin User

In Supabase:
```sql
UPDATE user_profiles 
SET role = 'system_admin' 
WHERE email = 'admin@yourdomain.com';
```

## Usage

### Access System Admin Dashboard

1. Login with system_admin role
2. Navigate to `/dashboard/sysadmin`
3. Sidebar shows system admin navigation

### Manage Tenants

1. Go to Tenants page
2. Filter by status/plan
3. View tenant details
4. Suspend/activate as needed

### Monitor Platform Health

1. Go to Monitoring page
2. View real-time metrics
3. Check background jobs
4. Auto-refreshes every 30s

### Handle Security Incidents

1. Go to Security page
2. Review audit logs
3. Check suspicious activity
4. Create incidents as needed

### Manage Feature Rollouts

1. Go to Features page
2. Create feature flag
3. Enable in staging
4. Gradual rollout to production
5. Monitor and adjust

## Testing

### Test Tenant Management
```bash
# List tenants
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sysadmin/tenants

# Suspend tenant
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Payment failure"}' \
  http://localhost:8000/api/v1/sysadmin/tenants/{id}/suspend
```

### Test Feature Flags
```bash
# List flags
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sysadmin/features/flags

# Toggle flag
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}' \
  http://localhost:8000/api/v1/sysadmin/features/flags/{id}/toggle
```

## Future Enhancements

### Phase 2
- [ ] Tenant impersonation (with strict logging)
- [ ] Data export (GDPR compliance)
- [ ] Backup management
- [ ] Email/SMS provider configuration
- [ ] Payment provider integration
- [ ] Advanced analytics dashboard

### Phase 3
- [ ] Multi-region support
- [ ] Custom branding per tenant
- [ ] White-label options
- [ ] Advanced reporting
- [ ] Cost analysis
- [ ] Capacity planning

## Troubleshooting

### Issue: System admin can't access pages

**Solution:**
1. Check user role in database:
   ```sql
   SELECT role FROM user_profiles WHERE email = 'your@email.com';
   ```
2. Ensure role is exactly `system_admin`
3. Clear browser cache and re-login

### Issue: RLS policies blocking access

**Solution:**
1. Check JWT contains correct role
2. Verify RLS policies are created
3. Use service role key for admin operations

### Issue: Mock data showing instead of real data

**Solution:**
1. Check Supabase connection
2. Verify `supabase_admin` is initialized
3. Check environment variables

## Support

For issues or questions:
1. Check this documentation
2. Review API endpoint responses
3. Check browser console for errors
4. Review backend logs in `backend/logs/app.log`

## License

MIT License - Part of EduCore SaaS Platform
