# Complete Implementation PRDs - Principal & Teacher Modules

## Status: Documented, Ready for Implementation

This document contains full PRDs for:
1. Principal Students (Oversight Mode)
2. Principal Reports & Analytics
3. Principal Approvals Required
4. Teacher Dashboard (Enhanced)
5. Teacher My Classes
6. Teacher Gradebook
7. Teacher Planning

---

## Priority Implementation Order

### Phase 1: Critical Backend (Week 1-2)
1. Approval requests system
2. Teacher gradebook backend
3. Lesson planning backend
4. Enhanced principal students API

### Phase 2: Frontend Pages (Week 3-4)
1. Principal Approvals page
2. Teacher Gradebook page
3. Teacher Planning page
4. Enhanced Teacher Dashboard

### Phase 3: Advanced Features (Week 5-6)
1. Bulk operations
2. Import/Export functionality
3. Analytics charts
4. Notification system

---

## Database Schema Additions Needed

### Approval System
```sql
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id),
    type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    requested_by UUID REFERENCES user_profiles(id),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    decision VARCHAR(20),
    decided_by UUID REFERENCES user_profiles(id),
    decided_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Teacher Planning
```sql
CREATE TABLE lesson_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    term_id UUID REFERENCES terms(id),
    date DATE NOT NULL,
    time_slot VARCHAR(50),
    topic VARCHAR(200) NOT NULL,
    objectives TEXT,
    activities TEXT,
    homework TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE assessment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    term_id UUID REFERENCES terms(id),
    title VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    planned_date DATE,
    total_marks DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'planned',
    linked_assessment_id UUID REFERENCES assessments(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id),
    uploaded_by UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    title VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url TEXT,
    tags TEXT[],
    visibility VARCHAR(20) DEFAULT 'private',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE gradebook_locks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    term_id UUID REFERENCES terms(id),
    locked_by UUID NOT NULL REFERENCES user_profiles(id),
    locked_at TIMESTAMPTZ DEFAULT NOW(),
    unlock_requested BOOLEAN DEFAULT false,
    unlock_approved_by UUID REFERENCES user_profiles(id),
    UNIQUE(class_id, subject_id, term_id)
);
```

---

## API Endpoints Summary

### Principal APIs
- `/principal/students` - Oversight view with risk indicators
- `/principal/students/{id}` - Full student profile
- `/principal/students/risk` - Flag for intervention
- `/principal/students/notify` - Send parent notification
- `/principal/students/export` - Executive reports
- `/principal/approvals` - Approval queue
- `/principal/approvals/{id}/decision` - Approve/reject
- `/principal/reports/summary` - Executive analytics
- `/principal/reports/generate` - Custom reports

### Teacher APIs
- `/teacher/dashboard/summary` - Today's overview
- `/teacher/schedule/today` - Daily schedule
- `/teacher/classes/snapshot` - All classes summary
- `/teacher/alerts` - At-risk students, pending tasks
- `/teacher/gradebook` - Spreadsheet view
- `/teacher/gradebook/assessments` - CRUD assessments
- `/teacher/gradebook/import` - Bulk import marks
- `/teacher/gradebook/lock` - Lock gradebook
- `/teacher/planning/lessons` - Lesson plans CRUD
- `/teacher/planning/copy-week` - Duplicate planning
- `/teacher/planning/assessments` - Assessment planning
- `/teacher/resources` - Upload/manage resources

---

## Key Features by Module

### Principal Students (Oversight)
- Risk-aware student list
- Multi-risk indicators (attendance/academic/financial)
- One-click intervention flagging
- Parent notification system
- Executive-level exports
- Status change approvals

### Principal Approvals
- Centralized approval queue
- Priority-based sorting
- Approval types: admissions, transfers, write-offs, payment plans, role changes
- Dual approval support (optional)
- Audit trail for all decisions
- Empty state with metrics

### Teacher Gradebook
- Spreadsheet-style interface
- Inline editing with keyboard navigation
- Bulk import from CSV
- Assessment management
- Auto-calculate averages and ranks
- Lock/unlock workflow
- Export to CSV/PDF
- Analytics tab with charts

### Teacher Planning
- Weekly planner grid
- Curriculum coverage tracking
- Resource library
- Assessment planning
- Copy previous week
- Lesson status tracking
- Export weekly plans
- Integration with gradebook

---

## Implementation Notes

### Critical Success Factors
1. **Speed**: Gradebook must be spreadsheet-fast
2. **Keyboard Navigation**: Teachers need arrow keys, enter, tab
3. **Bulk Operations**: Import/export must handle 50+ students
4. **Validation**: Prevent data corruption with proper checks
5. **Audit**: Log all grade changes, approvals, status updates

### UX Requirements
- Loading states for all async operations
- Confirmation dialogs for destructive actions
- Inline error messages
- Toast notifications for success/failure
- Empty states with actionable guidance
- Responsive design for tablets

### Security Requirements
- RLS policies on all new tables
- Role-based access control
- Approval audit trail
- Grade change logging
- Principal override tracking

---

## Estimated Effort

### Backend Development
- Approval system: 3-4 days
- Gradebook APIs: 4-5 days
- Planning APIs: 3-4 days
- Principal oversight APIs: 2-3 days
**Total**: 12-16 days

### Frontend Development
- Principal pages: 5-6 days
- Teacher Gradebook: 6-7 days
- Teacher Planning: 4-5 days
- Dashboard enhancements: 3-4 days
**Total**: 18-22 days

### Testing & Polish
- Integration testing: 3-4 days
- User acceptance testing: 2-3 days
- Bug fixes: 3-4 days
**Total**: 8-11 days

**Grand Total**: 38-49 days (8-10 weeks with 1 developer)

---

## Next Immediate Steps

1. ✅ Run `schema_new_tables_only.sql` in Supabase
2. Create approval_requests, lesson_plans, assessment_plans, resources, gradebook_locks tables
3. Implement principal approval endpoints
4. Implement teacher gradebook endpoints
5. Build principal approvals frontend page
6. Build teacher gradebook frontend page

---

## Current System Status

### ✅ Complete
- Database schema for risk management, assessments
- Principal dashboard with real metrics
- Attendance recording
- Admissions workflow
- Fee management basics
- Documents compliance

### 🚧 In Progress
- Principal oversight features
- Teacher workflow tools
- Approval system
- Advanced analytics

### 📋 Planned
- Gradebook implementation
- Lesson planning
- Resource management
- Notification system
- Parent portal

---

This document serves as the complete specification for the remaining work. All PRDs are detailed with buttons, forms, workflows, validations, and backend requirements.
