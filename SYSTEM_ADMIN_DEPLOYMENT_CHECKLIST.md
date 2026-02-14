# System Admin Dashboard - Deployment Checklist

## Pre-Deployment Checklist

### 1. Database Setup ☐

- [ ] Backup existing database
- [ ] Review `backend/database/system_admin_schema.sql`
- [ ] Run schema in Supabase SQL Editor
- [ ] Verify all tables created successfully
- [ ] Check RLS policies are active
- [ ] Verify indexes are created

**Commands:**
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
  'subscriptions', 'invoices', 'payments', 'feature_flags',
  'security_incidents', 'support_tickets', 'platform_settings'
);

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('subscriptions', 'invoices', 'feature_flags');
```

### 2. Backend Configuration ☐

- [ ] Verify `backend/app/api/v1/sysadmin.py` exists
- [ ] Check router is registered in `__init__.py`
- [ ] Verify `require_system_admin` security dependency
- [ ] Test Supabase connection
- [ ] Check environment variables

**Test:**
```bash
cd backend
python -c "from app.api.v1.sysadmin import router; print('✓ Router imported')"
python -c "from app.db.supabase import supabase_admin; print('✓ Supabase connected')"
```

### 3. Frontend Configuration ☐

- [ ] Verify all pages exist in `frontend/src/app/dashboard/sysadmin/`
- [ ] Check sidebar navigation updated
- [ ] Verify authFetch is configured
- [ ] Test API URL in environment variables
- [ ] Build frontend without errors

**Test:**
```bash
cd frontend
npm run build
# Should complete without errors
```

### 4. Create System Admin User ☐

- [ ] Identify admin user email
- [ ] Update user role in database
- [ ] Verify user can login
- [ ] Test access to system admin pages

**SQL:**
```sql
-- Update user role
UPDATE user_profiles 
SET role = 'system_admin' 
WHERE email = 'your-admin@email.com';

-- Verify
SELECT email, role FROM user_profiles WHERE role = 'system_admin';
```

### 5. Security Verification ☐

- [ ] Test non-admin users CANNOT access system admin pages
- [ ] Verify RLS policies block unauthorized access
- [ ] Check audit logging is working
- [ ] Test JWT token validation
- [ ] Verify CORS settings

**Test:**
```bash
# Try accessing with non-admin token (should fail)
curl -H "Authorization: Bearer $NON_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/sysadmin/overview
# Expected: 403 Forbidden
```

## Deployment Steps

### Step 1: Deploy Database Schema ☐

```bash
# Option A: Supabase SQL Editor
1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy contents of backend/database/system_admin_schema.sql
4. Run query
5. Verify success

# Option B: psql command line
psql -h your-db-host -U postgres -d your-db \
  -f backend/database/system_admin_schema.sql
```

**Verification:**
```sql
-- Check table count
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%system%' OR table_name IN (
  'subscriptions', 'invoices', 'payments', 'feature_flags'
);
-- Expected: 15+ tables
```

### Step 2: Deploy Backend ☐

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start server
uvicorn app.main:app --reload

# Verify endpoints
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Test Endpoints:**
```bash
# Get JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@email.com","password":"password"}' \
  | jq -r '.access_token')

# Test system admin endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sysadmin/overview
# Expected: JSON with platform metrics
```

### Step 3: Deploy Frontend ☐

```bash
cd frontend

# Install dependencies
npm install

# Build
npm run build

# Test build
npm start

# Verify pages load
# Navigate to http://localhost:3000/dashboard/sysadmin
```

**Verification:**
- [ ] Overview page loads
- [ ] Tenants page loads
- [ ] Billing page loads
- [ ] Features page loads
- [ ] Security page loads
- [ ] Monitoring page loads
- [ ] Support page loads
- [ ] Settings page loads

### Step 4: Create System Admin User ☐

```sql
-- In Supabase SQL Editor
UPDATE user_profiles 
SET role = 'system_admin' 
WHERE email = 'your-admin@email.com';

-- Verify
SELECT id, email, role, first_name, last_name 
FROM user_profiles 
WHERE role = 'system_admin';
```

### Step 5: Test Complete Flow ☐

1. **Login Test**
   - [ ] Login with system admin credentials
   - [ ] Verify JWT token contains system_admin role
   - [ ] Check sidebar shows system admin navigation

2. **Overview Page Test**
   - [ ] Navigate to `/dashboard/sysadmin`
   - [ ] Verify KPIs display
   - [ ] Check tenant health table loads
   - [ ] Verify metrics are accurate

3. **Tenants Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/tenants`
   - [ ] Verify tenant list loads
   - [ ] Test filters (status, plan, search)
   - [ ] Test suspend action (with confirmation)
   - [ ] Test activate action

4. **Billing Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/billing`
   - [ ] Check subscriptions tab
   - [ ] Check invoices tab
   - [ ] Check payments tab

5. **Features Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/features`
   - [ ] Verify feature flags list
   - [ ] Test toggle switch
   - [ ] Create new feature flag

6. **Security Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/security`
   - [ ] Check audit logs tab
   - [ ] Check incidents tab
   - [ ] Check suspicious activity tab

7. **Monitoring Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/monitoring`
   - [ ] Verify system health metrics
   - [ ] Check service status
   - [ ] Verify auto-refresh works (30s)

8. **Support Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/support`
   - [ ] Verify ticket list loads
   - [ ] Test filters
   - [ ] Create new ticket

9. **Settings Page Test**
   - [ ] Navigate to `/dashboard/sysadmin/settings`
   - [ ] Check all tabs load
   - [ ] Test save functionality

## Post-Deployment Verification

### 1. Security Audit ☐

- [ ] Non-admin users cannot access system admin pages
- [ ] API endpoints return 403 for non-admin users
- [ ] RLS policies are enforced
- [ ] Audit logs are being created
- [ ] IP addresses are being tracked

**Test:**
```bash
# Login as non-admin user
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@school.com","password":"password"}' \
  | jq -r '.access_token')

# Try to access system admin endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sysadmin/overview
# Expected: 403 Forbidden
```

### 2. Performance Check ☐

- [ ] Pages load in < 2 seconds
- [ ] API responses in < 500ms
- [ ] No console errors
- [ ] No memory leaks
- [ ] Database queries are optimized

**Monitor:**
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sysadmin/overview
```

### 3. Data Integrity ☐

- [ ] Audit logs are being created
- [ ] Timestamps are correct
- [ ] Foreign keys are working
- [ ] Cascading deletes work correctly
- [ ] Data is not duplicated

**Verify:**
```sql
-- Check audit logs
SELECT COUNT(*) FROM audit_logs 
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Check foreign keys
SELECT COUNT(*) FROM subscriptions s
LEFT JOIN schools sc ON s.school_id = sc.id
WHERE sc.id IS NULL;
-- Expected: 0
```

### 4. Monitoring Setup ☐

- [ ] System health metrics are updating
- [ ] Background jobs are running
- [ ] Webhooks are being tracked
- [ ] Error rates are being monitored
- [ ] Alerts are configured

### 5. Documentation ☐

- [ ] Team trained on system admin features
- [ ] Documentation shared with team
- [ ] Runbook created for common tasks
- [ ] Emergency procedures documented
- [ ] Contact information updated

## Production Checklist

### Before Going Live ☐

- [ ] All tests passing
- [ ] Security audit complete
- [ ] Performance benchmarks met
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Team trained

### Go-Live Steps ☐

1. [ ] Deploy database schema to production
2. [ ] Deploy backend to production
3. [ ] Deploy frontend to production
4. [ ] Create production system admin user
5. [ ] Verify all pages load
6. [ ] Test critical flows
7. [ ] Monitor for errors
8. [ ] Announce to team

### Post-Launch Monitoring ☐

**First Hour:**
- [ ] Check error rates
- [ ] Monitor API response times
- [ ] Verify audit logs
- [ ] Check user access

**First Day:**
- [ ] Review all metrics
- [ ] Check for any issues
- [ ] Gather user feedback
- [ ] Monitor performance

**First Week:**
- [ ] Analyze usage patterns
- [ ] Optimize slow queries
- [ ] Address any bugs
- [ ] Plan improvements

## Rollback Plan

### If Issues Occur ☐

1. **Database Issues:**
   ```sql
   -- Restore from backup
   -- Remove new tables if needed
   DROP TABLE IF EXISTS subscriptions CASCADE;
   DROP TABLE IF EXISTS invoices CASCADE;
   -- etc.
   ```

2. **Backend Issues:**
   ```bash
   # Revert to previous version
   git revert <commit-hash>
   # Redeploy
   ```

3. **Frontend Issues:**
   ```bash
   # Revert to previous version
   git revert <commit-hash>
   # Rebuild and redeploy
   npm run build
   ```

## Success Criteria

### Deployment is Successful When: ✓

- [ ] All pages load without errors
- [ ] API endpoints respond correctly
- [ ] Security policies are enforced
- [ ] Audit logging is working
- [ ] Performance meets benchmarks
- [ ] No critical bugs
- [ ] Team can use features
- [ ] Documentation is complete

## Support Contacts

- **Database Issues:** DBA Team
- **Backend Issues:** Backend Team
- **Frontend Issues:** Frontend Team
- **Security Issues:** Security Team
- **Emergency:** On-call Engineer

## Notes

- Keep this checklist updated
- Document any issues encountered
- Share learnings with team
- Celebrate successful deployment! 🎉

---

**Last Updated:** 2024-03-20
**Version:** 1.0
**Status:** Ready for Deployment
