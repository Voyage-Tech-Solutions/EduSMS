# 🧭 OFFICE ADMIN CONTROL PANEL — COMPLETE BLUEPRINT

## Overview
The Office Admin role is the **operational nervous system** of the school. While teachers generate data and principals make decisions, office admin makes the entire machine run without collapsing.

---

## ✅ IMPLEMENTATION STATUS: 100%

### Pages (8/8)
1. ✅ **Dashboard** - Operations overview with daily priorities
2. ✅ **Students** - Student directory and lifecycle management
3. ✅ **Admissions** - Application processing and enrollment
4. ✅ **Attendance** - Record, edit, and correct attendance
5. ✅ **Fees & Billing** - Invoice creation and payment processing
6. ✅ **Documents** - Verification queue and compliance tracking
7. ✅ **Reports** - Operational reports and exports
8. ✅ **Settings** - Limited admin configuration

### Backend API (25+ Endpoints)
- ✅ Dashboard priorities and snapshots
- ✅ Student CRUD operations
- ✅ Admission processing
- ✅ Fee management
- ✅ Payment recording
- ✅ Attendance operations
- ✅ Document verification
- ✅ Report generation

---

## 🎯 WHAT THIS ROLE DOES

### Core Responsibilities
- **Student Records**: Admission → Exit lifecycle
- **Document Verification**: Compliance tracking
- **Attendance Administration**: Recording and corrections
- **Invoice Creation**: Fee billing execution
- **Payment Processing**: Recording and allocation
- **Transfers**: Student movement management
- **Letters & Certificates**: Document generation
- **Compliance Tracking**: Regulatory requirements
- **Communication Coordination**: School-wide messaging
- **Daily Workload Processing**: Task-driven operations

---

## 🧱 GLOBAL LAYOUT

### Top Bar (Persistent)
**Left:**
- School name
- Page title

**Center:**
- Smart operational search (students, invoices, applications, documents)

**Right:**
- 🔔 Notifications bell
- 🔴 Pending tasks badge
- 👤 User profile menu
- 🚪 Sign out

### Daily Work Queue Panel
Accessible from bell icon or side panel.

**Shows:**
- Document verification pending
- Payments to allocate
- Transfer requests
- Letters requested
- Admission reviews
- Compliance issues

This is the admin's **to-do list**.

---

## 📚 SIDEBAR NAVIGATION

Structured by workflow order, not hierarchy:

```
🏠 Dashboard                    /dashboard/office-admin
👨🎓 Students                     /dashboard/office-admin/students
📝 Admissions                   /dashboard/office-admin/admissions
📅 Attendance                   /dashboard/office-admin/attendance
💰 Fees & Billing               /dashboard/office-admin/fees
📂 Documents                    /dashboard/office-admin/documents
📊 Reports                      /dashboard/office-admin/reports
⚙️ Settings                     /dashboard/office-admin/settings
```

---

## 🏠 PAGE 1: OPERATIONS DASHBOARD

### Purpose
Show workload and immediate tasks (not analytics).

### Section 1: Today's Priorities (Primary Area)
Task table with counts and actions:

| Task Type | Count | Action |
|-----------|-------|--------|
| Admissions awaiting verification | 5 | Review |
| Students with missing documents | 12 | Follow Up |
| Fee payments to allocate | 8 | Process |
| Proof of payment uploads | 3 | Verify |
| Transfer requests pending | 2 | Review |
| Letters requested | 4 | Generate |

Each row opens the relevant processing page.

### Section 2: Fees Snapshot
Quick finance operational view:
- Collected this month: $45,000
- Outstanding balance: $12,500
- Overdue payments: $3,200
- Payment plans active: 15

**Buttons:**
- Save Attendance
- Create Invoice

### Section 3: Student Admin Snapshot
Counts:
- Total active students: 450
- New admissions this month: 12
- Pending transfers: 3
- Inactive students: 8

**Buttons:**
- Add Student
- Add Staff

### Section 4: Documents & Compliance
Counts with color coding:
- Missing birth certificates: 8 (red)
- Missing parent IDs: 5 (amber)
- Medical forms outstanding: 12 (blue)

**Button:** Send Bulk Reminder

### Section 5: Quick Reports
Shortcuts:
- Student Directory Export
- Fee Statement
- Attendance Summary
- Grade Report

---

## 👨🎓 PAGE 2: STUDENTS MODULE

### Student Directory
Searchable table with filters.

**Columns:**
- Admission #
- Name
- Grade/Class
- Status
- Documents Status
- Fee Status
- Actions

**Filters:**
- Search (name/admission #)
- Grade
- Status (active/inactive/transferred)
- Document status
- Fee status

**Actions per student:**
- View profile
- Edit record
- Change status
- Generate letter
- View financial account

### Student Profile (Detailed View)
Tabs:
1. **Personal Info** - Demographics, contact
2. **Academic Info** - Grade, class, performance
3. **Attendance History** - Full attendance record
4. **Financial Account** - Invoices, payments, balance
5. **Documents** - All uploaded files
6. **Notes/History** - Audit trail

### Add Student
Form fields:
- Personal info (name, DOB, gender)
- Guardian info (name, contact, relationship)
- Grade/Class assignment
- Enrollment date
- Document upload
- Initial fee structure

**On save:** Creates enrollment record + generates admission number

### Transfers
Handles:
- **Incoming** - From other schools
- **Outgoing** - To other schools
- **Internal** - Grade/class changes

**Requires:** Approval (depending on policy)

**Workflow:**
1. Request submitted
2. Documents verified
3. Approval obtained
4. Records transferred
5. Status updated

### Status Changes
Lifecycle control:
- Active → Inactive
- Active → Transferred
- Active → Graduated
- Active → Suspended

**Must log:** Reason, effective date, approver

### Letters & Certificates
Generate auto-filled templates:
- Enrollment confirmation
- Transfer letter
- Fee clearance certificate
- Attendance record
- Character reference
- Completion certificate

---

## 📝 PAGE 3: ADMISSIONS MODULE

### Purpose
Handle pre-enrollment pipeline.

### Applications List
**Stages:**
- Incomplete (missing info/docs)
- Pending Review (awaiting verification)
- Approved (ready for enrollment)
- Enrolled (converted to student)
- Rejected (declined with reason)

**Table:**
| Application # | Name | Grade | Status | Submitted | Actions |

### Application Detail
Shows:
- Applicant information
- Submitted documents (checklist)
- Notes and comments
- Decision history
- Communication log

**Actions:**
- Approve
- Reject
- Request documents
- Schedule interview
- Convert to student

### Document Verification
Checklist per applicant:
- Birth certificate ✓
- Parent ID ✗
- Previous school report ✓
- Medical form ⏳

**Mark as:**
- Verified (green check)
- Invalid (red X)
- Missing (orange warning)

### Enrollment Processing
Convert approved application → student record:
1. Verify all documents complete
2. Assign admission number
3. Assign grade/class
4. Create student record
5. Generate initial invoice
6. Send welcome letter
7. Update application status

---

## 📅 PAGE 4: ATTENDANCE MODULE

### Purpose
Office admin supervises records and corrections.

### Record Attendance (Manual Override)
Same interface as teacher but admin-level:
- Select class
- Select date
- Mark each student (Present/Absent/Late/Excused)
- Add notes
- Submit

**Use case:** When teacher forgot or system error

### Edit Attendance
Allows correction of errors:
- Find record (by student/date/class)
- Change status
- Add correction reason
- Log who made change
- Submit

**Requires:** Reason log for audit trail

### Attendance Corrections Queue
Pending changes awaiting review:
- Original status
- Requested status
- Reason
- Requested by
- Date
- Actions (Approve/Reject)

### Attendance Reports
Generate:
- Daily summary (all classes)
- Grade report (by grade)
- Absentee list (chronic cases)
- Class attendance (specific class)
- Student attendance (individual)

**Export formats:** PDF, Excel, CSV

---

## 💰 PAGE 5: FEES & BILLING MODULE

### Purpose
Money administration and tracking.

### Invoices
**Create Invoice:**
- Select student
- Description (Tuition/Transport/Books/etc)
- Amount
- Due date
- Term (optional)
- Generate

**Invoice List:**
| Invoice # | Student | Description | Amount | Paid | Balance | Status | Actions |

**Actions:**
- View details
- Edit (if unpaid)
- Cancel (with reason)
- Send reminder
- Download PDF

### Payments
**Record Payment:**
- Select invoice (or student)
- Amount
- Payment method (Cash/Bank/Mobile/Card)
- Reference number
- Receipt upload (optional)
- Payment date
- Submit

**Auto-allocation:** System matches payment to invoices

### Payment Allocation
Match payments to invoices:
- Unallocated payments list
- Select payment
- Select invoice(s)
- Allocate amount
- Handle partial payments
- Confirm

### Refunds
Process refund requests:
- Student name
- Original invoice
- Refund amount
- Reason
- Approval (if required)
- Payment method
- Process

### Financial Adjustments
Manual corrections:
- **Discounts** - Reduce invoice amount
- **Penalties** - Add late fees
- **Write-offs** - Cancel debt (requires approval)
- **Corrections** - Fix errors

**All require:** Reason + approval log

---

## 📂 PAGE 6: DOCUMENTS & COMPLIANCE

### Purpose
Central regulatory tracking.

### Student Documents
All uploaded files organized by:
- Student
- Document type
- Status
- Upload date
- Expiry date (if applicable)

**Document types:**
- Birth certificate
- Parent ID
- Medical form
- Previous school report
- Immunization record
- Proof of residence
- Passport photo

### Verification Queue
Documents awaiting review:
| Student | Document Type | Uploaded | Status | Actions |

**Actions:**
- View document
- Verify (approve)
- Reject (with reason)
- Request reupload

### Missing Documents
Students lacking required files:
| Student | Grade | Missing Documents | Days Overdue | Actions |

**Actions:**
- Send reminder (email/SMS)
- Call parent
- Flag for follow-up
- Escalate to principal

### Expiry Tracking
Medical forms, permits, etc. with expiry dates:
| Student | Document | Expiry Date | Days Until Expiry | Actions |

**Alert before expiry:** 30 days, 14 days, 7 days

**Actions:**
- Send renewal reminder
- Request new document
- Mark as renewed

---

## 📊 PAGE 7: REPORTS MODULE

### Purpose
Operational reporting (not leadership analytics).

### Report Categories

**1. Student Reports:**
- Student directory (full list)
- New admissions (by period)
- Transfers (in/out)
- Status changes
- Document compliance

**2. Financial Reports:**
- Payment records (by period)
- Outstanding balances
- Overdue accounts
- Collection summary
- Payment method breakdown

**3. Attendance Reports:**
- Daily attendance logs
- Class attendance summary
- Chronic absentees
- Attendance corrections
- Teacher submission compliance

**4. Admission Reports:**
- Applications summary
- Conversion rate
- Pending applications
- Rejection reasons

**5. Document Reports:**
- Compliance status
- Missing documents
- Verification queue
- Expiry tracking

### Export Center
All reports exportable in:
- PDF (formatted)
- Excel (data)
- CSV (raw data)

**Scheduled reports:** Set up recurring exports

---

## ⚙️ PAGE 8: SETTINGS (LIMITED)

### Purpose
Office admin cannot change strategic settings.

### Allowed Settings

**1. Document Types:**
- Add/edit document types
- Set required/optional
- Set expiry rules

**2. Letter Templates:**
- Edit letter templates
- Add merge fields
- Preview templates

**3. Invoice Numbering:**
- Set numbering format
- Set starting number
- Set prefix/suffix

**4. Class Lists:**
- Assign students to classes
- Update class capacity
- Manage class teachers

### Not Allowed
❌ Academic targets
❌ Approval rules
❌ Staff performance settings
❌ Governance policies
❌ Financial write-off limits

---

## 🔄 CORE WORKFLOW

### Student Lifecycle
```
Application → Verification → Enrollment →
Attendance Tracking → Fee Billing →
Document Compliance → Status Updates →
Reporting → Archive
```

Office admin touches **every stage**.

### Daily Workflow
1. Check priority tasks
2. Process admissions
3. Verify documents
4. Record/correct attendance
5. Create invoices
6. Record payments
7. Handle queries
8. Generate reports
9. Update records

---

## 🔐 PERMISSIONS

### Office Admin CAN:
✅ Edit student records
✅ Create invoices
✅ Verify documents
✅ Correct attendance
✅ Generate reports
✅ Process admissions
✅ Record payments
✅ Manage transfers
✅ Generate letters
✅ Update compliance status

### Office Admin CANNOT:
❌ Approve write-offs (principal only)
❌ Change academic targets
❌ Manage staff performance
❌ Modify governance rules
❌ Access salary information
❌ Delete audit logs
❌ Override RLS policies

---

## 🧠 WHAT MAKES A GREAT OFFICE ADMIN SYSTEM

### Must Be:
✅ **Fast data entry** - Bulk operations supported
✅ **Bulk processing capable** - Handle 100+ students quickly
✅ **Error correction friendly** - Easy to fix mistakes
✅ **Audit logged** - Every action tracked
✅ **Document centered** - File management built-in
✅ **Task driven** - Priority-based workflow

### Performance Requirements:
- Form submission: < 1 second
- Bulk operations: < 5 seconds for 100 records
- Report generation: < 10 seconds
- Document upload: < 3 seconds
- Search results: < 500ms

---

## 🎯 SUCCESS CRITERIA

### Office Admin Should Answer Instantly:
✅ Who needs processing today?
✅ What records are incomplete?
✅ Which payments need handling?
✅ Which students need documents?
✅ What requests are waiting?

**Without clicking 10 pages.**

---

## 📊 KEY METRICS

### Daily Metrics:
- Tasks completed
- Documents verified
- Payments processed
- Invoices created
- Attendance records saved

### Weekly Metrics:
- Admissions processed
- Compliance rate
- Payment collection rate
- Document verification rate
- Error correction count

### Monthly Metrics:
- New enrollments
- Transfers processed
- Reports generated
- System uptime
- User satisfaction

---

## 🚀 BACKEND API ENDPOINTS

### Dashboard
- `GET /office-admin/dashboard/priorities` - Today's tasks
- `GET /office-admin/fees/snapshot` - Finance overview
- `GET /office-admin/students/snapshot` - Student stats
- `GET /office-admin/documents/compliance` - Compliance status
- `GET /office-admin/activity/recent` - Recent activity
- `GET /office-admin/exceptions` - System flags

### Students
- `POST /office-admin/students` - Add student
- `PATCH /office-admin/students/{id}/status` - Change status
- `GET /office-admin/students` - List students
- `GET /office-admin/students/{id}` - Student details

### Admissions
- `GET /office-admin/admissions` - List applications
- `POST /office-admin/admissions/{id}/verify` - Verify application
- `POST /office-admin/admissions/{id}/enroll` - Convert to student

### Fees
- `POST /office-admin/fees/invoices` - Create invoice
- `POST /office-admin/fees/payments` - Record payment
- `GET /office-admin/fees/invoices` - List invoices
- `GET /office-admin/fees/payments` - List payments

### Attendance
- `POST /office-admin/attendance/record` - Record attendance
- `PATCH /office-admin/attendance/{id}` - Edit attendance
- `GET /office-admin/attendance/corrections` - Correction queue

### Documents
- `GET /office-admin/documents/verification-queue` - Pending docs
- `POST /office-admin/documents/verify` - Verify document
- `GET /office-admin/documents/missing` - Missing docs

### Reports
- `GET /office-admin/reports/student-directory` - Student list
- `GET /office-admin/reports/fee-statement` - Fee report
- `GET /office-admin/reports/attendance-summary` - Attendance report

---

## 🎨 UI/UX PRINCIPLES

### Design Philosophy:
1. **Task-First** - Show what needs doing
2. **Quick Actions** - One-click common tasks
3. **Bulk Operations** - Process many at once
4. **Error Prevention** - Validate before submit
5. **Audit Trail** - Log everything
6. **Mobile Friendly** - Works on tablets

### Color Coding:
- 🔴 Urgent/Overdue (red)
- 🟠 Pending/Warning (orange)
- 🟢 Complete/Good (green)
- 🔵 Info/Neutral (blue)
- ⚫ Inactive (gray)

---

## 📝 IMPLEMENTATION CHECKLIST

### Phase 1: Core (✅ Complete)
- [x] Dashboard with priorities
- [x] Student management
- [x] Admission processing
- [x] Fee management
- [x] Attendance operations
- [x] Document verification
- [x] Report generation
- [x] Backend API

### Phase 2: Enhancements (Optional)
- [ ] Bulk operations UI
- [ ] Advanced search
- [ ] Document OCR
- [ ] SMS notifications
- [ ] Email templates
- [ ] Workflow automation

### Phase 3: Advanced (Future)
- [ ] AI document verification
- [ ] Predictive analytics
- [ ] Chatbot support
- [ ] Mobile app
- [ ] Voice commands

---

**Status:** Production Ready
**PRD Compliance:** 100%
**Last Updated:** 2024
**Version:** 1.0.0
