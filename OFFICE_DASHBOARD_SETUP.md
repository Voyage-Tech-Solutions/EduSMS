# Office Dashboard Setup Guide

## Quick Start

Follow these steps to deploy the Office Dashboard implementation.

---

## Step 1: Database Setup

### Run SQL Scripts in Supabase

1. Go to your Supabase project
2. Navigate to SQL Editor
3. Run these scripts in order:

```sql
-- First, run the new tables
-- Copy and paste content from: backend/database/office_dashboard_schema.sql
```

```sql
-- Then, run the RPC functions
-- Copy and paste content from: backend/database/office_dashboard_functions.sql
```

### Verify Tables Created

Run this query to verify:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'student_documents',
    'payment_plans',
    'transfer_requests',
    'letter_requests',
    'notifications_log',
    'attendance_sessions',
    'parent_student_links',
    'messages',
    'assessments',
    'assessment_scores'
);
```

You should see all 10 tables listed.

---

## Step 2: Backend Verification

### Check if office_admin router is registered

The router is already registered in `backend/app/api/v1/__init__.py`:

```python
api_router.include_router(office_admin_router, prefix="/office-admin", tags=["office_admin"])
```

### Test Backend Endpoints

Start your backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs

Look for these endpoints under "office_admin" tag:
- GET /api/v1/office-admin/dashboard/priorities
- GET /api/v1/office-admin/fees/snapshot
- GET /api/v1/office-admin/students/snapshot
- GET /api/v1/office-admin/documents/compliance
- GET /api/v1/office-admin/activity/recent
- GET /api/v1/office-admin/exceptions
- POST /api/v1/office-admin/attendance/save
- POST /api/v1/office-admin/invoice/create
- POST /api/v1/office-admin/student/add
- POST /api/v1/office-admin/staff/add
- POST /api/v1/office-admin/notifications/bulk
- POST /api/v1/office-admin/payment/allocate

---

## Step 3: Frontend Setup

### Install Dependencies (if needed)

```bash
cd frontend
npm install @radix-ui/react-radio-group
```

### Verify Files Exist

Check these files were created:
- `frontend/src/components/dashboard/office-modals.tsx`
- `frontend/src/components/ui/radio-group.tsx`

Check this file was updated:
- `frontend/src/components/dashboard/office-admin-dashboard.tsx`

### Start Frontend

```bash
npm run dev
```

Visit: http://localhost:3000

---

## Step 4: Test the Dashboard

### Login as Office Admin

1. Create a test user with role `office_admin`
2. Login to the system
3. You should see the Office Operations Dashboard

### Test Each Section

#### Today's Priorities
- Should show 6 metrics with counts
- Each row should have an action button

#### Fees & Payments Snapshot
- Should show 4 financial metrics
- "Save Attendance" button should open modal
- "Create Invoice" button should open modal

#### Student Admin Snapshot
- Should show 4 student metrics
- "Add Student" button should open modal
- "Add Staff" button should open modal

#### Quick Reports
- Should show 4 report buttons
- Each should link to reports page

#### Documents & Compliance
- Should show 3 document compliance metrics
- "Send Bulk Reminder" button should open modal

---

## Step 5: Test Action Buttons

### Save Attendance Modal
1. Click "Save Attendance"
2. Select date and class
3. Mark attendance for students
4. Submit
5. Verify dashboard refreshes

### Create Invoice Modal
1. Click "Create Invoice"
2. Fill in student, amount, due date
3. Submit
4. Verify dashboard refreshes

### Add Student Modal
1. Click "Add Student"
2. Fill in all required fields
3. Submit
4. Verify student appears in system

### Add Staff Modal
1. Click "Add Staff"
2. Fill in staff details
3. Submit
4. Verify invitation created

### Bulk Reminder Modal
1. Click "Send Bulk Reminder"
2. Select target group
3. Choose delivery method
4. Write message
5. Submit
6. Verify notifications queued

---

## Step 6: Verify Database Changes

### Check Audit Logs

```sql
SELECT * FROM audit_logs 
WHERE entity_type IN ('attendance', 'invoice', 'student', 'invitation', 'notification')
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Student Documents

```sql
SELECT s.first_name, s.last_name, sd.document_type, sd.status
FROM students s
JOIN student_documents sd ON sd.student_id = s.id
ORDER BY s.created_at DESC
LIMIT 10;
```

### Check Attendance Sessions

```sql
SELECT * FROM attendance_sessions
ORDER BY created_at DESC
LIMIT 5;
```

---

## Troubleshooting

### Backend Issues

**Error: "office_admin router not found"**
- Check `backend/app/api/v1/__init__.py` includes the router
- Restart backend server

**Error: "Table does not exist"**
- Run the SQL scripts in Supabase
- Verify tables created with SELECT query

**Error: "RPC function not found"**
- Run `office_dashboard_functions.sql`
- Check function exists: `SELECT * FROM pg_proc WHERE proname LIKE 'count_unverified%';`

### Frontend Issues

**Error: "Cannot find module 'office-modals'"**
- Verify file exists at correct path
- Check import statement matches filename

**Error: "RadioGroup not found"**
- Install: `npm install @radix-ui/react-radio-group`
- Verify `radio-group.tsx` exists in `components/ui/`

**Modal doesn't open**
- Check browser console for errors
- Verify state management (useState hooks)

### Database Issues

**RLS Policy blocking queries**
- Verify user has correct role
- Check `get_user_school_id()` function returns correct school
- Temporarily disable RLS for testing: `ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;`

**Slow queries**
- Check indexes exist
- Run EXPLAIN ANALYZE on slow queries
- Consider materialized views for aggregations

---

## Performance Optimization

### Add Indexes (if not already present)

```sql
CREATE INDEX IF NOT EXISTS idx_invoices_school_status ON invoices(school_id, status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_students_admission_date ON students(admission_date);
CREATE INDEX IF NOT EXISTS idx_student_documents_uploaded ON student_documents(uploaded);
```

### Create Materialized View for Dashboard (Optional)

```sql
CREATE MATERIALIZED VIEW office_dashboard_summary AS
SELECT 
    school_id,
    COUNT(*) FILTER (WHERE status = 'active') as active_students,
    COUNT(*) FILTER (WHERE admission_date >= date_trunc('month', CURRENT_DATE)) as new_this_month,
    (SELECT COUNT(*) FROM transfer_requests WHERE status = 'pending') as pending_transfers
FROM students
GROUP BY school_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW office_dashboard_summary;
```

---

## Security Checklist

- [ ] All endpoints require authentication
- [ ] Role-based access enforced (office_admin, principal)
- [ ] RLS policies active on all tables
- [ ] Audit logging enabled for all actions
- [ ] Input validation on all forms
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (React escapes by default)
- [ ] CSRF protection (JWT tokens)

---

## Production Deployment

### Environment Variables

Ensure these are set:

**Backend (.env)**
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET_KEY=your_secret_key
```

**Frontend (.env)**
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api/v1
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### Build Commands

**Backend:**
```bash
pip install -r requirements.txt
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
npm run build
npm start
```

---

## Monitoring

### Key Metrics to Track

1. Dashboard load time (should be < 2 seconds)
2. API response times
3. Database query performance
4. Error rates
5. User action completion rates

### Logging

Check logs for:
- Failed authentication attempts
- Database errors
- API errors
- Slow queries

---

## Support

If you encounter issues:

1. Check `OFFICE_DASHBOARD_IMPLEMENTATION.md` for detailed specs
2. Review backend logs
3. Check browser console
4. Verify database connections
5. Test with Postman/Thunder Client

---

**Setup Complete!** 🎉

Your Office Dashboard is now fully operational and PRD-compliant.
