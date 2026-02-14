'use client';

import { useEffect, useState } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Shield, AlertTriangle, FileText, Key } from 'lucide-react';

export default function SecurityPage() {
    const [auditLogs, setAuditLogs] = useState<any[]>([]);
    const [incidents, setIncidents] = useState<any[]>([]);
    const [suspicious, setSuspicious] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [logs, incs, susp] = await Promise.all([
                authFetch('/api/v1/sysadmin/security/audit-logs?limit=50').then(r => r.json()),
                authFetch('/api/v1/sysadmin/security/incidents').then(r => r.json()),
                authFetch('/api/v1/sysadmin/security/suspicious-activity').then(r => r.json()),
            ]);
            setAuditLogs(logs);
            setIncidents(incs);
            setSuspicious(susp);
        } catch (error) {
            console.error('Failed to load security data:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Security Center</h1>
                <p className="text-slate-500 mt-1">Monitor security events and incidents</p>
            </div>

            {/* Security Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Open Incidents</p>
                                <p className="text-2xl font-bold">
                                    {incidents.filter(i => i.status === 'open').length}
                                </p>
                            </div>
                            <AlertTriangle className="h-8 w-8 text-amber-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Suspicious Activity</p>
                                <p className="text-2xl font-bold">{suspicious.length}</p>
                            </div>
                            <Shield className="h-8 w-8 text-red-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Audit Logs (24h)</p>
                                <p className="text-2xl font-bold">{auditLogs.length}</p>
                            </div>
                            <FileText className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Active API Keys</p>
                                <p className="text-2xl font-bold">0</p>
                            </div>
                            <Key className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="audit" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="audit">
                        <FileText className="h-4 w-4 mr-2" />
                        Audit Logs
                    </TabsTrigger>
                    <TabsTrigger value="incidents">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Incidents
                    </TabsTrigger>
                    <TabsTrigger value="suspicious">
                        <Shield className="h-4 w-4 mr-2" />
                        Suspicious Activity
                    </TabsTrigger>
                </TabsList>

                {/* Audit Logs */}
                <TabsContent value="audit">
                    <Card>
                        <CardHeader>
                            <CardTitle>Platform Audit Logs</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Timestamp</TableHead>
                                        <TableHead>Actor</TableHead>
                                        <TableHead>Action</TableHead>
                                        <TableHead>Target</TableHead>
                                        <TableHead>Tenant</TableHead>
                                        <TableHead>Severity</TableHead>
                                        <TableHead>IP Address</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                        </TableRow>
                                    ) : auditLogs.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center text-slate-500">
                                                No audit logs found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        auditLogs.map((log) => (
                                            <TableRow key={log.id}>
                                                <TableCell className="text-sm text-slate-500">
                                                    {new Date(log.created_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell className="font-medium">
                                                    {log.user_profiles?.first_name} {log.user_profiles?.last_name}
                                                </TableCell>
                                                <TableCell className="font-mono text-sm">{log.action}</TableCell>
                                                <TableCell className="text-sm">
                                                    {log.entity_type} ({log.entity_id?.substring(0, 8)})
                                                </TableCell>
                                                <TableCell className="text-sm">
                                                    {log.schools?.name || 'Platform'}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant={
                                                            log.severity === 'critical'
                                                                ? 'destructive'
                                                                : log.severity === 'warning'
                                                                ? 'secondary'
                                                                : 'outline'
                                                        }
                                                    >
                                                        {log.severity}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="font-mono text-xs">
                                                    {log.ip_address || 'N/A'}
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Incidents */}
                <TabsContent value="incidents">
                    <Card>
                        <CardHeader>
                            <CardTitle>Security Incidents</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Title</TableHead>
                                        <TableHead>Severity</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Detected At</TableHead>
                                        <TableHead>Affected Tenants</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                        </TableRow>
                                    ) : incidents.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center text-slate-500">
                                                No incidents found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        incidents.map((incident) => (
                                            <TableRow key={incident.id}>
                                                <TableCell className="font-mono text-sm">
                                                    {incident.incident_type}
                                                </TableCell>
                                                <TableCell className="font-medium">{incident.title}</TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant={
                                                            incident.severity === 'critical'
                                                                ? 'destructive'
                                                                : incident.severity === 'high'
                                                                ? 'destructive'
                                                                : 'secondary'
                                                        }
                                                    >
                                                        {incident.severity}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant={incident.status === 'open' ? 'destructive' : 'default'}>
                                                        {incident.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {new Date(incident.detected_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="outline">
                                                        {incident.affected_schools?.length || 0} tenants
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button variant="ghost" size="sm">
                                                        Investigate
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Suspicious Activity */}
                <TabsContent value="suspicious">
                    <Card>
                        <CardHeader>
                            <CardTitle>Suspicious Activity Detection</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <p className="text-center text-slate-500">Loading...</p>
                            ) : suspicious.length === 0 ? (
                                <div className="text-center py-8">
                                    <Shield className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
                                    <p className="text-slate-500">No suspicious activity detected</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {suspicious.map((item, idx) => (
                                        <div
                                            key={idx}
                                            className="p-4 rounded-lg border border-red-200 bg-red-50"
                                        >
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <p className="font-medium text-red-800">
                                                        {item.type.replace(/_/g, ' ').toUpperCase()}
                                                    </p>
                                                    <p className="text-sm text-red-600 mt-1">
                                                        IP: {item.ip_address} - {item.count} attempts
                                                    </p>
                                                </div>
                                                <Badge variant="destructive">{item.severity}</Badge>
                                            </div>
                                            <div className="mt-3 flex gap-2">
                                                <Button size="sm" variant="destructive">
                                                    Block IP
                                                </Button>
                                                <Button size="sm" variant="outline">
                                                    Investigate
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
