'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { StatCard } from '@/components/dashboard';
import { AddStudentDialog } from '@/components/dialogs/add-student-dialog';
import { Label } from '@/components/ui/label';
import {
    Search, Plus, Edit, Trash2, Users, UserPlus, UserMinus, ArrowLeftRight,
    Loader2, ChevronLeft, ChevronRight, FileText, Eye,
} from 'lucide-react';

interface Student {
    id: string;
    admission_number: string;
    first_name: string;
    last_name: string;
    date_of_birth: string;
    gender: string;
    grade_id: string;
    class_id: string;
    status: string;
    created_at: string;
}

interface Grade {
    id: string;
    name: string;
    order: number;
}

interface ClassItem {
    id: string;
    name: string;
    grade_id: string;
}

const statusColors: Record<string, string> = {
    active: 'bg-emerald-100 text-emerald-800 hover:bg-emerald-100',
    inactive: 'bg-slate-100 text-slate-800 hover:bg-slate-100',
    transferred: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
    graduated: 'bg-purple-100 text-purple-800 hover:bg-purple-100',
};

export default function StudentsPage() {
    const [students, setStudents] = useState<Student[]>([]);
    const [grades, setGrades] = useState<Grade[]>([]);
    const [classes, setClasses] = useState<ClassItem[]>([]);
    const [search, setSearch] = useState('');
    const [gradeFilter, setGradeFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [showAddDialog, setShowAddDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [editingStudent, setEditingStudent] = useState<Student | null>(null);
    const [deletingStudent, setDeletingStudent] = useState<Student | null>(null);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [page, setPage] = useState(0);
    const pageSize = 50;

    const [formData, setFormData] = useState({
        first_name: '', last_name: '', date_of_birth: '', gender: 'male',
        grade_id: '', class_id: '', status: 'active',
    });

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
        loadStudents();
    }, [gradeFilter, statusFilter, page]);

    const loadInitialData = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const [gradesRes, classesRes] = await Promise.all([
                fetch(`${baseUrl}/schools/grades`, { headers }),
                fetch(`${baseUrl}/schools/classes`, { headers }),
            ]);
            if (gradesRes.ok) setGrades(await gradesRes.json());
            if (classesRes.ok) setClasses(await classesRes.json());
        } catch (error) {
            console.error('Failed to load grades/classes:', error);
        }
        loadStudents();
    };

    const loadStudents = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const params = new URLSearchParams({ skip: String(page * pageSize), limit: String(pageSize) });
            if (gradeFilter !== 'all') params.set('grade_id', gradeFilter);
            if (statusFilter !== 'all') params.set('status', statusFilter);
            if (search) params.set('search', search);
            const res = await fetch(`${baseUrl}/students?${params}`, { headers });
            if (res.ok) setStudents(await res.json());
        } catch (error) {
            console.error('Failed to load students:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = () => {
        setPage(0);
        loadStudents();
    };

    const handleAddStudent = async () => {
        if (!formData.first_name || !formData.last_name || !formData.date_of_birth) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const body: any = {
                first_name: formData.first_name,
                last_name: formData.last_name,
                date_of_birth: formData.date_of_birth,
                gender: formData.gender,
            };
            if (formData.grade_id) body.grade_id = formData.grade_id;
            if (formData.class_id) body.class_id = formData.class_id;
            const res = await fetch(`${baseUrl}/students`, { method: 'POST', headers, body: JSON.stringify(body) });
            if (res.ok) {
                setShowAddDialog(false);
                resetForm();
                setMessage({ type: 'success', text: 'Student added successfully.' });
                loadStudents();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to add student.' });
            }
        } catch { setMessage({ type: 'error', text: 'Network error.' }); }
        finally { setSaving(false); setTimeout(() => setMessage(null), 4000); }
    };

    const handleEditStudent = async () => {
        if (!editingStudent) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const body: any = {
                first_name: formData.first_name,
                last_name: formData.last_name,
                date_of_birth: formData.date_of_birth,
                gender: formData.gender,
                status: formData.status,
            };
            if (formData.grade_id) body.grade_id = formData.grade_id;
            if (formData.class_id) body.class_id = formData.class_id;
            const res = await fetch(`${baseUrl}/students/${editingStudent.id}`, { method: 'PATCH', headers, body: JSON.stringify(body) });
            if (res.ok) {
                setShowEditDialog(false);
                setMessage({ type: 'success', text: 'Student updated successfully.' });
                loadStudents();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to update student.' });
            }
        } catch { setMessage({ type: 'error', text: 'Network error.' }); }
        finally { setSaving(false); setTimeout(() => setMessage(null), 4000); }
    };

    const handleDeleteStudent = async () => {
        if (!deletingStudent) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/students/${deletingStudent.id}`, { method: 'DELETE', headers });
            if (res.ok) {
                setShowDeleteDialog(false);
                setDeletingStudent(null);
                setMessage({ type: 'success', text: 'Student removed successfully.' });
                loadStudents();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to delete student.' });
            }
        } catch { setMessage({ type: 'error', text: 'Network error.' }); }
        finally { setSaving(false); setTimeout(() => setMessage(null), 4000); }
    };

    const openEdit = (student: Student) => {
        setEditingStudent(student);
        setFormData({
            first_name: student.first_name, last_name: student.last_name,
            date_of_birth: student.date_of_birth?.split('T')[0] || '',
            gender: student.gender, grade_id: student.grade_id || '',
            class_id: student.class_id || '', status: student.status,
        });
        setShowEditDialog(true);
    };

    const resetForm = () => {
        setFormData({ first_name: '', last_name: '', date_of_birth: '', gender: 'male', grade_id: '', class_id: '', status: 'active' });
    };

    const getGradeName = (gradeId: string) => grades.find(g => g.id === gradeId)?.name || 'N/A';
    const getClassName = (classId: string) => classes.find(c => c.id === classId)?.name || 'N/A';
    const filteredClasses = formData.grade_id ? classes.filter(c => c.grade_id === formData.grade_id) : classes;

    const filteredStudents = students.filter(s => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (
            `${s.first_name} ${s.last_name}`.toLowerCase().includes(q) ||
            s.admission_number?.toLowerCase().includes(q)
        );
    });

    const stats = {
        active: students.filter(s => s.status === 'active').length,
        newThisMonth: students.filter(s => {
            const created = new Date(s.created_at);
            const now = new Date();
            return created.getMonth() === now.getMonth() && created.getFullYear() === now.getFullYear();
        }).length,
        transferred: students.filter(s => s.status === 'transferred').length,
        inactive: students.filter(s => s.status === 'inactive' || s.status === 'graduated').length,
    };

    const recentActivity = students
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5);

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    const StudentFormFields = ({ isEdit = false }: { isEdit?: boolean }) => (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label>First Name *</Label>
                    <Input value={formData.first_name} onChange={e => setFormData({ ...formData, first_name: e.target.value })} />
                </div>
                <div className="space-y-2">
                    <Label>Last Name *</Label>
                    <Input value={formData.last_name} onChange={e => setFormData({ ...formData, last_name: e.target.value })} />
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label>Date of Birth *</Label>
                    <Input type="date" value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })} />
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
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label>Grade</Label>
                    <Select value={formData.grade_id} onValueChange={v => setFormData({ ...formData, grade_id: v, class_id: '' })}>
                        <SelectTrigger><SelectValue placeholder="Select grade" /></SelectTrigger>
                        <SelectContent>
                            {grades.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
                <div className="space-y-2">
                    <Label>Class</Label>
                    <Select value={formData.class_id} onValueChange={v => setFormData({ ...formData, class_id: v })}>
                        <SelectTrigger><SelectValue placeholder="Select class" /></SelectTrigger>
                        <SelectContent>
                            {filteredClasses.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
            </div>
            {isEdit && (
                <div className="space-y-2">
                    <Label>Status</Label>
                    <Select value={formData.status} onValueChange={v => setFormData({ ...formData, status: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="active">Active</SelectItem>
                            <SelectItem value="inactive">Inactive</SelectItem>
                            <SelectItem value="transferred">Transferred</SelectItem>
                            <SelectItem value="graduated">Graduated</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            )}
        </div>
    );

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Student Administration Overview</h1>
                <p className="text-slate-500 mt-1">Current student status and recent activity</p>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard 
                    title="Active Students" 
                    value={stats.active} 
                    icon={Users}
                    description="Currently enrolled and active"
                />
                <StatCard 
                    title="New Admissions (This Month)" 
                    value={stats.newThisMonth} 
                    icon={UserPlus}
                    description="Students enrolled this month"
                />
                <StatCard 
                    title="Pending Transfers" 
                    value={stats.transferred} 
                    icon={ArrowLeftRight}
                    description="Awaiting approval or processing"
                />
                <StatCard 
                    title="Inactive Students" 
                    value={stats.inactive} 
                    icon={UserMinus}
                    description="Withdrawn, graduated, or suspended"
                />
            </div>

            <div className="flex gap-3">
                <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => { resetForm(); setShowAddDialog(true); }}>
                    <Plus className="mr-2 h-4 w-4" /> Add Student
                </Button>
                <Button variant="outline" onClick={() => setStatusFilter('transferred')}>
                    <ArrowLeftRight className="mr-2 h-4 w-4" /> Manage Transfers
                </Button>
                <Button variant="outline" onClick={() => setStatusFilter('all')}>
                    <FileText className="mr-2 h-4 w-4" /> View Student Directory
                </Button>
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input placeholder="Search by name or admission number..." className="pl-10"
                                value={search} onChange={e => setSearch(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleSearch()} />
                        </div>
                        <Select value={gradeFilter} onValueChange={v => { setGradeFilter(v); setPage(0); }}>
                            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Grades</SelectItem>
                                {grades.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
                            </SelectContent>
                        </Select>
                        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(0); }}>
                            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                <SelectItem value="active">Active</SelectItem>
                                <SelectItem value="inactive">Inactive</SelectItem>
                                <SelectItem value="transferred">Transferred</SelectItem>
                                <SelectItem value="graduated">Graduated</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Recent Student Activity</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Student</TableHead>
                                <TableHead>Action</TableHead>
                                <TableHead>Date</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {recentActivity.length > 0 ? recentActivity.map(student => (
                                <TableRow key={student.id}>
                                    <TableCell className="font-medium">{student.first_name} {student.last_name}</TableCell>
                                    <TableCell>
                                        {new Date(student.created_at).getTime() > Date.now() - 7 * 24 * 60 * 60 * 1000 
                                            ? 'Admitted' 
                                            : student.status === 'transferred' 
                                            ? 'Transfer Requested' 
                                            : 'Status Changed'}
                                    </TableCell>
                                    <TableCell>{new Date(student.created_at).toLocaleDateString()}</TableCell>
                                    <TableCell>
                                        <Badge className={statusColors[student.status] || 'bg-slate-100 text-slate-800'}>
                                            {student.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Button variant="ghost" size="sm" onClick={() => openEdit(student)}>
                                            <Eye className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-slate-500 py-8">
                                        No recent activity.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Student Directory ({filteredStudents.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Admission #</TableHead>
                                <TableHead>Name</TableHead>
                                <TableHead>Grade</TableHead>
                                <TableHead>Class</TableHead>
                                <TableHead>Gender</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredStudents.length > 0 ? filteredStudents.map(student => (
                                <TableRow key={student.id}>
                                    <TableCell className="font-mono text-sm">{student.admission_number}</TableCell>
                                    <TableCell className="font-medium">{student.first_name} {student.last_name}</TableCell>
                                    <TableCell>{getGradeName(student.grade_id)}</TableCell>
                                    <TableCell>{getClassName(student.class_id)}</TableCell>
                                    <TableCell className="capitalize">{student.gender}</TableCell>
                                    <TableCell>
                                        <Badge className={statusColors[student.status] || 'bg-slate-100 text-slate-800'}>
                                            {student.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-1">
                                            <Button variant="ghost" size="sm" onClick={() => openEdit(student)}>
                                                <Edit className="h-4 w-4" />
                                            </Button>
                                            <Button variant="ghost" size="sm" onClick={() => { setDeletingStudent(student); setShowDeleteDialog(true); }}>
                                                <Trash2 className="h-4 w-4 text-red-500" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-slate-500 py-8">
                                        No students found.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>

                    {students.length >= pageSize && (
                        <div className="flex items-center justify-between mt-4 pt-4 border-t">
                            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
                                <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                            </Button>
                            <span className="text-sm text-slate-500">Page {page + 1}</span>
                            <Button variant="outline" size="sm" disabled={students.length < pageSize} onClick={() => setPage(p => p + 1)}>
                                Next <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Add Student Dialog */}
            <AddStudentDialog 
                open={showAddDialog} 
                onOpenChange={setShowAddDialog}
                onSubmit={async (data) => {
                    setSaving(true);
                    try {
                        const headers = await getHeaders();
                        if (!headers) return;
                        const res = await fetch(`${baseUrl}/students`, { method: 'POST', headers, body: JSON.stringify(data) });
                        if (res.ok) {
                            setShowAddDialog(false);
                            setMessage({ type: 'success', text: 'Student added successfully.' });
                            loadStudents();
                        } else {
                            const err = await res.json().catch(() => ({}));
                            setMessage({ type: 'error', text: err.detail || 'Failed to add student.' });
                        }
                    } catch { setMessage({ type: 'error', text: 'Network error.' }); }
                    finally { setSaving(false); setTimeout(() => setMessage(null), 4000); }
                }}
            />

            {/* Edit Student Dialog */}
            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Edit Student</DialogTitle></DialogHeader>
                    <StudentFormFields isEdit />
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
                        <Button onClick={handleEditStudent} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Delete Student</DialogTitle></DialogHeader>
                    <p className="text-slate-600">
                        Are you sure you want to remove <strong>{deletingStudent?.first_name} {deletingStudent?.last_name}</strong> ({deletingStudent?.admission_number})?
                        This will deactivate the student record.
                    </p>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
                        <Button variant="destructive" onClick={handleDeleteStudent} disabled={saving}>
                            {saving ? 'Deleting...' : 'Delete'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
