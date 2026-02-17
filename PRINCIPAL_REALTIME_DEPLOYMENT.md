# Principal Dashboard Real-Time Implementation

## What This Fixes

✅ **Actions now persist to database** (no more "loads then disappears")
✅ **Real search** (by name/surname/grade, not just ID)
✅ **Real-time notifications** (teachers see principal requests)
✅ **KPIs from database views** (consistent, fast, accurate)
✅ **Proper tenant isolation** (RLS enforced everywhere)

## Deployment Steps

### 1. Deploy Database Schema

Run in Supabase SQL Editor:

```bash
# Copy contents of backend/database/principal_realtime_schema.sql
# Execute in Supabase SQL Editor
```

This creates:
- `risk_cases` table
- `marking_requests` table
- `notifications` table
- `kpi_targets` table
- `class_teachers` and `subject_teachers` helper tables
- Views: `v_student_performance`, `v_performance_bands`, `v_kpi_academics`, `v_finance_kpis_principal`, `v_arrears_list`, `v_reports_kpis_principal`
- Trigger: `notify_marking_request()` - auto-creates notifications
- Indexes for fast search
- RLS policies

### 2. Backend Already Configured

The new router is registered in `app/api/v1/__init__.py` ✅

### 3. API Endpoints Available

All endpoints write to DB first, then return created record:

#### Student Search (Real Search)
```
GET /api/v1/principal-realtime/students/search?q=john&grade_id=xxx
```

#### Risk Cases
```
POST   /api/v1/principal-realtime/risk-cases
GET    /api/v1/principal-realtime/risk-cases?status=open&severity=high
PATCH  /api/v1/principal-realtime/risk-cases/{id}
```

#### Marking Requests
```
POST   /api/v1/principal-realtime/marking-requests
GET    /api/v1/principal-realtime/marking-requests?status=open
```

#### Notifications
```
GET    /api/v1/principal-realtime/notifications?unread_only=true
PATCH  /api/v1/principal-realtime/notifications/{id}/read
```

#### KPI Targets
```
POST   /api/v1/principal-realtime/kpi-targets
GET    /api/v1/principal-realtime/kpi-targets/{year}
```

#### KPIs (From Views)
```
GET    /api/v1/principal-realtime/kpis/academics
GET    /api/v1/principal-realtime/kpis/finance
GET    /api/v1/principal-realtime/kpis/reports
```

#### Performance
```
GET    /api/v1/principal-realtime/performance/bands?grade_id=xxx&subject_id=xxx
GET    /api/v1/principal-realtime/performance/students?performance_band=low
```

#### Arrears
```
GET    /api/v1/principal-realtime/arrears
```

#### Staff (Teachers + Office Admin only)
```
GET    /api/v1/principal-realtime/staff?role=teacher
```

## Frontend Integration Pattern

### Rule: Write to DB first, update UI from returned record

**Before (Wrong):**
```typescript
// Just updates local state
setRiskCases([...riskCases, newCase]);
```

**After (Correct):**
```typescript
// 1. Write to DB
const response = await authFetch('/api/v1/principal-realtime/risk-cases', {
  method: 'POST',
  body: JSON.stringify(riskCaseData)
});

// 2. Get created record
const createdCase = await response.json();

// 3. Update UI from DB record
setRiskCases([...riskCases, createdCase]);

// 4. Show success
toast.success('Risk case created');
```

### Real-time Subscriptions (Supabase)

Subscribe to table changes:

```typescript
import { supabase } from '@/lib/supabase';

// Subscribe to risk cases
const subscription = supabase
  .channel('risk_cases_changes')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'risk_cases',
    filter: `school_id=eq.${schoolId}`
  }, (payload) => {
    // Refetch risk cases or update state
    fetchRiskCases();
  })
  .subscribe();

// Cleanup
return () => {
  subscription.unsubscribe();
};
```

### KPIs: Read from Views

```typescript
// Don't compute in frontend
const passRate = students.filter(s => s.avg >= 50).length / students.length;

// Do this instead
const kpis = await authFetch('/api/v1/principal-realtime/kpis/academics')
  .then(r => r.json());
const passRate = kpis.pass_rate_actual;
```

## Testing

### 1. Test Risk Case Creation

```bash
curl -X POST http://localhost:8000/api/v1/principal-realtime/risk-cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "xxx",
    "risk_type": "attendance",
    "severity": "high",
    "notes": "Chronic absenteeism"
  }'
```

Should return created record with ID.

### 2. Test Marking Request + Notification

```bash
curl -X POST http://localhost:8000/api/v1/principal-realtime/marking-requests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_scope": "grade",
    "grade_id": "xxx",
    "message": "Please complete marking by Friday"
  }'
```

Check notifications table - should have entries for affected teachers.

### 3. Test Student Search

```bash
curl "http://localhost:8000/api/v1/principal-realtime/students/search?q=john" \
  -H "Authorization: Bearer $TOKEN"
```

Should return students matching "john" in first_name, last_name, or admission_number.

### 4. Test KPIs

```bash
curl http://localhost:8000/api/v1/principal-realtime/kpis/academics \
  -H "Authorization: Bearer $TOKEN"
```

Should return pass_rate_actual, assessment_completion_actual from view.

## Data Flow

```
User Action (Frontend)
    ↓
API Call (POST/PATCH)
    ↓
Database Write (INSERT/UPDATE)
    ↓
Trigger Fires (if applicable)
    ↓
Notifications Created
    ↓
Return Created Record
    ↓
Update UI from Record
    ↓
Realtime Subscription Updates Other Users
```

## Performance

- **Indexes**: All queries use indexes (school_id, status, etc.)
- **Views**: Pre-computed aggregations, not calculated in frontend
- **Limits**: Queries limited to 50-100 records
- **Realtime**: Subscribe to base tables, refetch views on change

## Security

- **RLS**: All tables have row-level security
- **Tenant Isolation**: Every query filtered by school_id
- **Role-Based**: Policies enforce principal/teacher/admin access
- **No Cross-Tenant Leakage**: RLS prevents data leaks

## Troubleshooting

### Issue: "Failed to create risk case"

**Check:**
1. User has school_id in profile
2. RLS policy allows insert
3. All required fields provided
4. student_id exists and belongs to same school

### Issue: "Notifications not appearing"

**Check:**
1. Trigger is created and enabled
2. class_teachers/subject_teachers tables populated
3. Teachers have user_profiles with correct school_id
4. Frontend subscribed to notifications table

### Issue: "KPIs showing 0"

**Check:**
1. Views are created
2. Base tables have data (students, assessment_scores, invoices)
3. school_id matches in all tables
4. Status filters correct (e.g., students.status = 'active')

## Next Steps

1. **Deploy schema** - Run SQL in Supabase
2. **Test endpoints** - Use curl or Postman
3. **Update frontend** - Replace mock data with API calls
4. **Add subscriptions** - Wire up real-time updates
5. **Test notifications** - Verify teachers see requests

## Success Criteria

✅ Risk case button creates DB record and shows success toast
✅ Marking request creates notifications for teachers
✅ Student search finds by name, not just ID
✅ KPIs match database values, not frontend calculations
✅ Actions persist across page refreshes
✅ Real-time updates work for multiple users

---

**Remember**: If it doesn't write to the database, it's not a feature. It's an animation.
