'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { StatCard } from '@/components/dashboard';
import { Search, Plus, Mail, Phone, Users, UserCheck, GraduationCap, Shield, Loader2, Edit, Power } from 'lucide-react';

interface StaffMember {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
    phone: string;
    role: string;
    is_active: boolean;
    created_at: string;
}

export default function StaffPage() {
    const [staff, setStaff] = useState<StaffMember[]>([]);
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [showAddDialog, setShowAddDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [editingStaff, setEditingStaff] = useState<StaffMember | null>(null);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const [formData, setFormData] = useState({
        first_name: '', last_name: '', email: '', phone: '', role: 'teacher', password: '',
    });

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => { loadStaff(); }, []);

    const loadStaff = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const res = await fetch(`${baseUrl}/principal/staff`, { headers });
            if (res.ok) setStaff(await res.json());
        } catch (error) {
            console.error('Failed to load staff:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddStaff = async () => {
        if (!formData.email || !formData.first_name || !formData.last_name) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/principal/staff`, {
                method: 'POST', headers,
                body: JSON.stringify({ ...formData, password: formData.password || 'Welcome123!' }),
            });
            if (res.ok) {
                setShowAddDialog(false);
                setFormData({ first_name: '', last_name: '', email: '', phone: '', role: 'teacher', password: '' });
                setMessage({ type: 'success', text: 'Staff member added successfully.' });
                loadStaff();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to add staff member.' });
            }
        } catch { setMessage({ type: 'error', text: 'Network error.' }); }
        finally { setSaving(false); setTimeout(() => setMessage(null), 4000); }
    };

    const handleEditStaff = async () => {
        if (!editingStaff) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/principal/staff/${editingStaff.id}`, {
                method: 'PATCH', headers,
                body: JSON.stringify({
                    first_name: formData.first_name,
                    last_name: formData.last_name,
                    phone: formData.phone,
                    role: formData.role,
                }),
            });
            if (res.ok) {
                setShowEditDialog(false);
                setMessage({ type: 'success', text: 'Staff member updated.' });
                loadStaff();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to update.' });
            }
        } catch { setMessage({ type: 'error', text: 'Network error.' }); }
        finally { setSaving(false); setTimeout(() => setMessage(null), 4000); }
    };

    const handleToggleActive = async (member: StaffMember) => {
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/principal/staff/${member.id}/deactivate`, { method: 'POST', headers });
            if (res.ok) {
                setMessage({ type: 'success', text: `Staff member ${member.is_active ? 'deactivated' : 'activated'}.` });
                loadStaff();
            }
        } catch { /* ignore */ }
        finally { setTimeout(() => setMessage(null), 4000); }
    };

    const openEdit = (member: StaffMember) => {
        setEditingStaff(member);
        setFormData({ first_name: member.first_name, last_name: member.last_name, email: member.email, phone: member.phone, role: member.role, password: '' });
        setShowEditDialog(true);
    };

    const filteredStaff = staff.filter(m =>
        (m.full_name?.toLowerCase().includes(search.toLowerCase()) || m.email?.toLowerCase().includes(search.toLowerCase())) &&
        (roleFilter === 'all' || m.role === roleFilter)
    );

    const stats = {
        total: staff.length,
        active: staff.filter(s => s.is_active).length,
        teachers: staff.filter(s => s.role === 'teacher').length,
        admins: staff.filter(s => s.role === 'office_admin').length,
    };

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Staff Management</h1>
                    <p className="text-slate-500 mt-1">Manage school staff and teachers</p>
                </div>
                <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => {
                    setFormData({ first_name: '', last_name: '', email: '', phone: '', role: 'teacher', password: '' });
                    setShowAddDialog(true);
                }}>
                    <Plus className="mr-2 h-4 w-4" /> Add Staff
                </Button>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Total Staff" value={stats.total} icon={Users} />
                <StatCard title="Active" value={stats.active} icon={UserCheck} />
                <StatCard title="Teachers" value={stats.teachers} icon={GraduationCap} />
                <StatCard title="Admin Staff" value={stats.admins} icon={Shield} />
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input placeholder="Search staff..." className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
                        </div>
                        <Select value={roleFilter} onValueChange={setRoleFilter}>
                            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
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
                <CardHeader><CardTitle>All Staff ({filteredStaff.length})</CardTitle></CardHeader>
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
                                    <TableCell><div className="flex items-center gap-2"><Mail className="h-4 w-4 text-slate-400" />{member.email}</div></TableCell>
                                    <TableCell><div className="flex items-center gap-2"><Phone className="h-4 w-4 text-slate-400" />{member.phone || 'N/A'}</div></TableCell>
                                    <TableCell><Badge variant="secondary" className="capitalize">{member.role?.replace('_', ' ')}</Badge></TableCell>
                                    <TableCell>
                                        <Badge className={member.is_active ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-100' : 'bg-red-100 text-red-800 hover:bg-red-100'}>
                                            {member.is_active ? 'Active' : 'Inactive'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-1">
                                            <Button variant="ghost" size="sm" onClick={() => openEdit(member)}><Edit className="h-4 w-4" /></Button>
                                            <Button variant="ghost" size="sm" onClick={() => handleToggleActive(member)}>
                                                <Power className={`h-4 w-4 ${member.is_active ? 'text-red-500' : 'text-emerald-500'}`} />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow><TableCell colSpan={6} className="text-center text-slate-500 py-8">No staff members found.</TableCell></TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Add Staff Dialog */}
            <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Add Staff Member</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2"><Label>First Name</Label><Input value={formData.first_name} onChange={e => setFormData({ ...formData, first_name: e.target.value })} /></div>
                            <div className="space-y-2"><Label>Last Name</Label><Input value={formData.last_name} onChange={e => setFormData({ ...formData, last_name: e.target.value })} /></div>
                        </div>
                        <div className="space-y-2"><Label>Email</Label><Input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} /></div>
                        <div className="space-y-2"><Label>Phone</Label><Input value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} /></div>
                        <div className="space-y-2">
                            <Label>Role</Label>
                            <Select value={formData.role} onValueChange={v => setFormData({ ...formData, role: v })}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="teacher">Teacher</SelectItem>
                                    <SelectItem value="office_admin">Office Admin</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2"><Label>Password</Label><Input type="password" placeholder="Default: Welcome123!" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} /></div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
                        <Button onClick={handleAddStaff} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Adding...' : 'Add Staff'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Edit Staff Dialog */}
            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Edit Staff Member</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2"><Label>First Name</Label><Input value={formData.first_name} onChange={e => setFormData({ ...formData, first_name: e.target.value })} /></div>
                            <div className="space-y-2"><Label>Last Name</Label><Input value={formData.last_name} onChange={e => setFormData({ ...formData, last_name: e.target.value })} /></div>
                        </div>
                        <div className="space-y-2"><Label>Phone</Label><Input value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} /></div>
                        <div className="space-y-2">
                            <Label>Role</Label>
                            <Select value={formData.role} onValueChange={v => setFormData({ ...formData, role: v })}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="teacher">Teacher</SelectItem>
                                    <SelectItem value="office_admin">Office Admin</SelectItem>
                                    <SelectItem value="principal">Principal</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
                        <Button onClick={handleEditStaff} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
