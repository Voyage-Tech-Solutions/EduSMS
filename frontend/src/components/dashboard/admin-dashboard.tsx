'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { StatCard } from '@/components/dashboard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Users,
    TrendingUp,
    CalendarCheck,
    DollarSign,
    AlertTriangle,
    CheckCircle,
    Clock,
    FileText,
    UserCheck,
    GraduationCap,
    Shield,
} from 'lucide-react';

interface AdminDashboardProps {
    isSystemAdmin?: boolean;
}

export function AdminDashboard({ isSystemAdmin = false }: AdminDashboardProps) {
    const router = useRouter();
    const [metrics, setMetrics] = useState<any>(null);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [approvals, setApprovals] = useState<any[]>([]);
    const [academic, setAcademic] = useState<any>(null);
    const [finance, setFinance] = useState<any>(null);
    const [staff, setStaff] = useState<any>(null);
    const [activity, setActivity] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            if (!session?.access_token) {
                console.error('No auth session found');
                setLoading(false);
                return;
            }
            
            const headers = { 'Authorization': `Bearer ${session.access_token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [metricsRes, alertsRes, approvalsRes, academicRes, financeRes, staffRes, activityRes] = await Promise.all([
                fetch(`${baseUrl}/principal/dashboard/metrics`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/principal/alerts`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/principal/approvals`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/principal/academic/performance`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/principal/finance/overview`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/principal/staff/insight`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/principal/activity/recent`, { headers }).catch(() => ({ ok: false } as Response))
            ]);

            if (metricsRes.ok) setMetrics(await metricsRes.json());
            if (alertsRes.ok) setAlerts(await alertsRes.json());
            if (approvalsRes.ok) setApprovals(await approvalsRes.json());
            if (academicRes.ok) setAcademic(await academicRes.json());
            if (financeRes.ok) setFinance(await financeRes.json());
            if (staffRes.ok) setStaff(await staffRes.json());
            if (activityRes.ok) setActivity(await activityRes.json());
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
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
                <h1 className="text-3xl font-bold text-slate-900">School Performance Overview</h1>
                <p className="text-slate-500 mt-1">Key insights, approvals, and risks across your school</p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Students"
                    value={metrics?.total_students?.toString() || '0'}
                    description="Active enrollment"
                    icon={Users}
                />
                <StatCard
                    title="Attendance Rate"
                    value={`${metrics?.attendance_rate || 0}%`}
                    description="Last 30 days"
                    icon={CalendarCheck}
                />
                <StatCard
                    title="Students At Risk"
                    value={metrics?.at_risk_count?.toString() || '0'}
                    description="Require intervention"
                    icon={AlertTriangle}
                />
                <StatCard
                    title="Fee Collection"
                    value={`${metrics?.collection_rate || 0}%`}
                    description={`$${metrics?.outstanding_balance || 0} outstanding`}
                    icon={DollarSign}
                />
            </div>

            {/* School Alerts */}
            {alerts.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                            School Alerts
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {alerts.map((alert, idx) => (
                                <div key={idx} className={`p-3 rounded-lg border cursor-pointer hover:bg-slate-50 ${
                                    alert.severity === 'high' ? 'border-red-200 bg-red-50' :
                                    alert.severity === 'medium' ? 'border-amber-200 bg-amber-50' :
                                    'border-blue-200 bg-blue-50'
                                }`}>
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className={`h-5 w-5 ${
                                            alert.severity === 'high' ? 'text-red-600' :
                                            alert.severity === 'medium' ? 'text-amber-600' :
                                            'text-blue-600'
                                        }`} />
                                        <p className="font-medium text-slate-900">{alert.message}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Approvals Required */}
            {approvals.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <CheckCircle className="h-5 w-5 text-emerald-500" />
                            Approvals Required
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Approval Type</TableHead>
                                    <TableHead>Count</TableHead>
                                    <TableHead>Priority</TableHead>
                                    <TableHead className="text-right">Action</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {approvals.map((approval, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{approval.type}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary">{approval.count}</Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge className={approval.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}>
                                                {approval.priority}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button size="sm">Review</Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Academic Performance */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <GraduationCap className="h-5 w-5 text-blue-500" />
                            Academic Performance
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Pass Rate</span>
                                <span className="font-bold">{academic?.pass_rate || 0}%</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Assessment Completion</span>
                                <span className="font-bold">{academic?.completion_rate || 0}%</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Reports Submitted</span>
                                <span className="font-bold">{academic?.reports_submitted || 0}/{academic?.total_teachers || 0} Teachers</span>
                            </div>
                            <Button variant="outline" className="w-full mt-4" onClick={() => router.push('/dashboard/academics/report')}>View Full Report</Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Finance Overview */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <DollarSign className="h-5 w-5 text-emerald-500" />
                            Finance Overview
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Collection Rate</span>
                                <span className="font-bold">{finance?.collection_rate || 0}%</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Outstanding Balance</span>
                                <span className="font-bold text-amber-600">${finance?.outstanding_balance || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Overdue (30+ days)</span>
                                <span className="font-bold text-red-600">${finance?.overdue_amount || 0}</span>
                            </div>
                            <Button variant="outline" className="w-full mt-4" onClick={() => router.push('/dashboard/fees/arrears')}>View Arrears List</Button>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Staff Insight */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <UserCheck className="h-5 w-5 text-purple-500" />
                        Staff Insight
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold">{staff?.active_teachers || 0}</p>
                            <p className="text-sm text-slate-500">Active Teachers</p>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold">{staff?.marking_complete || 0}%</p>
                            <p className="text-sm text-slate-500">Marking Complete</p>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold">{staff?.staff_absent || 0}</p>
                            <p className="text-sm text-slate-500">Staff Absent Today</p>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold">{staff?.late_submissions || 0}</p>
                            <p className="text-sm text-slate-500">Late Submissions</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Recent Activity */}
            {activity.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Recent School Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {activity.map((act, idx) => (
                                <div key={idx} className="flex items-start gap-3 pb-3 border-b last:border-0">
                                    <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center">
                                        <FileText className="h-4 w-4 text-emerald-600" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-slate-900">{act.action}</p>
                                        <p className="text-xs text-slate-500 mt-1">{new Date(act.time).toLocaleString()}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
