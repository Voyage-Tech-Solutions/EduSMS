'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    CalendarCheck,
    DollarSign,
    BookOpen,
    Bell,
    FileText,
    MessageSquare,
    TrendingUp,
    TrendingDown,
    Minus,
    AlertTriangle,
    Megaphone,
    CreditCard,
    Users,
    Clock,
    Trophy,
} from 'lucide-react';

interface ChildOverview {
    name: string;
    class: string;
    attendance_rate: number;
    average_grade: number;
    pending_assignments: number;
    outstanding_fees: number;
    student_id: string;
}

interface Notification {
    type: string;
    message: string;
    priority: string;
}

interface FeeItem {
    item: string;
    amount: number;
    due_date: string;
    invoice_id: string;
    status: string;
}

interface AcademicProgress {
    name: string;
    student_id: string;
    trend: string;
    recent_grades: { subject: string; assessment: string; score: number }[];
    attendance_trend: number;
}

interface Announcement {
    id: string;
    title: string;
    content: string;
    priority: string;
    date: string;
}

interface ScheduleItem {
    time: string;
    subject: string;
    teacher: string;
    room: string;
}

interface AssignmentItem {
    task: string;
    subject: string;
    due: string;
    due_date: string;
}

interface SubjectPerformance {
    subject: string;
    percentage: number;
}

interface GradeItem {
    assignment: string;
    subject: string;
    score: number;
}

export function ParentDashboard() {
    const [children, setChildren] = useState<ChildOverview[]>([]);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [fees, setFees] = useState<FeeItem[]>([]);
    const [progress, setProgress] = useState<AcademicProgress[]>([]);
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [loading, setLoading] = useState(true);

    // Child detail state
    const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
    const [childSchedule, setChildSchedule] = useState<ScheduleItem[]>([]);
    const [childAssignments, setChildAssignments] = useState<AssignmentItem[]>([]);
    const [childSubjects, setChildSubjects] = useState<SubjectPerformance[]>([]);
    const [childGrades, setChildGrades] = useState<GradeItem[]>([]);
    const [childDetailLoading, setChildDetailLoading] = useState(false);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    useEffect(() => {
        if (selectedChildId) {
            fetchChildDetails(selectedChildId);
        }
    }, [selectedChildId]);

    const getHeaders = async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}` };
    };

    const fetchDashboardData = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [childrenRes, notificationsRes, feesRes, progressRes, announcementsRes] = await Promise.all([
                fetch(`${baseUrl}/parent/children/overview`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/notifications`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/fees/summary`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/academic/progress`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/announcements`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (childrenRes.ok) {
                const data = await childrenRes.json();
                setChildren(data);
                if (data.length > 0 && !selectedChildId) {
                    setSelectedChildId(data[0].student_id);
                }
            }
            if (notificationsRes.ok) setNotifications(await notificationsRes.json());
            if (feesRes.ok) setFees(await feesRes.json());
            if (progressRes.ok) setProgress(await progressRes.json());
            if (announcementsRes.ok) setAnnouncements(await announcementsRes.json());
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchChildDetails = async (studentId: string) => {
        setChildDetailLoading(true);
        try {
            const headers = await getHeaders();
            if (!headers) { setChildDetailLoading(false); return; }

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [scheduleRes, assignmentsRes, subjectsRes, gradesRes] = await Promise.all([
                fetch(`${baseUrl}/parent/children/${studentId}/schedule/today`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/children/${studentId}/assignments`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/children/${studentId}/subjects`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/children/${studentId}/grades/recent`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (scheduleRes.ok) setChildSchedule(await scheduleRes.json()); else setChildSchedule([]);
            if (assignmentsRes.ok) setChildAssignments(await assignmentsRes.json()); else setChildAssignments([]);
            if (subjectsRes.ok) setChildSubjects(await subjectsRes.json()); else setChildSubjects([]);
            if (gradesRes.ok) setChildGrades(await gradesRes.json()); else setChildGrades([]);
        } catch (error) {
            console.error('Failed to fetch child details:', error);
        } finally {
            setChildDetailLoading(false);
        }
    };

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'fee_overdue':
            case 'fee_due':
                return <CreditCard className="h-4 w-4" />;
            case 'assignment_overdue':
                return <BookOpen className="h-4 w-4" />;
            case 'attendance_warning':
                return <CalendarCheck className="h-4 w-4" />;
            case 'discipline':
                return <AlertTriangle className="h-4 w-4" />;
            default:
                return <Bell className="h-4 w-4" />;
        }
    };

    const getNotificationStyle = (priority: string) => {
        switch (priority) {
            case 'high': return 'border-red-200 bg-red-50';
            case 'medium': return 'border-amber-200 bg-amber-50';
            default: return 'border-blue-200 bg-blue-50';
        }
    };

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'improving': return <TrendingUp className="h-4 w-4 text-emerald-500" />;
            case 'declining': return <TrendingDown className="h-4 w-4 text-red-500" />;
            default: return <Minus className="h-4 w-4 text-slate-400" />;
        }
    };

    const getTrendBadge = (trend: string) => {
        switch (trend) {
            case 'improving': return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Improving</Badge>;
            case 'declining': return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">Declining</Badge>;
            default: return <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100">Stable</Badge>;
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-emerald-600';
        if (score >= 60) return 'text-amber-600';
        return 'text-red-600';
    };

    const getBarColor = (pct: number) => {
        if (pct >= 80) return 'bg-emerald-500';
        if (pct >= 60) return 'bg-amber-500';
        return 'bg-red-500';
    };

    const selectedChild = children.find(c => c.student_id === selectedChildId);

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
                        <p className="mt-4 text-slate-500">Loading dashboard...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Your Children&apos;s Overview</h1>
                <p className="text-slate-500 mt-1">Track academic progress, attendance, fees, and daily activities</p>
            </div>

            {/* Children Summary Cards */}
            {children.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {children.map((child) => (
                        <Card
                            key={child.student_id}
                            className={`overflow-hidden cursor-pointer transition-all ${selectedChildId === child.student_id ? 'ring-2 ring-emerald-500 shadow-lg' : 'hover:shadow-md'}`}
                            onClick={() => setSelectedChildId(child.student_id)}
                        >
                            <CardHeader className={`pb-3 ${selectedChildId === child.student_id ? 'bg-emerald-50' : 'bg-slate-50'}`}>
                                <CardTitle className="flex items-center gap-2">
                                    <Users className="h-5 w-5 text-emerald-600" />
                                    {child.name} &ndash; {child.class}
                                    {selectedChildId === child.student_id && (
                                        <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 ml-auto">Selected</Badge>
                                    )}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-slate-500">Attendance</p>
                                        <p className={`text-2xl font-bold ${child.attendance_rate >= 90 ? 'text-emerald-600' : child.attendance_rate >= 80 ? 'text-amber-600' : 'text-red-600'}`}>
                                            {child.attendance_rate}%
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-500">Average Grade</p>
                                        <p className={`text-2xl font-bold ${child.average_grade >= 80 ? 'text-emerald-600' : child.average_grade >= 60 ? 'text-amber-600' : 'text-red-600'}`}>
                                            {child.average_grade}%
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-500">Pending Assignments</p>
                                        <p className="text-2xl font-bold">{child.pending_assignments}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-500">Outstanding Fees</p>
                                        <p className={`text-2xl font-bold ${child.outstanding_fees > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                            ${child.outstanding_fees}
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card>
                    <CardContent className="py-12 text-center text-slate-500">
                        <Users className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                        <p className="font-medium">No children linked to your account yet.</p>
                        <p className="text-sm mt-1">Contact your school administration to link your children.</p>
                    </CardContent>
                </Card>
            )}

            {/* Child Detail Section */}
            {selectedChild && (
                <>
                    <div className="border-t pt-6">
                        <h2 className="text-xl font-bold text-slate-900 mb-1">
                            {selectedChild.name}&apos;s Details
                        </h2>
                        <p className="text-slate-500 text-sm">Schedule, assignments, grades, and subject performance</p>
                    </div>

                    {childDetailLoading ? (
                        <div className="flex items-center justify-center h-32">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
                        </div>
                    ) : (
                        <>
                            {/* Today's Schedule */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Clock className="h-5 w-5 text-blue-500" />
                                        Today&apos;s Schedule
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    {childSchedule.length > 0 ? (
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead className="w-20">Time</TableHead>
                                                    <TableHead>Subject</TableHead>
                                                    <TableHead>Teacher</TableHead>
                                                    <TableHead>Room</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {childSchedule.map((item, idx) => (
                                                    <TableRow key={idx}>
                                                        <TableCell className="font-medium">{item.time}</TableCell>
                                                        <TableCell className="font-medium">{item.subject}</TableCell>
                                                        <TableCell>{item.teacher}</TableCell>
                                                        <TableCell>{item.room}</TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    ) : (
                                        <div className="py-6 text-center text-slate-500">
                                            <Clock className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                                            <p className="text-sm">No classes scheduled today</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Upcoming Assignments */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <FileText className="h-5 w-5 text-indigo-500" />
                                        Upcoming Assignments
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    {childAssignments.length > 0 ? (
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>Task</TableHead>
                                                    <TableHead>Subject</TableHead>
                                                    <TableHead>Due</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {childAssignments.map((task, idx) => (
                                                    <TableRow key={idx}>
                                                        <TableCell className="font-medium">{task.task}</TableCell>
                                                        <TableCell>{task.subject}</TableCell>
                                                        <TableCell>
                                                            <Badge variant={task.due === 'Today' ? 'destructive' : task.due === 'Tomorrow' ? 'secondary' : 'outline'}>
                                                                {task.due}
                                                            </Badge>
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    ) : (
                                        <div className="py-6 text-center text-slate-500">
                                            <FileText className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                                            <p className="text-sm">No upcoming assignments</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Recent Grades */}
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <Trophy className="h-5 w-5 text-amber-500" />
                                            Recent Grades
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {childGrades.length > 0 ? (
                                            <Table>
                                                <TableHeader>
                                                    <TableRow>
                                                        <TableHead>Assessment</TableHead>
                                                        <TableHead>Subject</TableHead>
                                                        <TableHead className="text-right">Score</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                    {childGrades.map((grade, idx) => (
                                                        <TableRow key={idx}>
                                                            <TableCell className="font-medium">{grade.assignment}</TableCell>
                                                            <TableCell>{grade.subject}</TableCell>
                                                            <TableCell className={`text-right font-bold ${getScoreColor(grade.score)}`}>
                                                                {grade.score}%
                                                            </TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        ) : (
                                            <div className="py-6 text-center text-slate-500">
                                                <Trophy className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                                                <p className="text-sm">No grades recorded yet</p>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>

                                {/* Subject Performance */}
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <BookOpen className="h-5 w-5 text-emerald-500" />
                                            Subject Performance
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {childSubjects.length > 0 ? (
                                            <div className="space-y-4">
                                                {childSubjects.map((subject, idx) => (
                                                    <div key={idx}>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-sm font-medium text-slate-700">{subject.subject}</span>
                                                            <span className={`text-sm font-bold ${getScoreColor(subject.percentage)}`}>
                                                                {subject.percentage}%
                                                            </span>
                                                        </div>
                                                        <div className="w-full bg-slate-100 rounded-full h-2.5">
                                                            <div
                                                                className={`h-2.5 rounded-full transition-all ${getBarColor(subject.percentage)}`}
                                                                style={{ width: `${Math.min(subject.percentage, 100)}%` }}
                                                            ></div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="py-6 text-center text-slate-500">
                                                <BookOpen className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                                                <p className="text-sm">No subject data available yet</p>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        </>
                    )}
                </>
            )}

            {/* Important Notifications */}
            {notifications.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Bell className="h-5 w-5 text-amber-500" />
                            Important Notifications
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {notifications.map((notif, idx) => (
                                <div key={idx} className={`p-3 rounded-lg border flex items-start gap-3 ${getNotificationStyle(notif.priority)}`}>
                                    <div className="mt-0.5 text-slate-600">
                                        {getNotificationIcon(notif.type)}
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-slate-900">{notif.message}</p>
                                    </div>
                                    {notif.priority === 'high' && (
                                        <Badge variant="destructive" className="text-xs">Urgent</Badge>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Fees Summary */}
            {fees.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <DollarSign className="h-5 w-5 text-emerald-500" />
                            Fees Summary
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Item</TableHead>
                                    <TableHead>Amount</TableHead>
                                    <TableHead>Due Date</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead className="text-right">Action</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {fees.map((fee, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{fee.item}</TableCell>
                                        <TableCell>${fee.amount}</TableCell>
                                        <TableCell>{new Date(fee.due_date).toLocaleDateString()}</TableCell>
                                        <TableCell>
                                            <Badge className={
                                                fee.status === 'overdue' ? 'bg-red-100 text-red-700 hover:bg-red-100' :
                                                fee.status === 'partial' ? 'bg-amber-100 text-amber-700 hover:bg-amber-100' :
                                                'bg-slate-100 text-slate-700 hover:bg-slate-100'
                                            }>
                                                {fee.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button size="sm">Pay Now</Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                        <div className="flex gap-2 mt-4">
                            <Button variant="outline">View Full Statement</Button>
                            <Button variant="outline">Upload Proof of Payment</Button>
                            <Button variant="outline">Request Payment Plan</Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Academic Progress Snapshot */}
            {progress.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BookOpen className="h-5 w-5 text-blue-500" />
                            Academic Progress Trends
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            {progress.map((child, idx) => (
                                <div key={idx} className={idx > 0 ? 'pt-6 border-t' : ''}>
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="font-semibold text-slate-900">{child.name}</h3>
                                        <div className="flex items-center gap-2">
                                            {getTrendIcon(child.trend)}
                                            {getTrendBadge(child.trend)}
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-sm text-slate-500 mb-2">Recent Grades</p>
                                            {child.recent_grades.length > 0 ? (
                                                <div className="space-y-1">
                                                    {child.recent_grades.map((grade, gIdx) => (
                                                        <div key={gIdx} className="flex justify-between items-center text-sm">
                                                            <span className="text-slate-700">{grade.subject} - {grade.assessment}</span>
                                                            <span className={`font-semibold ${grade.score >= 80 ? 'text-emerald-600' : grade.score >= 60 ? 'text-amber-600' : 'text-red-600'}`}>
                                                                {grade.score}%
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-slate-400">No recent grades</p>
                                            )}
                                        </div>
                                        <div>
                                            <p className="text-sm text-slate-500 mb-2">Attendance (30 days)</p>
                                            <div className="flex items-center gap-3">
                                                <div className="flex-1 bg-slate-100 rounded-full h-3">
                                                    <div
                                                        className={`h-3 rounded-full ${child.attendance_trend >= 90 ? 'bg-emerald-500' : child.attendance_trend >= 80 ? 'bg-amber-500' : 'bg-red-500'}`}
                                                        style={{ width: `${Math.min(child.attendance_trend, 100)}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-sm font-semibold">{child.attendance_trend}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* School Announcements */}
            {announcements.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Megaphone className="h-5 w-5 text-indigo-500" />
                            School Announcements
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {announcements.map((ann) => (
                                <div key={ann.id} className="p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h4 className="font-medium text-slate-900">{ann.title}</h4>
                                            <p className="text-sm text-slate-500 mt-1 line-clamp-2">{ann.content}</p>
                                        </div>
                                        {ann.priority === 'urgent' && (
                                            <Badge variant="destructive" className="ml-2 shrink-0">Urgent</Badge>
                                        )}
                                        {ann.priority === 'high' && (
                                            <Badge className="ml-2 shrink-0 bg-amber-100 text-amber-700 hover:bg-amber-100">Important</Badge>
                                        )}
                                    </div>
                                    {ann.date && (
                                        <p className="text-xs text-slate-400 mt-2">
                                            {new Date(ann.date).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
