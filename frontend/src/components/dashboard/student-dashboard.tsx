'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Clock,
    BookOpen,
    AlertCircle,
    Trophy,
    CalendarCheck,
    FileText,
    AlertTriangle,
    Megaphone,
    CheckCircle,
} from 'lucide-react';

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
    assignment_id: string;
}

interface Performance {
    attendance_rate: number;
    overall_average: number;
    subjects_below_70: number;
}

interface GradeItem {
    assignment: string;
    subject: string;
    score: number;
}

interface SubjectPerformance {
    subject: string;
    percentage: number;
}

interface Alert {
    type: string;
    message: string;
    priority: string;
}

export function StudentDashboard() {
    const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
    const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
    const [performance, setPerformance] = useState<Performance | null>(null);
    const [recentGrades, setRecentGrades] = useState<GradeItem[]>([]);
    const [subjects, setSubjects] = useState<SubjectPerformance[]>([]);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setLoading(false);
                return;
            }

            const headers = { 'Authorization': `Bearer ${token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [scheduleRes, assignmentsRes, performanceRes, gradesRes, subjectsRes, alertsRes] = await Promise.all([
                fetch(`${baseUrl}/student/schedule/today`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/assignments/today`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/performance/overview`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/grades/recent`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/performance/subjects`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/alerts`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (scheduleRes.ok) setSchedule(await scheduleRes.json());
            if (assignmentsRes.ok) setAssignments(await assignmentsRes.json());
            if (performanceRes.ok) setPerformance(await performanceRes.json());
            if (gradesRes.ok) setRecentGrades(await gradesRes.json());
            if (subjectsRes.ok) setSubjects(await subjectsRes.json());
            if (alertsRes.ok) setAlerts(await alertsRes.json());
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getAlertIcon = (type: string) => {
        switch (type) {
            case 'assignment':
            case 'overdue':
                return <FileText className="h-4 w-4" />;
            case 'attendance':
                return <CalendarCheck className="h-4 w-4" />;
            case 'announcement':
                return <Megaphone className="h-4 w-4" />;
            default:
                return <AlertCircle className="h-4 w-4" />;
        }
    };

    const getAlertStyle = (priority: string) => {
        switch (priority) {
            case 'high':
                return 'border-red-200 bg-red-50';
            case 'medium':
                return 'border-amber-200 bg-amber-50';
            default:
                return 'border-blue-200 bg-blue-50';
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

    // Determine current class based on time
    const getCurrentClassIndex = () => {
        if (schedule.length === 0) return -1;
        const now = new Date();
        const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        for (let i = schedule.length - 1; i >= 0; i--) {
            if (currentTime >= schedule[i].time) return i;
        }
        return -1;
    };

    const currentClassIdx = getCurrentClassIndex();

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
                <h1 className="text-3xl font-bold text-slate-900">Today at School</h1>
                <p className="text-slate-500 mt-1">Your schedule, assignments, and performance</p>
            </div>

            {/* Performance Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Attendance Rate</p>
                                <p className={`text-3xl font-bold ${(performance?.attendance_rate || 0) >= 90 ? 'text-emerald-600' : (performance?.attendance_rate || 0) >= 80 ? 'text-amber-600' : 'text-red-600'}`}>
                                    {performance?.attendance_rate || 0}%
                                </p>
                            </div>
                            <CalendarCheck className="h-8 w-8 text-slate-300" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Overall Average</p>
                                <p className={`text-3xl font-bold ${getScoreColor(performance?.overall_average || 0)}`}>
                                    {performance?.overall_average || 0}%
                                </p>
                            </div>
                            <Trophy className="h-8 w-8 text-slate-300" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Subjects Below 70%</p>
                                <p className={`text-3xl font-bold ${(performance?.subjects_below_70 || 0) === 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                    {performance?.subjects_below_70 || 0}
                                </p>
                            </div>
                            {(performance?.subjects_below_70 || 0) === 0 ? (
                                <CheckCircle className="h-8 w-8 text-emerald-300" />
                            ) : (
                                <AlertTriangle className="h-8 w-8 text-red-300" />
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Student Alerts */}
            {alerts.length > 0 && (
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="flex items-center gap-2">
                            <AlertCircle className="h-5 w-5 text-amber-500" />
                            Alerts
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {alerts.map((alert, idx) => (
                                <div key={idx} className={`p-3 rounded-lg border flex items-start gap-3 ${getAlertStyle(alert.priority)}`}>
                                    <div className="mt-0.5 text-slate-600">
                                        {getAlertIcon(alert.type)}
                                    </div>
                                    <p className="text-sm font-medium text-slate-900 flex-1">{alert.message}</p>
                                    {alert.priority === 'high' && (
                                        <Badge variant="destructive" className="text-xs shrink-0">Urgent</Badge>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Today's Schedule */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-blue-500" />
                        Today&apos;s Schedule
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {schedule.length > 0 ? (
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
                                {schedule.map((item, idx) => (
                                    <TableRow key={idx} className={idx === currentClassIdx ? 'bg-emerald-50 border-l-4 border-l-emerald-500' : ''}>
                                        <TableCell className="font-medium">
                                            {item.time}
                                            {idx === currentClassIdx && (
                                                <Badge className="ml-2 bg-emerald-100 text-emerald-700 hover:bg-emerald-100 text-xs">Now</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="font-medium">{item.subject}</TableCell>
                                        <TableCell>{item.teacher}</TableCell>
                                        <TableCell>{item.room}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="py-8 text-center text-slate-500">
                            <Clock className="h-10 w-10 mx-auto mb-3 text-slate-300" />
                            <p className="font-medium">No classes scheduled today</p>
                            <p className="text-sm mt-1">Enjoy your day off!</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Today's Tasks */}
            {assignments.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5 text-indigo-500" />
                            Upcoming Tasks
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Task</TableHead>
                                    <TableHead>Subject</TableHead>
                                    <TableHead>Due</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {assignments.map((task, idx) => (
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
                        <Button variant="outline" className="w-full mt-4">View All Assignments</Button>
                    </CardContent>
                </Card>
            )}

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
                        {recentGrades.length > 0 ? (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Assignment</TableHead>
                                        <TableHead>Subject</TableHead>
                                        <TableHead className="text-right">Score</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {recentGrades.map((grade, idx) => (
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
                        {subjects.length > 0 ? (
                            <div className="space-y-4">
                                {subjects.map((subject, idx) => (
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
        </div>
    );
}
