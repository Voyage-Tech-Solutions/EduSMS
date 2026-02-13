'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { StatCard } from '@/components/dashboard';
import {
    Search, Plus, Eye, CheckCircle, XCircle, Clock, UserPlus, FileText, Download, Loader2, MoreHorizontal
} from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const statusConfig: Record<string, { color: string; label: string }> = {
    incomplete: { color: 'bg-slate-100 text-slate-800', label: 'Incomplete' },
    pending: { color: 'bg-amber-100 text-amber-800', label: 'Pending' },
    under_review: { color: 'bg-blue-100 text-blue-800', label: 'Under Review' },
    approved: { color: 'bg-emerald-100 text-emerald-800', label: 'Approved' },
    enrolled: { color: 'bg-purple-100 text-purple-800', label: 'Enrolled' },
    declined: { color: 'bg-red-100 text-red-800', label: 'Declined' },
    withdrawn: { color: 'bg-slate-100 text-slate-800', label: 'Withdrawn' },
};

export default function AdmissionsPage() {
    const [applications, setApplications] = useState<any[]>([]);
    const [grades, setGrades] = useState<any[]>([]);
    const [classes, setClasses] = useState<any[]>([]);
    const [stats, setStats] = useState({ total: 0, incomplete: 0, pending: 0, under_review: 0, approved: 0, enrolled: 0 });
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [showAddDialog, setShowAddDialog] = useState(false);
    const [showEnrollDialog, setShowEnrollDialog] = useState(false);
    const [selectedApp, setSelectedApp] = useState<any>(null);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const [formData, setFormData] = useState({
        student_first_name: '', student_last_name: '', student_dob: '', gender: 'male', grade_applied_id: ''
    });

    const [enrollData, setEnrollData] = useState({ class_id: '', admission_date: '' });

    useEffect(() => {
        setEnrollData(prev => ({ ...prev, admission_date: new Date().toISOString().split('T')[0] }));
    }, []);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        loadApplications();
    }, [statusFilter]);

    const loadInitialData = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const [gradesRes, classesRes, statsRes] = await Promise.all([
                fetch(`${baseUrl}/schools/grades`, { headers }),
                fetch(`${baseUrl}/schools/classes`, { headers }),
                fetch(`${baseUrl}/admissions/stats`, { headers }),
            ]);
            if (gradesRes.ok) setGrades(await gradesRes.json());
            if (classesRes.ok) setClasses(await classesRes.json());
            if (statsRes.ok) setStats(await statsRes.json());
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
        loadApplications();
    };

    const loadApplications = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const params = new URLSearchParams();
            if (statusFilter !== 'all') params.set('status', statusFilter);
            if (search) params.set('q', search);
            const res = await fetch(`${baseUrl}/admissions?${params}`, { headers });
            if (res.ok) {
                const data = await res.json();
                setApplications(data.data || []);
            }
        } catch (error) {
            console.error('Failed to load applications:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddApplication = async () => {
        if (!formData.student_first_name || !formData.student_last_name || !formData.student_dob) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/admissions`, {
                method: 'POST',
                headers,
                body: JSON.stringify(formData)
            });
            if (res.ok) {
                setShowAddDialog(false);
                resetForm();
                setMessage({ type: 'success', text: 'Application created successfully.' });
                loadApplications();
                loadInitialData();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to create application.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const handleAction = async (appId: string, action: string, data?: any) => {
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/admissions/${appId}/${action}`, {
                method: 'POST',
                headers,
                body: data ? JSON.stringify(data) : undefined
            });
            if (res.ok) {
                setMessage({ type: 'success', text: `Application ${action} successful.` });
                loadApplications();
                loadInitialData();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || `Failed to ${action}.` });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const handleEnroll = async () => {
        if (!selectedApp || !enrollData.class_id) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/admissions/${selectedApp.id}/enroll`, {
                method: 'POST',
                headers,
                body: JSON.stringify(enrollData)
            });
            if (res.ok) {
                setShowEnrollDialog(false);
                setSelectedApp(null);
                setMessage({ type: 'success', text: 'Student enrolled successfully!' });
                loadApplications();
                loadInitialData();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to enroll student.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const resetForm = () => {
        setFormData({ student_first_name: '', student_last_name: '', student_dob: '', gender: 'male', grade_applied_id: '' });
    };

    const getGradeName = (gradeId: string) => grades.find(g => g.id === gradeId)?.name || 'N/A';
    const filteredClasses = selectedApp?.grade_applied_id ? classes.filter(c => c.grade_id === selectedApp.grade_applied_id) : classes;

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Admissions</h1>
                    <p className="text-slate-500 mt-1">Manage student applications and enrollments</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
                    <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => { resetForm(); setShowAddDialog(true); }}>
                        <Plus className="mr-2 h-4 w-4" />New Application
                    </Button>
                </div>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Total Applications" value={stats.total} description="this term" icon={FileText} />
                <StatCard title="Pending Review" value={stats.pending} description="awaiting action" icon={Clock} />
                <StatCard title="Under Review" value={stats.under_review} description="in progress" icon={Eye} />
                <StatCard title="Approved" value={stats.approved} description="ready for enrollment" icon={CheckCircle} />
            </div>

            <Card>
                <CardHeader><CardTitle>Application Pipeline</CardTitle></CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        {[
                            { label: 'Incomplete', count: stats.incomplete || 0, color: 'bg-slate-200' },
                            { label: 'Pending', count: stats.pending, color: 'bg-amber-200' },
                            { label: 'Under Review', count: stats.under_review, color: 'bg-blue-200' },
                            { label: 'Approved', count: stats.approved, color: 'bg-emerald-200' },
                            { label: 'Enrolled', count: stats.enrolled, color: 'bg-purple-200' },
                        ].map((stage, index) => (
                            <div key={stage.label} className="flex items-center">
                                <div className="text-center cursor-pointer" onClick={() => setStatusFilter(stage.label.toLowerCase().replace(' ', '_'))}>
                                    <div className={`w-16 h-16 rounded-full ${stage.color} flex items-center justify-center text-xl font-bold hover:ring-2 ring-slate-400`}>
                                        {stage.count}
                                    </div>
                                    <p className="text-sm text-slate-600 mt-2">{stage.label}</p>
                                </div>
                                {index < 4 && <div className="w-12 h-0.5 bg-slate-200 mx-2" />}
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input placeholder="Search by student name, application number..." className="pl-10"
                                value={search} onChange={e => setSearch(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && loadApplications()} />
                        </div>
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                {Object.entries(statusConfig).map(([key, val]) => (
                                    <SelectItem key={key} value={key}>{val.label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>Applications <Badge variant="secondary" className="ml-2">{applications.length}</Badge></CardTitle></CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Application #</TableHead>
                                <TableHead>Student</TableHead>
                                <TableHead>Grade Applied</TableHead>
                                <TableHead>Date</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {applications.length > 0 ? applications.map(app => (
                                <TableRow key={app.id}>
                                    <TableCell className="font-mono text-sm">{app.application_no}</TableCell>
                                    <TableCell className="font-medium">{app.student_first_name} {app.student_last_name}</TableCell>
                                    <TableCell>{getGradeName(app.grade_applied_id)}</TableCell>
                                    <TableCell>{new Date(app.created_at).toLocaleDateString()}</TableCell>
                                    <TableCell>
                                        <Badge variant="secondary" className={statusConfig[app.status]?.color}>
                                            {statusConfig[app.status]?.label}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                {app.status === 'pending' && (
                                                    <DropdownMenuItem onClick={() => handleAction(app.id, 'start-review')}>
                                                        <Eye className="mr-2 h-4 w-4" />Start Review
                                                    </DropdownMenuItem>
                                                )}
                                                {app.status === 'under_review' && (
                                                    <>
                                                        <DropdownMenuItem className="text-emerald-600" onClick={() => handleAction(app.id, 'approve', {})}>
                                                            <CheckCircle className="mr-2 h-4 w-4" />Approve
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem className="text-red-600" onClick={() => handleAction(app.id, 'decline', { reason: 'Not meeting requirements' })}>
                                                            <XCircle className="mr-2 h-4 w-4" />Decline
                                                        </DropdownMenuItem>
                                                    </>
                                                )}
                                                {app.status === 'approved' && (
                                                    <DropdownMenuItem onClick={() => { setSelectedApp(app); setShowEnrollDialog(true); }}>
                                                        <UserPlus className="mr-2 h-4 w-4" />Enroll Student
                                                    </DropdownMenuItem>
                                                )}
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center text-slate-500 py-8">
                                        No applications found.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Add Application Dialog */}
            <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>New Application</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>First Name *</Label>
                                <Input value={formData.student_first_name} onChange={e => setFormData({ ...formData, student_first_name: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                                <Label>Last Name *</Label>
                                <Input value={formData.student_last_name} onChange={e => setFormData({ ...formData, student_last_name: e.target.value })} />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Date of Birth *</Label>
                                <Input type="date" value={formData.student_dob} onChange={e => setFormData({ ...formData, student_dob: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                                <Label>Gender</Label>
                                <Select value={formData.gender} onValueChange={v => setFormData({ ...formData, gender: v })}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="male">Male</SelectItem>
                                        <SelectItem value="female">Female</SelectItem>
                                        <SelectItem value="other">Other</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Grade Applied</Label>
                            <Select value={formData.grade_applied_id} onValueChange={v => setFormData({ ...formData, grade_applied_id: v })}>
                                <SelectTrigger><SelectValue placeholder="Select grade" /></SelectTrigger>
                                <SelectContent>
                                    {grades.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
                        <Button onClick={handleAddApplication} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Creating...' : 'Create Application'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Enroll Student Dialog */}
            <Dialog open={showEnrollDialog} onOpenChange={setShowEnrollDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Enroll Student</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-50 rounded-lg">
                            <p className="text-sm text-slate-600">Student: <strong>{selectedApp?.student_first_name} {selectedApp?.student_last_name}</strong></p>
                            <p className="text-sm text-slate-600">Grade: <strong>{getGradeName(selectedApp?.grade_applied_id)}</strong></p>
                        </div>
                        <div className="space-y-2">
                            <Label>Assign Class *</Label>
                            <Select value={enrollData.class_id} onValueChange={v => setEnrollData({ ...enrollData, class_id: v })}>
                                <SelectTrigger><SelectValue placeholder="Select class" /></SelectTrigger>
                                <SelectContent>
                                    {filteredClasses.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Admission Date</Label>
                            <Input type="date" value={enrollData.admission_date} onChange={e => setEnrollData({ ...enrollData, admission_date: e.target.value })} />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowEnrollDialog(false)}>Cancel</Button>
                        <Button onClick={handleEnroll} disabled={saving || !enrollData.class_id} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Enrolling...' : 'Enroll Student'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
