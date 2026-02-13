'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
    Card, CardContent, CardHeader, CardTitle, CardDescription,
} from '@/components/ui/card';
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { StatCard } from '@/components/dashboard';
import {
    CalendarCheck, Users, AlertTriangle, Clock, Save, ChevronLeft, ChevronRight, CheckCircle, Loader2,
} from 'lucide-react';

type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused';

const statusConfig: Record<AttendanceStatus, { color: string; label: string }> = {
    present: { color: 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200', label: 'Present' },
    absent: { color: 'bg-red-100 text-red-800 hover:bg-red-200', label: 'Absent' },
    late: { color: 'bg-amber-100 text-amber-800 hover:bg-amber-200', label: 'Late' },
    excused: { color: 'bg-blue-100 text-blue-800 hover:bg-blue-200', label: 'Excused' },
};

export default function AttendancePage() {
    const [selectedClass, setSelectedClass] = useState('');
    const [selectedDate, setSelectedDate] = useState('');

    useEffect(() => {
        setSelectedDate(new Date().toISOString().split('T')[0]);
    }, []);
    const [students, setStudents] = useState<any[]>([]);
    const [classes, setClasses] = useState<any[]>([]);
    const [attendance, setAttendance] = useState<Record<string, AttendanceStatus>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [existingRecords, setExistingRecords] = useState(false);

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    useEffect(() => {
        loadClasses();
    }, []);

    useEffect(() => {
        if (selectedClass) {
            loadStudentsAndAttendance();
        }
    }, [selectedClass, selectedDate]);

    const loadClasses = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const res = await fetch(`${baseUrl}/schools/classes`, { headers });
            if (res.ok) {
                const data = await res.json();
                setClasses(data);
                if (data.length > 0) setSelectedClass(data[0].id);
            }
        } catch (error) {
            console.error('Failed to load classes:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadStudentsAndAttendance = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) return;

            const studentsRes = await fetch(`${baseUrl}/students?class_id=${selectedClass}`, { headers });
            let studentList: any[] = [];
            if (studentsRes.ok) {
                studentList = await studentsRes.json();
                setStudents(studentList);
            } else {
                setStudents([]);
            }

            const attendanceRes = await fetch(
                `${baseUrl}/attendance?class_id=${selectedClass}&date_from=${selectedDate}&date_to=${selectedDate}`,
                { headers }
            );

            if (attendanceRes.ok) {
                const records = await attendanceRes.json();
                if (records.length > 0) {
                    const existingMap: Record<string, AttendanceStatus> = {};
                    for (const r of records) {
                        existingMap[r.student_id] = r.status as AttendanceStatus;
                    }
                    for (const s of studentList) {
                        if (!existingMap[s.id]) {
                            existingMap[s.id] = 'present';
                        }
                    }
                    setAttendance(existingMap);
                    setExistingRecords(true);
                } else {
                    setAttendance(Object.fromEntries(studentList.map((s: any) => [s.id, 'present' as AttendanceStatus])));
                    setExistingRecords(false);
                }
            } else {
                setAttendance(Object.fromEntries(studentList.map((s: any) => [s.id, 'present' as AttendanceStatus])));
                setExistingRecords(false);
            }
        } catch (error) {
            console.error('Failed to load data:', error);
            setStudents([]);
        }
    };

    const handleStatusChange = (studentId: string, status: AttendanceStatus) => {
        setAttendance(prev => ({ ...prev, [studentId]: status }));
    };

    const stats = {
        present: Object.values(attendance).filter(s => s === 'present').length,
        absent: Object.values(attendance).filter(s => s === 'absent').length,
        late: Object.values(attendance).filter(s => s === 'late').length,
        excused: Object.values(attendance).filter(s => s === 'excused').length,
    };

    const attendanceRate = students.length > 0 ? Math.round(((stats.present + stats.late) / students.length) * 100) : 0;

    const handleSave = async () => {
        if (students.length === 0) return;
        setSaving(true);
        setSaveMessage(null);
        try {
            const headers = await getHeaders();
            if (!headers) { setSaving(false); return; }

            const res = await fetch(`${baseUrl}/attendance/bulk`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    class_id: selectedClass,
                    date: selectedDate,
                    records: Object.entries(attendance).map(([student_id, status]) => ({
                        student_id,
                        status,
                    })),
                }),
            });

            if (res.ok) {
                const absentCount = stats.absent;
                setSaveMessage({
                    type: 'success',
                    text: absentCount > 0
                        ? `Attendance saved. ${absentCount} student${absentCount > 1 ? 's' : ''} marked absent — parents will be notified.`
                        : 'Attendance saved successfully.'
                });
                setExistingRecords(true);
            } else {
                const err = await res.json().catch(() => ({}));
                setSaveMessage({ type: 'error', text: err.detail || 'Failed to save attendance.' });
            }
        } catch (error) {
            setSaveMessage({ type: 'error', text: 'Network error. Please try again.' });
        } finally {
            setSaving(false);
            setTimeout(() => setSaveMessage(null), 5000);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-12 w-12 animate-spin text-emerald-600" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Attendance</h1>
                    <p className="text-slate-500 mt-1">Record and track student attendance</p>
                </div>
                <Button onClick={handleSave} disabled={saving || students.length === 0} className="bg-emerald-600 hover:bg-emerald-700">
                    {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    {saving ? 'Saving...' : 'Save Attendance'}
                </Button>
            </div>

            {saveMessage && (
                <div className={`p-3 rounded-lg border flex items-center gap-2 ${saveMessage.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {saveMessage.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                    <span className="text-sm font-medium">{saveMessage.text}</span>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Present" value={stats.present} description={`${attendanceRate}% attendance rate`} icon={CalendarCheck} />
                <StatCard title="Absent" value={stats.absent} icon={Users} />
                <StatCard title="Late" value={stats.late} icon={Clock} />
                <StatCard title="Excused" value={stats.excused} icon={AlertTriangle} />
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4 items-end">
                        <div className="flex-1">
                            <label className="text-sm font-medium text-slate-700 mb-2 block">Select Class</label>
                            <Select value={selectedClass} onValueChange={setSelectedClass}>
                                <SelectTrigger><SelectValue placeholder="Select class" /></SelectTrigger>
                                <SelectContent>
                                    {classes.map((cls: any) => (
                                        <SelectItem key={cls.id} value={cls.id}>{cls.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="flex-1">
                            <label className="text-sm font-medium text-slate-700 mb-2 block">Date</label>
                            <div className="flex items-center gap-2">
                                <Button variant="outline" size="icon" onClick={() => {
                                    const d = new Date(selectedDate); d.setDate(d.getDate() - 1);
                                    setSelectedDate(d.toISOString().split('T')[0]);
                                }}><ChevronLeft className="h-4 w-4" /></Button>
                                <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)}
                                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm" />
                                <Button variant="outline" size="icon" onClick={() => {
                                    const d = new Date(selectedDate); d.setDate(d.getDate() + 1);
                                    setSelectedDate(d.toISOString().split('T')[0]);
                                }}><ChevronRight className="h-4 w-4" /></Button>
                            </div>
                        </div>
                        <Button variant="outline" onClick={() => setAttendance(Object.fromEntries(students.map(s => [s.id, 'present' as AttendanceStatus])))} disabled={students.length === 0}>
                            Mark All Present
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {existingRecords && (
                <div className="p-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 text-sm flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    Attendance already recorded for this date. Saving will update existing records.
                </div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle>{classes.find((c: any) => c.id === selectedClass)?.name || 'Attendance'}</CardTitle>
                    <CardDescription>
                        {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-12">#</TableHead>
                                <TableHead>Admission #</TableHead>
                                <TableHead>Student Name</TableHead>
                                <TableHead>Status</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {students.length > 0 ? students.map((student: any, index: number) => (
                                <TableRow key={student.id}>
                                    <TableCell className="font-medium">{index + 1}</TableCell>
                                    <TableCell className="font-mono text-sm">{student.admission_number}</TableCell>
                                    <TableCell className="font-medium">{student.first_name} {student.last_name}</TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            {(Object.keys(statusConfig) as AttendanceStatus[]).map((status) => (
                                                <Badge key={status} variant="secondary"
                                                    className={`cursor-pointer transition-all ${attendance[student.id] === status ? statusConfig[status].color + ' ring-2 ring-offset-1 ring-slate-400' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                                                    onClick={() => handleStatusChange(student.id, status)}>
                                                    {statusConfig[status].label}
                                                </Badge>
                                            ))}
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center text-slate-500 py-8">
                                        {classes.length === 0 ? 'No classes found. Create classes first.' : 'No students found in this class.'}
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
