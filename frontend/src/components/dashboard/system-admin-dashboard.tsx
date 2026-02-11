'use client';

import React, { useEffect, useState } from 'react';
import { StatCard } from '@/components/dashboard';
import { AddSchoolDialog } from '@/components/forms/add-school-dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Building2,
    Users,
    Activity,
    DollarSign,
    AlertTriangle,
    Shield,
    TrendingUp,
    Server,
    Plus,
    Eye,
    Ban,
    CheckCircle,
} from 'lucide-react';
import { api } from '@/lib/api';

export function SystemAdminDashboard() {
    const [metrics, setMetrics] = useState<any>(null);
    const [schools, setSchools] = useState<any[]>([]);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [activity, setActivity] = useState<any[]>([]);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            const [metricsData, schoolsData, alertsData, activityData, securityData] = await Promise.all([
                fetch('/api/v1/system/platform-metrics').then(r => r.json()).catch(() => ({})),
                fetch('/api/v1/system/schools').then(r => r.json()).catch(() => []),
                fetch('/api/v1/system/alerts').then(r => r.json()).catch(() => []),
                fetch('/api/v1/system/activity').then(r => r.json()).catch(() => []),
                fetch('/api/v1/system/security/summary').then(r => r.json()).catch(() => ({})),
            ]);

            setMetrics({ ...metricsData, ...securityData });
            setSchools(schoolsData);
            setAlerts(alertsData);
            setActivity(activityData);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Platform Overview</h1>
                    <p className="text-slate-500 mt-1">Monitor all schools, system health, and platform activity</p>
                </div>
                <AddSchoolDialog onSchoolAdded={loadDashboardData} />
            </div>

            {/* Platform Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Schools"
                    value={metrics?.total_schools || 0}
                    description={`${metrics?.new_schools_30d || 0} new this month`}
                    icon={Building2}
                    trend={{ value: metrics?.new_schools_30d || 0, isPositive: true }}
                />
                <StatCard
                    title="Active Users"
                    value={metrics?.total_users?.toLocaleString() || '0'}
                    description="across all schools"
                    icon={Users}
                />
                <StatCard
                    title="Daily Active Users"
                    value={metrics?.daily_active_users || 0}
                    description="users online now"
                    icon={Activity}
                />
                <StatCard
                    title="System Uptime"
                    value={metrics?.system_uptime || '99.9%'}
                    description={`${metrics?.api_response_time || '0ms'} avg response`}
                    icon={Server}
                />
            </div>

            {/* System Health */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">API Response</p>
                                <p className="text-2xl font-bold text-slate-900">{metrics?.api_response_time || '0ms'}</p>
                            </div>
                            <TrendingUp className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Error Rate</p>
                                <p className="text-2xl font-bold text-slate-900">{metrics?.error_rate || '0.00%'}</p>
                            </div>
                            <CheckCircle className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Total Students</p>
                                <p className="text-2xl font-bold text-slate-900">{metrics?.total_students?.toLocaleString() || '0'}</p>
                            </div>
                            <Users className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">MRR</p>
                                <p className="text-2xl font-bold text-slate-900">$0</p>
                            </div>
                            <DollarSign className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* System Alerts */}
            {alerts.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                            System Alerts
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {alerts.map((alert, idx) => (
                                <div key={idx} className={`p-3 rounded-lg border ${
                                    alert.severity === 'warning' ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'
                                }`}>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className={`font-medium ${
                                                alert.severity === 'warning' ? 'text-amber-800' : 'text-blue-800'
                                            }`}>{alert.message}</p>
                                            <p className="text-sm text-slate-500 mt-1">{alert.type}</p>
                                        </div>
                                        <Badge variant={alert.severity === 'warning' ? 'destructive' : 'secondary'}>
                                            {alert.severity}
                                        </Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Schools Overview */}
            <Card>
                <CardHeader>
                    <CardTitle>Schools Overview</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="table-responsive">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>School</TableHead>
                                    <TableHead>Code</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Users</TableHead>
                                    <TableHead>Students</TableHead>
                                    <TableHead>Last Active</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {schools.length > 0 ? schools.map((school) => (
                                    <TableRow key={school.id}>
                                        <TableCell className="font-medium">{school.name}</TableCell>
                                        <TableCell className="font-mono text-sm">{school.code}</TableCell>
                                        <TableCell>
                                            <Badge variant={school.status === 'Active' ? 'default' : 'secondary'}>
                                                {school.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{school.users}</TableCell>
                                        <TableCell>{school.students}</TableCell>
                                        <TableCell className="text-sm text-slate-500">{school.last_active || 'Never'}</TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-2">
                                                <Button variant="ghost" size="sm">
                                                    <Eye className="h-4 w-4" />
                                                </Button>
                                                <Button variant="ghost" size="sm">
                                                    <Ban className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                )) : (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center text-slate-500">
                                            No schools available
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            {/* Platform Activity */}
            <Card>
                <CardHeader>
                    <CardTitle>Platform Activity</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {activity.length > 0 ? activity.map((item, idx) => (
                            <div key={idx} className="flex items-start gap-3 pb-3 border-b last:border-0">
                                <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center">
                                    <Shield className="h-4 w-4 text-emerald-600" />
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm font-medium text-slate-900">{item.description}</p>
                                    <p className="text-xs text-slate-500 mt-1">{new Date(item.timestamp).toLocaleString()}</p>
                                </div>
                            </div>
                        )) : (
                            <p className="text-sm text-slate-500 text-center py-4">No recent activity</p>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Security Summary */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5 text-blue-500" />
                        Security Center
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold text-slate-900">{metrics?.failed_logins_24h || 0}</p>
                            <p className="text-sm text-slate-500 mt-1">Failed Logins (24h)</p>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold text-slate-900">{metrics?.locked_accounts || 0}</p>
                            <p className="text-sm text-slate-500 mt-1">Locked Accounts</p>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold text-slate-900">{metrics?.admin_role_changes || 0}</p>
                            <p className="text-sm text-slate-500 mt-1">Admin Role Changes</p>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-50">
                            <p className="text-2xl font-bold text-slate-900">{metrics?.suspicious_activity || 0}</p>
                            <p className="text-sm text-slate-500 mt-1">Suspicious Activity</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
