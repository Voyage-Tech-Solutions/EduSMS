'use client';

import React, { useState, useEffect } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Plus, Eye, Ban, CheckCircle, TrendingUp, AlertTriangle } from 'lucide-react';
import { AddSchoolDialog } from '@/components/forms/add-school-dialog';

export default function SchoolsPage() {
    const [schools, setSchools] = useState<any[]>([]);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    useEffect(() => {
        loadSchools();
    }, []);

    const loadSchools = async () => {
        try {
            const response = await authFetch('/api/v1/system/schools');
            const data = await response.json();
            setSchools(data);
        } catch (error) {
            console.error('Failed to load schools:', error);
            setSchools([]);
        }
    };

    const filteredSchools = schools.filter(school =>
        school.name.toLowerCase().includes(search.toLowerCase())
    );

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Active': return 'bg-emerald-100 text-emerald-800';
            case 'Trial': return 'bg-blue-100 text-blue-800';
            case 'Suspended': return 'bg-red-100 text-red-800';
            default: return 'bg-slate-100 text-slate-800';
        }
    };

    return (
        <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Schools Management</h1>
                        <p className="text-slate-500 mt-1">Manage all tenant schools</p>
                    </div>
                    <AddSchoolDialog onSchoolAdded={loadSchools} />
                </div>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input placeholder="Search schools..." className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-48">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="trial">Trial</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>All Schools ({filteredSchools.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>School</TableHead>
                                    <TableHead>Plan</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Users</TableHead>
                                    <TableHead>Students</TableHead>
                                    <TableHead>Storage</TableHead>
                                    <TableHead>Health</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredSchools.length > 0 ? filteredSchools.map((school) => (
                                    <TableRow key={school.id}>
                                        <TableCell>
                                            <div className="font-medium">{school.name}</div>
                                            <div className="text-sm text-slate-500">{school.code}</div>
                                        </TableCell>
                                        <TableCell><Badge variant="secondary">{school.plan}</Badge></TableCell>
                                        <TableCell><Badge className={getStatusColor(school.status)}>{school.status}</Badge></TableCell>
                                        <TableCell>{school.users}</TableCell>
                                        <TableCell>{school.students}</TableCell>
                                        <TableCell>{school.storage_used}</TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                {school.health === 'Healthy' ? <CheckCircle className="h-4 w-4 text-emerald-500" /> : <AlertTriangle className="h-4 w-4 text-amber-500" />}
                                                <span className="text-sm">{school.health}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex gap-2">
                                                <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                                                <Button variant="ghost" size="sm"><Ban className="h-4 w-4" /></Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                )) : (
                                    <TableRow>
                                        <TableCell colSpan={8} className="text-center text-slate-500">
                                            No schools found
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
        </div>
    );
}
