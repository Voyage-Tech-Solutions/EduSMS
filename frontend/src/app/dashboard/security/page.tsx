'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Shield, AlertTriangle, Lock, Activity, LogOut } from 'lucide-react';

export default function SecurityPage() {
    const sessions = [
        {user: 'John Doe', school: 'Greenfield', device: 'Chrome/Windows', location: 'New York, US', session_age: '2h', ip: '192.168.1.1'},
        {user: 'Jane Smith', school: 'Riverside', device: 'Safari/Mac', location: 'London, UK', session_age: '30m', ip: '192.168.1.2'},
    ];

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Security Center</h1>
                <p className="text-slate-500 mt-1">Platform-wide security monitoring</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Failed Logins (24h)</p>
                                <p className="text-3xl font-bold text-slate-900">12</p>
                            </div>
                            <AlertTriangle className="h-8 w-8 text-amber-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Locked Accounts</p>
                                <p className="text-3xl font-bold text-slate-900">3</p>
                            </div>
                            <Lock className="h-8 w-8 text-red-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">2FA Adoption</p>
                                <p className="text-3xl font-bold text-slate-900">45%</p>
                            </div>
                            <Shield className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Active Sessions</p>
                                <p className="text-3xl font-bold text-slate-900">482</p>
                            </div>
                            <Activity className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Active Sessions Monitor</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>User</TableHead>
                                <TableHead>School</TableHead>
                                <TableHead>Device</TableHead>
                                <TableHead>Location</TableHead>
                                <TableHead>Session Age</TableHead>
                                <TableHead>IP Address</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {sessions.map((session, idx) => (
                                <TableRow key={idx}>
                                    <TableCell className="font-medium">{session.user}</TableCell>
                                    <TableCell>{session.school}</TableCell>
                                    <TableCell className="text-sm">{session.device}</TableCell>
                                    <TableCell className="text-sm">{session.location}</TableCell>
                                    <TableCell>{session.session_age}</TableCell>
                                    <TableCell className="font-mono text-sm">{session.ip}</TableCell>
                                    <TableCell>
                                        <Button variant="ghost" size="sm">
                                            <LogOut className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Authentication Health</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm">2FA Adoption (Staff)</span>
                                <span className="font-bold">68%</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Password Policy Compliance</span>
                                <span className="font-bold">92%</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">SSO Usage</span>
                                <span className="font-bold">12%</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Threat Monitoring</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
                                <p className="font-medium text-amber-800">Brute Force Attempts</p>
                                <p className="text-sm text-amber-600 mt-1">5 attempts detected in last hour</p>
                            </div>
                            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                                <p className="font-medium text-emerald-800">No High-Risk Access</p>
                                <p className="text-sm text-emerald-600 mt-1">All clear</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
