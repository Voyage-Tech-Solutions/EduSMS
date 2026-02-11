# System Admin Quick Reference

## 🎯 Purpose
System Admin manages the **EduCore SaaS platform**, not individual schools.

## 🔑 Access
Login with a user account that has `role = 'system_admin'` in the database.

## 📊 Dashboard Sections

### Platform Metrics
- Total Schools (with growth trend)
- Active Users (across all schools)
- Daily Active Users
- System Uptime & Performance

### System Health
- API Response Time
- Error Rate
- Total Students (platform-wide)
- Monthly Recurring Revenue

### Schools Overview
View all schools with:
- Name and code
- Status (Active/Inactive)
- User count
- Student count
- Last activity
- Actions (View, Suspend)

### System Alerts
- Performance warnings
- Security alerts
- System issues

### Security Center
- Failed login attempts (24h)
- Locked accounts
- Admin role changes
- Suspicious activity

### Platform Activity
Recent platform events:
- New schools created
- School upgrades
- Feature toggles
- System changes

## 🔧 API Endpoints

All endpoints require `system_admin` role and are prefixed with `/api/v1/system/`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/platform-metrics` | GET | Platform statistics |
| `/schools-overview` | GET | All schools list |
| `/system-alerts` | GET | Platform alerts |
| `/platform-activity` | GET | Recent events |
| `/security-summary` | GET | Security metrics |
| `/schools/{id}/suspend` | POST | Suspend school |
| `/schools/{id}/activate` | POST | Activate school |

## 🚀 Quick Actions

From the dashboard, System Admin can:
1. **Add New School** - Onboard new tenant
2. **View School** - See school details
3. **Suspend School** - Disable school access
4. **Monitor Alerts** - Review system issues
5. **Track Activity** - See platform events

## 📱 Navigation

System Admin sidebar shows:
- Dashboard (Platform overview)
- Schools (Manage all schools)
- Users (Global user management)
- Security (Security center)
- System Logs (Audit logs)
- Feature Flags (Toggle features)
- Settings (Platform settings)

## 🔐 Permissions

System Admin can:
✅ View all schools
✅ Suspend/activate schools
✅ View platform metrics
✅ Monitor system health
✅ Review security alerts
✅ Access audit logs

System Admin cannot:
❌ Edit student records directly
❌ Take attendance
❌ Record payments
❌ Manage school operations

## 💡 Use Cases

### Daily Tasks
- Check system health metrics
- Review security alerts
- Monitor active users
- Track new school signups

### Weekly Tasks
- Review platform activity
- Check school engagement
- Monitor revenue trends
- Review failed logins

### Monthly Tasks
- Analyze growth metrics
- Review churn risk schools
- Plan capacity scaling
- Generate platform reports

## 🐛 Troubleshooting

### Can't see System Admin dashboard?
- Check user role is `system_admin` in database
- Logout and login again
- Clear browser cache

### No data showing?
- Check Supabase connection
- Verify environment variables
- Check browser console for errors
- Mock data will show if DB not connected

### API errors?
- Check backend logs
- Verify JWT token
- Check role permissions
- Review API documentation at `/docs`

## 📞 Support

For issues:
1. Check backend logs: `backend/logs/app.log`
2. Review browser console
3. Check API docs: `http://localhost:8000/docs`
4. Review SYSTEM_ADMIN.md for details
