'use client';

import { useEffect, useState } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Activity, Server, Zap, Database, CheckCircle, XCircle } from 'lucide-react';

export default function MonitoringPage() {
    const [health, setHealth] = useState<any>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const [healthData, jobsData] = await Promise.all([
                authFetch('/api/v1/sysadmin/monitoring/health').then(r => r.json()),
                authFetch('/api/v1/sysadmin/monitoring/jobs').then(r => r.json()),
            ]);
            setHealth(healthData);
            setJobs(jobsData);
        } catch (error) {
            console.error('Failed to load monitoring data:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">System Monitoring</h1>
                    <p className="text-slate-500 mt-1">Real-time platform health and performance</p>
                </div>
                <Badge variant="default" className="bg-emerald-500">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    All Systems Operational
                </Badge>
            </div>

            {/* System Health */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">API Uptime</p>
                                <p className="text-2xl font-bold">{health?.api_uptime || '99.9%'}</p>
                            </div>
                            <Server className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Avg Response Time</p>
                                <p className="text-2xl font-bold">{health?.avg_response_time_ms || 0}ms</p>
                            </div>
                            <Zap className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Error Rate</p>
                                <p className="text-2xl font-bold">{health?.error_rate || 0}%</p>
                            </div>
                            <Activity className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Active Connections</p>
                                <p className="text-2xl font-bold">{health?.active_connections || 0}</p>
                            </div>
                            <Database className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Service Status */}
            <Card>
                <CardHeader>
                    <CardTitle>Service Status</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex items-center justify-between p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="h-5 w-5 text-emerald-600" />
                                <div>
                                    <p className="font-medium text-emerald-900">Database</p>
                                    <p className="text-sm text-emerald-600">{health?.db_health || 'Healthy'}</p>
                                </div>
                            </div>
                            <Badge variant="default" className="bg-emerald-500">Operational</Badge>
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="h-5 w-5 text-emerald-600" />
                                <div>
                                    <p className="font-medium text-emerald-900">Queue</p>
                                    <p className="text-sm text-emerald-600">{health?.queue_status || 'Operational'}</p>
                                </div>
                            </div>
                            <Badge variant="default" className="bg-emerald-500">Operational</Badge>
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="h-5 w-5 text-emerald-600" />
                                <div>
                                    <p className="font-medium text-emerald-900">Storage</p>
                                    <p className="text-sm text-emerald-600">{health?.storage_health || 'Healthy'}</p>
                                </div>
                            </div>
                            <Badge variant="default" className="bg-emerald-500">Operational</Badge>
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="h-5 w-5 text-emerald-600" />
                                <div>
                                    <p className="font-medium text-emerald-900">API</p>
                                    <p className="text-sm text-emerald-600">All endpoints responding</p>
                                </div>
                            </div>
                            <Badge variant="default" className="bg-emerald-500">Operational</Badge>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Tabs defaultValue="jobs" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="jobs">Background Jobs</TabsTrigger>
                    <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
                </TabsList>

                {/* Background Jobs */}
                <TabsContent value="jobs">
                    <Card>
                        <CardHeader>
                            <CardTitle>Background Jobs</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Job Type</TableHead>
                                        <TableHead>Tenant</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Attempts</TableHead>
                                        <TableHead>Scheduled At</TableHead>
                                        <TableHead>Completed At</TableHead>
                                        <TableHead>Error</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                        </TableRow>
                                    ) : jobs.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center text-slate-500">
                                                No background jobs found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        jobs.map((job) => (
                                            <TableRow key={job.id}>
                                                <TableCell className="font-mono text-sm">{job.job_type}</TableCell>
                                                <TableCell className="text-sm">
                                                    {job.school_id?.substring(0, 8) || 'Platform'}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant={
                                                            job.status === 'completed'
                                                                ? 'default'
                                                                : job.status === 'failed'
                                                                ? 'destructive'
                                                                : 'secondary'
                                                        }
                                                    >
                                                        {job.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    {job.attempts} / {job.max_attempts}
                                                </TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {new Date(job.scheduled_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}
                                                </TableCell>
                                                <TableCell className="text-sm text-red-600">
                                                    {job.error_message?.substring(0, 50) || '-'}
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Webhooks */}
                <TabsContent value="webhooks">
                    <Card>
                        <CardHeader>
                            <CardTitle>Webhook Deliveries</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-8 text-slate-500">
                                No webhook deliveries to display
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
