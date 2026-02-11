# Role Isolation - Principal vs Office Admin

## Overview

The system now has **complete role isolation** between Principal and Office Admin with distinct dashboards, navigation, and responsibilities.

---

## 🎓 PRINCIPAL (School Executive)

### Purpose
Strategic oversight, approvals, performance monitoring, risk management

### Dashboard Focus
- **Performance Metrics**: Students, attendance rates, at-risk counts, fee collection
- **School Alerts**: Grade-level issues, at-risk students, collection problems
- **Approvals Required**: Fee discounts, mark changes, transfers, disciplinary cases
- **Academic Performance**: Pass rates, assessment completion, teacher submissions
- **Finance Overview**: Collection rates, outstanding balances, overdue amounts
- **Staff Insight**: Teacher counts, marking completion, late submissions
- **Recent Activity**: Important school-level events only

### Navigation Menu
1. Dashboard (executive overview)
2. Academics (performance tracking)
3. Attendance (overview, not data entry)
4. Finance (overview, not cashier work)
5. Staff (performance monitoring)
6. Students (view-heavy, limited edit)
7. Reports (strategic insights)
8. Approvals (review and approve)
9. Settings (policy-level)

### Backend API
**Prefix**: `/api/v1/principal/`

**Endpoints**:
- `GET /dashboard/metrics` - Key performance indicators
- `GET /alerts` - School-level alerts
- `GET /approvals` - Pending approval queue
- `GET /academic/performance` - Academic metrics
- `GET /finance/overview` - Financial summary
- `GET /staff/insight` - Staff performance
- `GET /activity/recent` - Important events

### What Principal CANNOT Do
❌ Take attendance (teacher task)
❌ Record payments (office admin task)
❌ Add students (office admin task)
❌ Enter grades (teacher task)
❌ Daily operational data entry

### What Principal CAN Do
✅ View all performance metrics
✅ Approve fee discounts
✅ Review mark changes
✅ Monitor at-risk students
✅ Approve transfers
✅ Review disciplinary cases
✅ Access strategic reports
✅ Set school policies

---

## 🏢 OFFICE ADMIN (Operations Manager)

### Purpose
Daily operations, student records, fee management, document compliance, task queues

### Dashboard Focus
- **Today's Priorities**: Work queues with action buttons
  - Admissions awaiting verification
  - Missing documents
  - Payments to allocate
  - Proof of payment uploads
  - Transfer requests
  - Letters requested
- **Fees & Payments Snapshot**: Operational metrics with action buttons
  - Collected this month
  - Outstanding balance
  - Overdue accounts
  - Payment plans
  - **Buttons**: View Arrears, Record Payment, Reconcile
- **Student Admin Snapshot**: Enrollment operations
  - Active students
  - New admissions
  - Pending transfers
  - Inactive students
  - **Buttons**: Add Student, View Pipeline
- **Documents & Compliance**: Missing document tracking
- **Exceptions & Flags**: Issues requiring resolution
- **Recent Activity**: Operational events only

### Navigation Menu
1. Dashboard (operations center)
2. Students (full CRUD access)
3. Admissions (process applications)
4. Attendance (data entry)
5. Fees & Billing (record payments, manage invoices)
6. Documents (manage compliance)
7. Reports (operational reports)
8. Settings (operational settings)

### Backend API
**Prefix**: `/api/v1/office-admin/`

**Endpoints**:
- `GET /dashboard/priorities` - Today's work queue
- `GET /fees/snapshot` - Fee operations metrics
- `GET /students/snapshot` - Student operations metrics
- `GET /documents/compliance` - Missing documents
- `GET /activity/recent` - Operational events
- `GET /exceptions` - Issues to resolve

### What Office Admin CANNOT Do
❌ Approve major policy decisions (principal task)
❌ View strategic performance trends (principal level)
❌ Approve disciplinary outcomes (principal task)
❌ Set school-wide policies (principal task)

### What Office Admin CAN Do
✅ Add/edit/delete students
✅ Record payments
✅ Take attendance
✅ Process admissions
✅ Manage documents
✅ Generate letters
✅ Reconcile payments
✅ Follow up on missing documents
✅ Process transfers
✅ Manage invoices

---

## Key Differences

| Aspect | Principal | Office Admin |
|--------|-----------|--------------|
| **Focus** | Strategic oversight | Daily operations |
| **Dashboard** | Performance metrics | Work queues |
| **Buttons** | "View Report", "Review", "Approve" | "Add", "Record", "Process", "Generate" |
| **Data Entry** | None | Extensive |
| **Approvals** | Reviews and approves | Submits for approval |
| **Reports** | Strategic insights | Operational lists |
| **Finance** | Collection rates, trends | Record payments, reconcile |
| **Students** | View performance, at-risk | Add, edit, manage records |
| **Attendance** | View rates, alerts | Take attendance, mark absences |

---

## Database Access

### Principal Queries
- **Read-only aggregations**: COUNT, SUM, AVG
- **Performance calculations**: Rates, percentages, trends
- **Risk identification**: Chronic absentees, at-risk students
- **No direct data entry**: All through approvals

### Office Admin Queries
- **Full CRUD operations**: INSERT, UPDATE, DELETE
- **Direct data entry**: Students, payments, attendance
- **Document management**: Upload, track, verify
- **Operational tasks**: Allocate, reconcile, process

---

## Frontend Components

### Principal
- **Component**: `AdminDashboard` (admin-dashboard.tsx)
- **Style**: Executive summary cards, trend indicators, approval tables
- **Colors**: Professional blues, greens for positive metrics
- **Actions**: "View", "Review", "Approve"

### Office Admin
- **Component**: `OfficeAdminDashboard` (office-admin-dashboard.tsx)
- **Style**: Task lists, work queues, action buttons
- **Colors**: Alert colors (red/amber/blue) for priority tasks
- **Actions**: "Add", "Record", "Process", "Verify", "Generate"

---

## Navigation Isolation

### System Admin
- Dashboard, Schools, Users, Security, Logs, Features, Settings

### Principal
- Dashboard, Academics, Attendance, Finance, Staff, Students, Reports, Approvals, Settings

### Office Admin
- Dashboard, Students, Admissions, Attendance, Fees & Billing, Documents, Reports, Settings

### Teacher
- Dashboard, Students, Attendance, Academics, Reports, Settings

### Parent
- Dashboard, Students, Fees, Reports, Settings

---

## Testing Role Isolation

### Test Principal Access
1. Login as principal
2. Verify dashboard shows performance metrics
3. Confirm NO "Add Student" or "Record Payment" buttons
4. Check Approvals page exists
5. Verify navigation menu matches principal scope

### Test Office Admin Access
1. Login as office_admin
2. Verify dashboard shows work queues
3. Confirm "Add Student" and "Record Payment" buttons exist
4. Check NO Approvals page in navigation
5. Verify operational focus throughout

---

## Summary

**Principal** = School executive who monitors, approves, and guides strategy
**Office Admin** = Operations manager who processes, records, and manages daily tasks

The dashboards, navigation, and capabilities are now completely isolated with no overlap in operational vs strategic responsibilities.
