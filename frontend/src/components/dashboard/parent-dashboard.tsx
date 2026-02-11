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

export function ParentDashboard() {
    const [children, setChildren] = useState<ChildOverview[]>([]);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [fees, setFees] = useState<FeeItem[]>([]);
    const [progress, setProgress] = useState<AcademicProgress[]>([]);
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
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

            const [childrenRes, notificationsRes, feesRes, progressRes, announcementsRes] = await Promise.all([
                fetch(`${baseUrl}/parent/children/overview`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/notifications`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/fees/summary`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/academic/progress`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/announcements`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (childrenRes.ok) setChildren(await childrenRes.json());
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
            case 'high':
                return 'border-red-200 bg-red-50';
            case 'medium':
                return 'border-amber-200 bg-amber-50';
            default:
                return 'border-blue-200 bg-blue-50';
        }
    };

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'improving':
                return <TrendingUp className="h-4 w-4 text-emerald-500" />;
            case 'declining':
                return <TrendingDown className="h-4 w-4 text-red-500" />;
            default:
                return <Minus className="h-4 w-4 text-slate-400" />;
        }
    };

    const getTrendBadge = (trend: string) => {
        switch (trend) {
            case 'improving':
                return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Improving</Badge>;
            case 'declining':
                return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">Declining</Badge>;
            default:
                return <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100">Stable</Badge>;
        }
    };

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
                <p className="text-slate-500 mt-1">Track academic progress, attendance, and fees</p>
            </div>

            {/* Children Summary Cards */}
            {children.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {children.map((child, idx) => (
                        <Card key={idx} className="overflow-hidden">
                            <CardHeader className="bg-slate-50 pb-3">
                                <CardTitle className="flex items-center gap-2">
                                    <Users className="h-5 w-5 text-emerald-600" />
                                    {child.name} &ndash; {child.class}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4">
                                <div className="space-y-4">
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
                                    <div className="flex gap-2 pt-4 border-t">
                                        <Button variant="outline" size="sm" className="flex-1">
                                            <FileText className="h-4 w-4 mr-1" />
                                            Report Card
                                        </Button>
                                        <Button variant="outline" size="sm" className="flex-1">
                                            <CalendarCheck className="h-4 w-4 mr-1" />
                                            Attendance
                                        </Button>
                                        <Button variant="outline" size="sm" className="flex-1">
                                            <MessageSquare className="h-4 w-4 mr-1" />
                                            Message Teacher
                                        </Button>
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
                            Academic Progress
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
