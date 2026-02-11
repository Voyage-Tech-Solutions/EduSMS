'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Plus, Eye, Mail, Phone } from 'lucide-react';
import { StatCard } from '@/components/dashboard';
import { Users, UserCheck, UserX, GraduationCap } from 'lucide-react';

export default function StaffPage() {
    const [staff, setStaff] = useState<any[]>([]);
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('all');

    useEffect(() => {
        loadStaff();
    }, []);

    const loadStaff = async () => {
        try {
            const response = await fetch('/api/v1/staff');
            const data = await response.json();
            setStaff(data);
        } catch (error) {
            console.error('Failed to load staff:', error);
            setStaff([]);
        }
    };

    const filteredStaff = staff.filter(member =>
        (member.full_name?.toLowerCase().includes(search.toLowerCase()) || 
         member.email?.toLowerCase().includes(search.toLowerCase())) &&
        (roleFilter === 'all' || member.role === roleFilter)
    );

    const stats = {
        total: staff.length,
        active: staff.filter(s => s.is_active).length,
        teachers: staff.filter(s => s.role === 'teacher').length,
        admins: staff.filter(s => s.role === 'office_admin').length,
    };

    return (
        <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Staff Management</h1>
                        <p className="text-slate-500 mt-1">Manage school staff and teachers</p>
                    </div>
                    <Button className="bg-emerald-600 hover:bg-emerald-700">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Staff
                    </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        title="Total Staff"
                        value={stats.total}
                        icon={Users}
                    />
                    <StatCard
                        title="Active"
                        value={stats.active}
                        icon={UserCheck}
                    />
                    <StatCard
                        title="Teachers"
                        value={stats.teachers}
                        icon={GraduationCap}
                    />
                    <StatCard
                        title="Admin Staff"
                        value={stats.admins}
                        icon={UserX}
                    />
                </div>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input 
                                    placeholder="Search staff..." 
                                    className="pl-10" 
                                    value={search} 
                                    onChange={(e) => setSearch(e.target.value)} 
                                />
                            </div>
                            <Select value={roleFilter} onValueChange={setRoleFilter}>
                                <SelectTrigger className="w-48">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Roles</SelectItem>
                                    <SelectItem value="principal">Principal</SelectItem>
                                    <SelectItem value="teacher">Teacher</SelectItem>
                                    <SelectItem value="office_admin">Office Admin</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>All Staff ({filteredStaff.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Phone</TableHead>
                                    <TableHead>Role</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredStaff.length > 0 ? filteredStaff.map((member) => (
                                    <TableRow key={member.id}>
                                        <TableCell className="font-medium">{member.full_name}</TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Mail className="h-4 w-4 text-slate-400" />
                                                {member.email}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Phone className="h-4 w-4 text-slate-400" />
                                                {member.phone || 'N/A'}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="secondary" className="capitalize">
                                                {member.role?.replace('_', ' ')}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge className={member.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}>
                                                {member.is_active ? 'Active' : 'Inactive'}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Button variant="ghost" size="sm">
                                                <Eye className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                )) : (
                                    <TableRow>
                                        <TableCell colSpan={6} className="text-center text-slate-500">
                                            No staff members found
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
