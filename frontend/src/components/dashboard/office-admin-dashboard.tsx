'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    ClipboardCheck,
    DollarSign,
    Users,
    FileText,
    AlertTriangle,
    CheckCircle,
} from 'lucide-react';

export function OfficeAdminDashboard() {
    const [priorities, setPriorities] = useState<any>(null);
    const [fees, setFees] = useState<any>(null);
    const [students, setStudents] = useState<any>(null);
    const [documents, setDocuments] = useState<any>(null);
    const [activity, setActivity] = useState<any[]>([]);
    const [exceptions, setExceptions] = useState<any[]>([]);
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

            const [prioritiesRes, feesRes, studentsRes, docsRes, activityRes, exceptionsRes] = await Promise.all([
                fetch(`${baseUrl}/office-admin/dashboard/priorities`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/office-admin/fees/snapshot`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/office-admin/students/snapshot`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/office-admin/documents/compliance`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/office-admin/activity/recent`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/office-admin/exceptions`, { headers }).catch(() => ({ ok: false } as Response))
            ]);

            if (prioritiesRes.ok) setPriorities(await prioritiesRes.json());
            if (feesRes.ok) setFees(await feesRes.json());
            if (studentsRes.ok) setStudents(await studentsRes.json());
            if (docsRes.ok) setDocuments(await docsRes.json());
            if (activityRes.ok) setActivity(await activityRes.json());
            if (exceptionsRes.ok) setExceptions(await exceptionsRes.json());
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
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-slate-500">Loading dashboard...</p>
                    </div>
                </div>
            </div>
        );
    }

    const priorityTasks = [
        { task: 'Admissions awaiting document verification', count: priorities?.admissions_pending || 0 },
        { task: 'Students with missing documents', count: priorities?.missing_documents || 0 },
        { task: 'Fee payments to allocate', count: priorities?.payments_to_allocate || 0 },
        { task: 'Proof of payment uploads', count: priorities?.proof_uploads || 0 },
        { task: 'Transfer requests pending', count: priorities?.transfer_requests || 0 },
        { task: 'Letters requested', count: priorities?.letters_requested || 0 },
    ];

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Office Operations Overview</h1>
                <p className="text-slate-500 mt-1">Daily workload, pending actions, and important updates</p>
            </div>

            {/* Today's Priorities */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <ClipboardCheck className="h-5 w-5 text-blue-500" />
                        Today's Priorities
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Task Type</TableHead>
                                <TableHead>Count</TableHead>
                                <TableHead className="text-right">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {priorityTasks.map((task, idx) => (
                                <TableRow key={idx}>
                                    <TableCell className="font-medium">{task.task}</TableCell>
                                    <TableCell>
                                        <Badge variant={task.count > 0 ? "destructive" : "secondary"}>
                                            {task.count}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button size="sm" disabled={task.count === 0}>
                                            {task.task.includes('awaiting') ? 'Review' : 
                                             task.task.includes('missing') ? 'Follow Up' : 
                                             task.task.includes('allocate') ? 'Process' : 
                                             task.task.includes('uploads') ? 'Verify' : 
                                             task.task.includes('Transfer') ? 'Review' : 'Generate'}
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Fees & Payments */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <DollarSign className="h-5 w-5 text-emerald-500" />
                            Fees & Payments Snapshot
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Collected This Month</span>
                                <span className="font-bold text-emerald-600">${fees?.collected_this_month || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Outstanding Balance</span>
                                <span className="font-bold text-amber-600">${fees?.outstanding_balance || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Overdue (30+ days)</span>
                                <span className="font-bold text-red-600">${fees?.overdue_amount || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Payment Plans Active</span>
                                <span className="font-bold">{fees?.active_payment_plans || 0}</span>
                            </div>
                            <div className="flex gap-2 mt-4">
                                <Button size="sm" className="flex-1" onClick={() => window.location.href = '/dashboard/attendance'}>
                                    Save Attendance
                                </Button>
                                <Button variant="outline" size="sm" className="flex-1" onClick={() => window.location.href = '/dashboard/fees'}>
                                    Create Invoice
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Student Admin */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Users className="h-5 w-5 text-blue-500" />
                            Student Admin Snapshot
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Total Active Students</span>
                                <span className="font-bold">{students?.total_active || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">New Admissions This Month</span>
                                <span className="font-bold text-emerald-600">{students?.new_this_month || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Pending Transfers</span>
                                <span className="font-bold text-amber-600">{students?.pending_transfers || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Inactive Students</span>
                                <span className="font-bold">{students?.inactive_students || 0}</span>
                            </div>
                            <div className="flex gap-2 mt-4">
                                <Button size="sm" className="flex-1" onClick={() => window.location.href = '/dashboard/students'}>
                                    Add Student
                                </Button>
                                <Button variant="outline" size="sm" className="flex-1" onClick={() => window.location.href = '/dashboard/staff'}>
                                    Add Staff
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Quick Reports */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-indigo-500" />
                        Quick Reports
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <Button variant="outline" size="sm" onClick={() => window.location.href = '/dashboard/reports?type=student-directory'}>
                            Student Directory
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => window.location.href = '/dashboard/reports?type=fee-statement'}>
                            Fee Statement
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => window.location.href = '/dashboard/reports?type=attendance-summary'}>
                            Attendance Summary
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => window.location.href = '/dashboard/reports?type=grade-report'}>
                            Grade Report
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Documents & Compliance */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-purple-500" />
                        Documents & Compliance
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 rounded-lg bg-red-50 border border-red-200">
                            <p className="text-2xl font-bold text-red-600">{documents?.missing_birth_certificates || 0}</p>
                            <p className="text-sm text-slate-600">Missing Birth Certificates</p>
                        </div>
                        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                            <p className="text-2xl font-bold text-amber-600">{documents?.missing_parent_ids || 0}</p>
                            <p className="text-sm text-slate-600">Missing Parent IDs</p>
                        </div>
                        <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                            <p className="text-2xl font-bold text-blue-600">{documents?.missing_medical_forms || 0}</p>
                            <p className="text-sm text-slate-600">Medical Forms Outstanding</p>
                        </div>
                    </div>
                    <Button variant="outline" className="w-full mt-4">Send Bulk Reminder</Button>
                </CardContent>
            </Card>

            {/* Exceptions & Flags */}
            {exceptions.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                            Exceptions & Flags
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {exceptions.map((exception, idx) => (
                                <div key={idx} className="p-3 rounded-lg border border-red-200 bg-red-50 flex justify-between items-center">
                                    <div>
                                        <p className="font-medium text-slate-900">{exception.message}</p>
                                        {exception.count && <p className="text-sm text-slate-500">{exception.count} cases</p>}
                                    </div>
                                    <Button size="sm" variant="outline">Resolve</Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Recent Activity */}
            {activity.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Recent Admin Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {activity.map((act, idx) => (
                                <div key={idx} className="flex items-start gap-3 pb-3 border-b last:border-0">
                                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                        <CheckCircle className="h-4 w-4 text-blue-600" />
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
