'use client';

import React, { useState, useEffect } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Eye, Lock, Unlock, Shield } from 'lucide-react';
import { AddUserDialog } from '@/components/forms/add-user-dialog';

export default function UsersPage() {
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('all');
    const [users, setUsers] = useState<any[]>([]);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const response = await authFetch('/api/v1/system/users');
            const data = await response.json();
            setUsers(data);
        } catch (error) {
            console.error('Failed to load users:', error);
            setUsers([]);
        }
    };

    const filteredUsers = users.filter(user =>
        (user.full_name?.toLowerCase().includes(search.toLowerCase()) || user.email?.toLowerCase().includes(search.toLowerCase())) &&
        (roleFilter === 'all' || user.role === roleFilter)
    );

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Global Users</h1>
                    <p className="text-slate-500 mt-1">Manage all users across the platform</p>
                </div>
                <AddUserDialog onUserAdded={loadUsers} />
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input placeholder="Search users..." className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
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
                    <CardTitle>All Users ({filteredUsers.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Name</TableHead>
                                <TableHead>Email</TableHead>
                                <TableHead>Role</TableHead>
                                <TableHead>School</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Last Login</TableHead>
                                <TableHead>2FA</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredUsers.length > 0 ? filteredUsers.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell className="font-medium">{user.full_name}</TableCell>
                                    <TableCell>{user.email}</TableCell>
                                    <TableCell><Badge variant="secondary" className="capitalize">{user.role?.replace('_', ' ')}</Badge></TableCell>
                                    <TableCell>{user.school_name || 'N/A'}</TableCell>
                                    <TableCell>
                                        <Badge className={user.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}>
                                            {user.is_active ? 'Active' : 'Locked'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-sm text-slate-500">{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</TableCell>
                                    <TableCell>
                                        {user.two_fa_enabled ? <Shield className="h-4 w-4 text-emerald-500" /> : <span className="text-slate-400">-</span>}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                                            <Button variant="ghost" size="sm">{user.is_active ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}</Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow>
                                    <TableCell colSpan={8} className="text-center text-slate-500">
                                        No users found
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
