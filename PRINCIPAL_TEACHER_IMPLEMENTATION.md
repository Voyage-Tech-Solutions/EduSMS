# Principal & Teacher Implementation Guide

## Database Schema Additions Required

### 1. Approval System
```sql
approval_requests (
  id, type, entity_id, entity_type, requested_by, submitted_at,
  priority, status, decision, decided_by, decided_at, notes
)
```

### 2. Teacher Planning
```sql
lesson_plans (
  id, teacher_id, class_id, subject_id, term_id, date, time_slot,
  topic, objectives, activities, homework, status, notes
)

assessment_plans (
  id, teacher_id, class_id, subject_id, term_id, title, type,
  planned_date, total_marks, status, linked_assessment_id
)

resources (
  id, uploaded_by, class_id, subject_id, title, type, url, tags, visibility
)

curriculum_units (
  id, subject_id, grade_id, unit_name, order_index
)

coverage_tracking (
  id, unit_id, class_id, term_id, planned_date, completed_date, status
)
```

### 3. Gradebook Enhancements
```sql
gradebook_locks (
  id, class_id, subject_id, term_id, locked_by, locked_at,
  unlock_requested, unlock_approved_by
)
```

---

## PRINCIPAL PAGES

### 1. Principal - Students (Oversight Mode)

**Route:** `/dashboard/principal/students`

**Summary Cards:**
- Total Students
- Active
- Inactive
- Transferred
- Students At Risk
- Chronic Absentees
- Academic Below Pass

**Filters:**
- Search (name/admission #)
- Grade dropdown
- Status dropdown
- Risk level (low/medium/high)
- Attendance below X%
- Academic below pass%
- Overdue fees toggle

**Table Columns:**
| Admission # | Name | Grade | Class | Gender | Status | Attendance % | Academic Avg | Outstanding | Risk | Actions |

**Actions per Student:**
1. **View Profile** - Full student detail with trends
2. **Flag for Intervention** - Create risk_case + intervention
3. **Send Parent Notification** - Template-based messaging
4. **Change Status** - Mark inactive/transfer/reinstate
5. **Export Student Report** - PDF summary

**Backend Endpoints:**
```
GET  /principal/students?filters=
GET  /principal/student/{id}
POST /principal/students/risk
POST /principal/students/notify
PATCH /principal/students/status
GET  /principal/students/export
```

---

### 2. Principal - Reports & Analytics (Executive View)

**Route:** `/dashboard/principal/reports`

**Top Controls:**
- Date Range (This Month / Term / Custom)
- Export All

**Summary Metrics:**
- Total Enrollment
- Avg Attendance
- Fee Collection ($)
- Collection Rate (%)
- Academic Avg

**Quick Reports:**
1. **Student Directory** - Filters: grade, status, risk indicators
2. **Fee Statement** - By grade, overdue only, by term
3. **Attendance Summary** - School-wide, grade-level, below threshold
4. **Grade Report** - By term, subject, grade

**Executive Charts:**
- Enrollment trend (line)
- Attendance trend (line)
- Collection vs target (bar)
- Academic performance distribution (histogram)

**Backend Endpoints:**
```
GET  /principal/reports/summary
POST /principal/reports/generate
GET  /principal/reports/export
```

---

### 3. Principal - Approvals Required (Control Center)

**Route:** `/dashboard/principal/approvals`

**Summary Cards:**
- Total Pending
- High Priority
- Categories Clear (green when zero)

**Approval Types:**
1. **Admissions Approval** - Approve/Reject/Request Info
2. **Transfer Approval** - Approve outgoing/incoming
3. **Financial Write-Off** - Amount, reason, approve/reject
4. **Payment Plan Approval** - View terms, approve/modify/reject
5. **Staff Role Change** - Old/new role, effective date
6. **Policy Override** - Attendance/grade/fee waivers

**Table Columns:**
| Request ID | Type | Student/Staff | Description | Priority | Submitted By | Date | Status | Actions |

**Actions:**
- View Details
- Approve
- Reject
- Escalate
- Add Comment

**Approval Modal Fields:**
- Decision (approve/reject)
- Notes (required if reject)
- Notify requester toggle
- Notify affected user toggle

**Priority Logic:**
- High if: overdue > 7 days, amount > threshold, risk severity = high

**Backend Endpoints:**
```
GET  /principal/approvals?status=pending
GET  /principal/approvals/{id}
POST /principal/approvals/{id}/decision
GET  /principal/approvals/stats
```

---

## TEACHER PAGES

### 4. Teacher Dashboard (Enhanced Control Center)

**Route:** `/dashboard/teacher`

**A) Next Class Card:**
- Subject, class, time, room, student count
- Attendance last session
- Pending tasks
- Buttons: Take Attendance, Open Class, Start Lesson Timer

**B) Grading Tasks Card:**
- Ungraded submissions count
- Overdue grading tasks
- Average grading delay (days)
- Buttons: Open Gradebook, Grade Now, Bulk Grade

**C) Alerts/Flags:**
- Students absent 3+ consecutive days
- Missing assignments
- At-risk students in classes
- Incomplete attendance submissions

**Quick Actions:**
- Take Attendance
- Open Gradebook
- Add Assignment
- Send Class Message
- Upload Learning Material
- View At-Risk Students

**Today's Schedule Table:**
| Time | Subject | Class | Room | Status | Attendance | Lesson Plan | Actions |

**My Classes Snapshot:**
| Class | Students | Attendance Avg | Class Avg | Coverage | At Risk | Last Lesson |

**Backend Endpoints:**
```
GET /teacher/dashboard/summary
GET /teacher/schedule/today
GET /teacher/classes/snapshot
GET /teacher/alerts
```

---

### 5. Teacher - My Classes (Full Teaching Workspace)

**Route:** `/dashboard/teacher/classes`

**Section A: Today's Timetable**
- Full day view with filters
- Day selector, week view toggle

**Section B: My Subjects**
- Class cards with: subject, grade, student count, attendance avg, class avg, at-risk count, next lesson
- Buttons: Open Class, Gradebook, Attendance History, Assign Homework, Message Students

**Class Detail Page Tabs:**

**Tab 1: Students**
| Name | Attendance % | Avg Score | Missing Work | Risk | Actions |

**Tab 2: Gradebook**
- Spreadsheet interface
- Buttons: Add Assessment, Import Marks, Bulk Grade, Lock Grades

**Tab 3: Attendance**
- Calendar view with trends

**Tab 4: Assignments**
- List with submissions, graded %, avg score
- Buttons: Create Assignment, Extend Deadline, Download Submissions

**Tab 5: Materials**
- Upload PDFs, videos, slides, links

**Tab 6: Analytics**
- Grade distribution, attendance trend, performance charts

**Backend Endpoints:**
```
GET /teacher/class/{id}
GET /teacher/class/{id}/students
GET /teacher/class/{id}/grades
GET /teacher/class/{id}/attendance
GET /teacher/class/{id}/assignments
```

---

### 6. Teacher - Attendance (Enhanced)

**Route:** `/dashboard/teacher/attendance`

**Top Controls:**
- Select Class
- Date picker
- Mark All Present
- **Load Previous Pattern** (NEW)
- Save Attendance

**Intelligent Features:**
- Load previous pattern (auto-fill based on trends)
- Smart flags (highlight chronic absentees, late frequently)
- Quick status keys (P/A/L/E keyboard shortcuts)
- Inline notes per student

**Table Columns:**
| # | Admission # | Student | Last 7 Days | Status | Notes | Risk |

**Bulk Tools:**
- Select students → bulk set status

**Backend Endpoints:**
```
GET  /teacher/attendance/class/{id}?date=
POST /teacher/attendance/save
GET  /teacher/attendance/history/{class_id}
GET  /teacher/attendance/pattern/{class_id}
```

---

### 7. Teacher - Gradebook

**Route:** `/dashboard/teacher/gradebook`

**Top Controls:**
- Term selector
- Class selector ✅
- Subject selector ✅
- Assessment type filter
- Search student

**Buttons:**
- Add Assessment
- Import Marks
- Export
- Lock Gradebook
- Publish Results

**Tab A: Spreadsheet View**
| Admission # | Name | Attendance % | [Assessments...] | Total | Average % | Rank | Status |

Features:
- Inline editing
- Keyboard navigation
- Bulk fill
- Copy/paste from Excel
- Autosave

**Tab B: Assessments List**
| Title | Type | Date | Total Marks | Entries | Missing | Class Avg | Status | Actions |

**Tab C: Analytics**
- Score distribution histogram
- Pass rate
- Top/bottom performers
- Missing marks breakdown

**Add Assessment Modal:**
- Title, Type, Subject, Class, Term
- Date assigned, Due date
- Total marks, Pass mark %, Weighting %
- Allow late entries toggle
- Notes

**Import Marks Modal:**
1. Choose Assessment
2. Download CSV template
3. Upload CSV
4. Preview mapping + errors
5. Confirm import

**Lock Gradebook Modal:**
- Confirm lock
- Reason
- "Require principal approval to unlock" toggle

**Backend Endpoints:**
```
GET   /teacher/gradebook?class_id=&subject_id=&term_id=
POST  /teacher/gradebook/assessments
PATCH /teacher/gradebook/assessments/{id}
POST  /teacher/gradebook/assessments/{id}/import
POST  /teacher/gradebook/lock
POST  /teacher/gradebook/unlock-request
GET   /teacher/gradebook/export
```

---

### 8. Teacher - Planning

**Route:** `/dashboard/teacher/planning`

**Top Controls:**
- Term selector
- Week selector
- Class selector
- Subject selector

**Buttons:**
- Add Lesson Plan
- Add Assessment Plan
- Upload Resource
- Export Weekly Plan
- Copy Previous Week

**Tab A: Weekly Planner**
Grid: Days × Time slots
Each cell: topic, objectives, homework, resources, status
Actions: Edit, Mark Delivered, Attach Resource, Add Homework

**Tab B: Curriculum Coverage**
| Unit/Topic | Planned Date | Delivered Date | Coverage % | Notes |
Buttons: Add unit, Mark completed, Shift schedule

**Tab C: Resources Library**
- PDFs, links, videos, worksheets
- Tags: topic, week, assessment-related

**Tab D: Assessment Planner**
| Title | Type | Planned Date | Class | Status | Actions |
Actions: Convert to actual assessment, Edit, Cancel

**Add Lesson Plan Modal:**
- Date, Time slot, Class, Subject
- Topic title, Learning objectives
- Activities/steps, Homework
- Resources, Notes
- Status: planned/delivered/missed

**Copy Previous Week Modal:**
- Copy from week
- Copy resources toggle
- Copy homework toggle
- Shift dates automatically toggle

**Add Assessment Plan Modal:**
- Title, Type, Planned date
- Total marks, Syllabus link/topic
- Notes
- Button: Save Plan, Convert to Assessment

**Upload Resource Modal:**
- File/link, Title, Tags, Topic
- Visibility: private/shared with grade team

**Backend Endpoints:**
```
GET  /teacher/planning?week=&class_id=&subject_id=&term_id=
POST /teacher/planning/lessons
PATCH /teacher/planning/lessons/{id}
POST /teacher/planning/copy-week
POST /teacher/planning/assessments
POST /teacher/planning/assessments/{id}/convert
POST /teacher/resources
GET  /teacher/planning/export
```

---

## Implementation Estimates

### Database Schema (2-3 days)
- approval_requests table
- lesson_plans, assessment_plans, resources tables
- curriculum_units, coverage_tracking tables
- gradebook_locks table

### Backend APIs (15-18 days)
- Principal Students: 3 days
- Principal Reports: 2 days
- Principal Approvals: 3 days
- Teacher Dashboard: 2 days
- Teacher Classes: 3 days
- Teacher Gradebook: 4 days
- Teacher Planning: 3 days

### Frontend Pages (20-25 days)
- Principal Students: 4 days
- Principal Reports: 3 days
- Principal Approvals: 4 days
- Teacher Dashboard: 3 days
- Teacher Classes: 4 days
- Teacher Gradebook: 5 days
- Teacher Planning: 4 days

### Testing & Polish (5 days)

**Total: 42-51 days (8-10 weeks with 1 developer)**

---

## Next Immediate Steps

1. ✅ Create database schema for new tables
2. ✅ Implement approval_requests system
3. ✅ Build Principal Students API + Frontend
4. ✅ Build Principal Approvals API + Frontend
5. ✅ Build Teacher Gradebook API + Frontend
6. ✅ Build Teacher Planning API + Frontend
7. ✅ Integration testing
8. ✅ Deploy to production

---

## Key Success Metrics

**Principal Pages:**
- Approval turnaround time < 24 hours
- Risk case identification rate
- Executive report generation time < 5 seconds

**Teacher Pages:**
- Attendance submission time < 2 minutes
- Gradebook entry time < 30 seconds per student
- Lesson planning time reduced by 40%
- Teacher adoption rate > 85%
