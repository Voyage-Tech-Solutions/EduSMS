# System Admin Dashboard - Quick Reference

## 🎯 Purpose
**SaaS Operations Control** - NOT school operations. This is platform management.

## 🚀 Quick Access

### Routes
```
/dashboard/sysadmin              → Overview (Command Center)
/dashboard/sysadmin/tenants      → Tenant Management
/dashboard/sysadmin/billing      → Subscriptions & Invoices
/dashboard/sysadmin/features     → Feature Flags
/dashboard/sysadmin/security     → Audit Logs & Incidents
/dashboard/sysadmin/monitoring   → System Health
/dashboard/sysadmin/support      → Support Tickets
```

## 📊 Key Features

### Overview Page
- **KPIs**: Active tenants, MRR/ARR, users, uptime
- **Tenant Health**: Real-time tenant status
- **Metrics**: Churn rate, payment failures, incidents

### Tenants Page
- List all schools (tenants)
- Filter by status/plan
- Suspend/activate tenants
- View usage stats
- Create new tenants

### Billing Page
- **Subscriptions**: Active plans, billing cycles
- **Invoices**: Payment status, due dates
- **Payments**: Attempts, failures, retries

### Features Page
- Create/manage feature flags
- Toggle global enable/disable
- Gradual rollout (10% → 50% → 100%)
- Per-tenant enablement

### Security Page
- **Audit Logs**: All platform actions
- **Incidents**: Security events
- **Suspicious Activity**: Auto-detection

### Monitoring Page
- System health metrics
- Service status (DB, Queue, API)
- Background jobs
- Auto-refresh every 30s

### Support Page
- Ticket management
- Priority/status filtering
- SLA tracking
- Ticket stats

## 🔐 Security

### Access Control
- Only `system_admin` role can access
- RLS policies on all tables
- Backend: `require_system_admin` dependency
- Frontend: Role-based sidebar

### Audit Trail
- All actions logged
- IP address tracked
- Severity levels
- Metadata stored

## 🛠️ Common Tasks

### Create System Admin User
```sql
UPDATE user_profiles 
SET role = 'system_admin' 
WHERE email = 'admin@yourdomain.com';
```

### Suspend Tenant
1. Go to Tenants page
2. Click Ban icon
3. Enter reason
4. Confirm action
5. Action logged in audit trail

### Enable Feature Flag
1. Go to Features page
2. Toggle switch
3. Or create new flag
4. Set rollout percentage
5. Monitor impact

### View Audit Logs
1. Go to Security page
2. Select "Audit Logs" tab
3. Filter by severity/action
4. View details

### Check System Health
1. Go to Monitoring page
2. View real-time metrics
3. Check service status
4. Review background jobs

## 📝 API Quick Reference

### Tenants
```bash
GET    /api/v1/sysadmin/tenants
POST   /api/v1/sysadmin/tenants/{id}/suspend
POST   /api/v1/sysadmin/tenants/{id}/activate
```

### Billing
```bash
GET    /api/v1/sysadmin/billing/subscriptions
GET    /api/v1/sysadmin/billing/invoices
GET    /api/v1/sysadmin/billing/payments
```

### Features
```bash
GET    /api/v1/sysadmin/features/flags
PATCH  /api/v1/sysadmin/features/flags/{id}/toggle
```

### Security
```bash
GET    /api/v1/sysadmin/security/audit-logs
GET    /api/v1/sysadmin/security/incidents
GET    /api/v1/sysadmin/security/suspicious-activity
```

### Monitoring
```bash
GET    /api/v1/sysadmin/monitoring/health
GET    /api/v1/sysadmin/monitoring/jobs
```

## ⚠️ Critical Rules

1. **Destructive actions require confirmation + reason**
2. **Everything writes to audit logs**
3. **Impersonation must be logged**
4. **Soft delete before hard delete**
5. **Test in staging first**

## 🎨 UI Components Used

- **Card**: Container for sections
- **Table**: Data display
- **Badge**: Status indicators
- **Button**: Actions
- **Tabs**: Multi-view pages
- **Select**: Filters
- **Switch**: Toggle controls

## 📈 Metrics Tracked

- Active tenants
- MRR/ARR
- Active users (30d)
- System uptime
- Churn rate
- Payment failures
- Open incidents
- API response time
- Error rate

## 🔄 Auto-Refresh

- **Monitoring page**: Every 30 seconds
- **Other pages**: Manual refresh

## 📱 Responsive Design

All pages are mobile-responsive using Tailwind CSS grid system.

## 🚨 Troubleshooting

### Can't access System Admin pages?
- Check role is `system_admin`
- Clear cache and re-login
- Verify JWT token

### No data showing?
- Check Supabase connection
- Verify environment variables
- Check browser console

### RLS blocking access?
- Verify RLS policies created
- Check JWT role claim
- Use service role for admin ops

## 📚 Full Documentation

See `SYSTEM_ADMIN_IMPLEMENTATION.md` for complete details.

## ✅ Setup Checklist

- [ ] Run database schema
- [ ] Create system admin user
- [ ] Test API endpoints
- [ ] Access dashboard
- [ ] Verify all pages load
- [ ] Test tenant management
- [ ] Test feature flags
- [ ] Review audit logs
- [ ] Check monitoring metrics

## 🎯 Next Steps

1. Deploy database schema
2. Create your system admin user
3. Login and access `/dashboard/sysadmin`
4. Explore each module
5. Configure feature flags
6. Set up monitoring alerts
7. Review security policies

---

**Remember**: System Admin is for SaaS operations, not school operations. Keep them separate!
