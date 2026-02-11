'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from '@/components/ui/card';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { StatCard } from '@/components/dashboard';
import {
    CalendarCheck,
    Users,
    AlertTriangle,
    Clock,
    Save,
    ChevronLeft,
    ChevronRight,
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
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [students, setStudents] = useState<any[]>([]);
    const [classes, setClasses] = useState<any[]>([]);
    const [attendance, setAttendance] = useState<Record<string, AttendanceStatus>>({});

    useEffect(() => {
        loadClasses();
    }, []);

    useEffect(() => {
        if (selectedClass) {
            loadStudents();
        }
    }, [selectedClass, selectedDate]);

    const loadClasses = async () => {
        try {
            const response = await fetch('/api/v1/classes');
            const data = await response.json();
            setClasses(data);
            if (data.length > 0) setSelectedClass(data[0].id);
        } catch (error) {
            console.error('Failed to load classes:', error);
        }
    };

    const loadStudents = async () => {
        try {
            const response = await fetch(`/api/v1/students?class_id=${selectedClass}`);
            const data = await response.json();
            setStudents(data);
            setAttendance(Object.fromEntries(data.map((s: any) => [s.id, 'present'])));
        } catch (error) {
            console.error('Failed to load students:', error);
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
        try {
            await fetch('/api/v1/attendance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    class_id: selectedClass,
                    date: selectedDate,
                    records: Object.entries(attendance).map(([student_id, status]) => ({
                        student_id,
                        status,
                    })),
                }),
            });
            alert('Attendance saved successfully!');
        } catch (error) {
            console.error('Failed to save attendance:', error);
        }
    };

    return (
        <div className="space-y-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Attendance</h1>
                        <p className="text-slate-500 mt-1">Record and track student attendance</p>
                    </div>
                    <Button onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-700">
                        <Save className="mr-2 h-4 w-4" />
                        Save Attendance
                    </Button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        title="Present"
                        value={stats.present}
                        description={`${attendanceRate}% attendance rate`}
                        icon={CalendarCheck}
                    />
                    <StatCard
                        title="Absent"
                        value={stats.absent}
                        icon={Users}
                    />
                    <StatCard
                        title="Late"
                        value={stats.late}
                        icon={Clock}
                    />
                    <StatCard
                        title="Excused"
                        value={stats.excused}
                        icon={AlertTriangle}
                    />
                </div>

                {/* Class & Date Selection */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex flex-col md:flex-row gap-4 items-end">
                            <div className="flex-1">
                                <label className="text-sm font-medium text-slate-700 mb-2 block">
                                    Select Class
                                </label>
                                <Select value={selectedClass} onValueChange={setSelectedClass}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select class" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {classes.length > 0 ? classes.map((cls) => (
                                            <SelectItem key={cls.id} value={cls.id}>
                                                {cls.name}
                                            </SelectItem>
                                        )) : (
                                            <SelectItem value="none" disabled>No classes available</SelectItem>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="flex-1">
                                <label className="text-sm font-medium text-slate-700 mb-2 block">
                                    Date
                                </label>
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        onClick={() => {
                                            const date = new Date(selectedDate);
                                            date.setDate(date.getDate() - 1);
                                            setSelectedDate(date.toISOString().split('T')[0]);
                                        }}
                                    >
                                        <ChevronLeft className="h-4 w-4" />
                                    </Button>
                                    <input
                                        type="date"
                                        value={selectedDate}
                                        onChange={(e) => setSelectedDate(e.target.value)}
                                        className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                                    />
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        onClick={() => {
                                            const date = new Date(selectedDate);
                                            date.setDate(date.getDate() + 1);
                                            setSelectedDate(date.toISOString().split('T')[0]);
                                        }}
                                    >
                                        <ChevronRight className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    onClick={() => setAttendance(Object.fromEntries(students.map(s => [s.id, 'present'])))}
                                    disabled={students.length === 0}
                                >
                                    Mark All Present
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Attendance Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>{classes.find(c => c.id === selectedClass)?.name || 'Attendance'}</CardTitle>
                        <CardDescription>
                            {new Date(selectedDate).toLocaleDateString('en-US', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
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
                                {students.length > 0 ? students.map((student, index) => (
                                    <TableRow key={student.id}>
                                        <TableCell className="font-medium">{index + 1}</TableCell>
                                        <TableCell className="font-mono text-sm">
                                            {student.admission_number}
                                        </TableCell>
                                        <TableCell className="font-medium">{student.full_name}</TableCell>
                                        <TableCell>
                                            <div className="flex gap-2">
                                                {(Object.keys(statusConfig) as AttendanceStatus[]).map((status) => (
                                                    <Badge
                                                        key={status}
                                                        variant="secondary"
                                                        className={`cursor-pointer transition-all ${attendance[student.id] === status
                                                                ? statusConfig[status].color + ' ring-2 ring-offset-1 ring-slate-400'
                                                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                                            }`}
                                                        onClick={() => handleStatusChange(student.id, status)}
                                                    >
                                                        {statusConfig[status].label}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                )) : (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center text-slate-500">
                                            No students found. Select a class with students.
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
