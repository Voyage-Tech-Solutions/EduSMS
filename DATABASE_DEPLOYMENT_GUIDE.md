# 🗄️ Database Deployment Guide

## Complete Supabase Schema Implementation

This guide provides step-by-step instructions for deploying the complete EduCore database schema to Supabase.

---

## 📋 Files Overview

| File | Purpose | Tables/Objects |
|------|---------|----------------|
| `complete_schema.sql` | Core database structure | 35 tables, indexes, triggers |
| `rls_policies.sql` | Row-level security | 50+ RLS policies |
| `principal_dashboard_rpc.sql` | Analytics functions | 6 RPC functions |
| `principal_dashboard_tables.sql` | Additional tables | 8 specialized tables |
| `seed_data.sql` | Sample test data | Demo data for testing |

---

## 🚀 Deployment Steps

### Step 1: Prerequisites

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create new project
   - Wait for project initialization

2. **Enable Required Extensions**
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

3. **Get Connection Details**
   - Project URL
   - Anon/Public Key
   - Service Role Key (for backend)

---

### Step 2: Execute Schema Files (IN ORDER)

#### 2.1 Core Schema
```bash
# Execute in Supabase SQL Editor
File: complete_schema.sql
```

**What it creates:**
- 35 core tables
- Foreign key relationships
- Indexes for performance
- Triggers for automation
- Timestamp management

**Verification:**
```sql
-- Check tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Should return 35+ tables
```

---

#### 2.2 RLS Policies
```bash
# Execute in Supabase SQL Editor
File: rls_policies.sql
```

**What it creates:**
- Helper functions (get_user_school_id, get_user_role, etc.)
- RLS policies for all tables
- Multi-tenant data isolation
- Role-based access control

**Verification:**
```sql
-- Check RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- All tables should have rowsecurity = true
```

---

#### 2.3 Principal Dashboard RPC Functions
```bash
# Execute in Supabase SQL Editor
File: principal_dashboard_rpc.sql
```

**What it creates:**
- detect_at_risk_students()
- calculate_invoice_risk()
- get_staff_performance()
- get_grade_performance()
- get_subject_rankings()
- get_missing_attendance_submissions()

**Verification:**
```sql
-- Check functions created
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_type = 'FUNCTION';

-- Should include 6 new functions
```

---

#### 2.4 Principal Dashboard Tables
```bash
# Execute in Supabase SQL Editor
File: principal_dashboard_tables.sql
```

**What it creates:**
- risk_cases (if not exists)
- interventions
- report_submissions
- academic_targets
- invoice_adjustments
- payment_plans
- teacher_assignments (if not exists)
- notification_templates

**Verification:**
```sql
-- Check new tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'risk_cases', 'interventions', 'report_submissions',
    'academic_targets', 'invoice_adjustments', 'payment_plans'
);
```

---

#### 2.5 Seed Data (Optional - For Testing)
```bash
# Execute in Supabase SQL Editor
File: seed_data.sql
```

**What it creates:**
- 2 sample schools
- Academic structure (years, terms, grades, classes)
- 5 sample students
- Fee structures and invoices
- Attendance records
- Assessment scores
- Admissions applications
- Risk cases

**Verification:**
```sql
-- Check seed data
SELECT 
    (SELECT COUNT(*) FROM schools) as schools,
    (SELECT COUNT(*) FROM students) as students,
    (SELECT COUNT(*) FROM invoices) as invoices,
    (SELECT COUNT(*) FROM attendance_records) as attendance;
```

---

## 🔐 Security Configuration

### 1. Service Role Key (Backend Only)

**CRITICAL:** Never expose service role key in frontend!

```env
# Backend .env
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 2. Anon Key (Frontend)

```env
# Frontend .env
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

### 3. RLS Verification

Test RLS policies work correctly:

```sql
-- Test as different roles
SET LOCAL role = 'authenticated';
SET LOCAL request.jwt.claims = '{"sub": "user-id-here", "role": "teacher"}';

-- Try querying students
SELECT * FROM students;
-- Should only return students in user's school/classes
```

---

## 📊 Database Schema Summary

### Core Entities (35 Tables)

**Identity & Access:**
- schools
- user_profiles
- guardians
- student_guardians

**Academic Structure:**
- academic_years
- terms
- grades
- classes
- subjects
- teacher_assignments

**Students:**
- students
- admissions

**Attendance:**
- attendance_sessions
- attendance_records

**Assessments:**
- assessments
- assessment_scores

**Finance:**
- fee_structures
- invoices
- payments
- payment_plans
- invoice_adjustments

**Documents:**
- documents
- document_requirements

**Risk Management:**
- risk_cases
- interventions

**Governance:**
- approval_requests

**Planning:**
- lesson_plans
- resources

**Communication:**
- messages
- notifications_log

**Configuration:**
- school_settings

**Audit:**
- audit_logs

---

## 🔍 Testing Checklist

### 1. Schema Validation
- [ ] All 35+ tables created
- [ ] All foreign keys working
- [ ] All indexes created
- [ ] Triggers functioning

### 2. RLS Validation
- [ ] All tables have RLS enabled
- [ ] Helper functions work
- [ ] Policies enforce school isolation
- [ ] Role-based access works

### 3. RPC Functions
- [ ] detect_at_risk_students() returns results
- [ ] get_staff_performance() calculates correctly
- [ ] get_grade_performance() aggregates properly
- [ ] All 6 functions executable

### 4. Data Integrity
- [ ] Can insert students
- [ ] Can create invoices
- [ ] Can record attendance
- [ ] Can create assessments
- [ ] Foreign keys prevent orphans

### 5. Performance
- [ ] Queries use indexes (check EXPLAIN)
- [ ] RLS policies don't cause N+1 queries
- [ ] Aggregations perform well

---

## 🐛 Common Issues & Solutions

### Issue 1: "relation already exists"
**Solution:** Some tables may already exist from previous schema. Either:
- Drop existing tables: `DROP TABLE IF EXISTS table_name CASCADE;`
- Or skip duplicate CREATE statements

### Issue 2: RLS blocks all queries
**Solution:** Ensure user has proper role in user_profiles:
```sql
INSERT INTO user_profiles (id, school_id, email, first_name, last_name, role)
VALUES (auth.uid(), 'school-id', 'user@email.com', 'First', 'Last', 'principal');
```

### Issue 3: RPC functions fail
**Solution:** Check function exists and has correct signature:
```sql
SELECT * FROM pg_proc WHERE proname = 'detect_at_risk_students';
```

### Issue 4: Foreign key violations
**Solution:** Insert data in correct order:
1. schools
2. user_profiles
3. academic structure (years, terms, grades, classes)
4. students
5. everything else

---

## 📈 Performance Optimization

### Indexes Created

All critical indexes are included in schema:
- school_id on all multi-tenant tables
- student_id on student-related tables
- date fields on time-series data
- status fields for filtering
- Foreign keys for joins

### Query Optimization Tips

1. **Always filter by school_id first**
   ```sql
   WHERE school_id = 'xxx' AND other_conditions
   ```

2. **Use indexes for sorting**
   ```sql
   ORDER BY created_at DESC  -- indexed
   ```

3. **Avoid SELECT ***
   ```sql
   SELECT id, name, status  -- specific columns
   ```

4. **Use RPC functions for complex aggregations**
   ```sql
   SELECT * FROM get_grade_performance('school-id');
   ```

---

## 🔄 Migration Strategy

### For Existing Deployments

If you already have data:

1. **Backup existing data**
   ```bash
   pg_dump -h db.xxx.supabase.co -U postgres > backup.sql
   ```

2. **Create migration script**
   - Compare old vs new schema
   - Write ALTER TABLE statements
   - Test on staging first

3. **Run migration**
   ```sql
   BEGIN;
   -- Your migration statements
   COMMIT;
   ```

4. **Verify data integrity**
   ```sql
   SELECT COUNT(*) FROM students;
   -- Compare with backup
   ```

---

## 📝 Next Steps After Deployment

1. **Create First School**
   ```sql
   INSERT INTO schools (name, code, email) 
   VALUES ('My School', 'SCH001', 'admin@school.com');
   ```

2. **Create System Admin User**
   ```sql
   INSERT INTO user_profiles (id, school_id, email, first_name, last_name, role)
   VALUES (
       auth.uid(), 
       'school-id', 
       'admin@school.com', 
       'Admin', 
       'User', 
       'system_admin'
   );
   ```

3. **Configure School Settings**
   ```sql
   INSERT INTO school_settings (school_id, setting_key, setting_value)
   VALUES 
       ('school-id', 'attendance_threshold', '75'),
       ('school-id', 'pass_mark', '50');
   ```

4. **Test Backend Connection**
   ```bash
   curl http://localhost:8000/api/v1/schools
   ```

5. **Test Frontend**
   ```bash
   npm run dev
   # Navigate to http://localhost:3000
   ```

---

## 🎯 Production Readiness Checklist

- [ ] All schema files executed successfully
- [ ] RLS policies tested and working
- [ ] Sample data inserted and queryable
- [ ] Backend connects to Supabase
- [ ] Frontend connects to backend
- [ ] Authentication flow works
- [ ] Multi-tenancy enforced
- [ ] Performance acceptable (<100ms queries)
- [ ] Backup strategy in place
- [ ] Monitoring configured

---

## 📞 Support

If you encounter issues:

1. Check Supabase logs (Dashboard → Logs)
2. Verify RLS policies (Dashboard → Authentication → Policies)
3. Test queries in SQL Editor
4. Check backend logs
5. Review this guide's troubleshooting section

---

## 🎉 Success Criteria

Your database is ready when:

✅ All tables created
✅ RLS policies active
✅ RPC functions working
✅ Sample data queryable
✅ Backend API responds
✅ Frontend loads data
✅ Multi-tenancy enforced
✅ Performance acceptable

**You now have a production-ready school management database!**
