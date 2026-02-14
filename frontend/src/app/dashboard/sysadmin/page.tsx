'use client';

import { useEffect, useState } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Building2, Users, DollarSign, TrendingUp, AlertTriangle, Activity,
    Server, CheckCircle, Eye, Ban, Shield
} from 'lucide-react';

export default function SysAdminOverview() {
    const [metrics, setMetrics] = useState<any>(null);
    const [tenants, setTenants] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [overview, tenantList] = await Promise.all([
                authFetch('/api/v1/sysadmin/overview').then(r => r.json()),
                authFetch('/api/v1/sysadmin/tenants?limit=10').then(r => r.json()),
            ]);
            setMetrics(overview);
            setTenants(tenantList);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Platform Overview</h1>
                <p className="text-slate-500 mt-1">SaaS Command Center</p>
            </div>

            {/* KPI Strip */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Active Tenants</p>
                                <p className="text-2xl font-bold">{metrics?.active_tenants || 0}</p>
                                <p className="text-xs text-emerald-600 mt-1">
                                    +{metrics?.new_tenants_30d || 0} this month
                                </p>
                            </div>
                            <Building2 className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Active Users (30d)</p>
                                <p className="text-2xl font-bold">{metrics?.active_users_30d?.toLocaleString() || 0}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    of {metrics?.total_users?.toLocaleString() || 0} total
                                </p>
                            </div>
                            <Users className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">MRR / ARR</p>
                                <p className="text-2xl font-bold">${(metrics?.mrr || 0).toLocaleString()}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    ${(metrics?.arr || 0).toLocaleString()} ARR
                                </p>
                            </div>
                            <DollarSign className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">System Uptime</p>
                                <p className="text-2xl font-bold">{metrics?.system_uptime || '99.9%'}</p>
                                <p className="text-xs text-emerald-600 mt-1">
                                    {metrics?.open_incidents || 0} open incidents
                                </p>
                            </div>
                            <Server className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Tenant Health Snapshot */}
            <Card>
                <CardHeader>
                    <CardTitle>Tenant Health Snapshot</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Tenant</TableHead>
                                <TableHead>Plan</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Users</TableHead>
                                <TableHead>Students</TableHead>
                                <TableHead>Last Active</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {tenants.map((tenant) => (
                                <TableRow key={tenant.id}>
                                    <TableCell className="font-medium">{tenant.name}</TableCell>
                                    <TableCell>
                                        <Badge variant="outline" className="capitalize">
                                            {tenant.plan}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={tenant.status === 'Active' ? 'default' : 'secondary'}>
                                            {tenant.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{tenant.users}</TableCell>
                                    <TableCell>
                                        {tenant.students} / {tenant.max_students}
                                    </TableCell>
                                    <TableCell className="text-sm text-slate-500">
                                        {tenant.last_activity ? new Date(tenant.last_activity).toLocaleString() : 'Never'}
                                    </TableCell>
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
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* System Health */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Churn Rate (30d)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{metrics?.churn_rate_30d || 0}%</p>
                        <p className="text-xs text-slate-500 mt-2">Industry avg: 5-7%</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Payment Failures (7d)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{metrics?.payment_failures_7d || 0}</p>
                        <p className="text-xs text-amber-600 mt-2">Requires attention</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Open Incidents</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{metrics?.open_incidents || 0}</p>
                        <p className="text-xs text-emerald-600 mt-2">All systems operational</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
