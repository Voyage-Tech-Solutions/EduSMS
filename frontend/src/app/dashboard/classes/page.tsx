'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Clock } from 'lucide-react';

interface ScheduleItem {
    time: string;
    subject: string;
    teacher: string;
    room: string;
}

interface SubjectPerformance {
    subject: string;
    percentage: number;
}

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

export default function MyClassesPage() {
    const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
    const [subjects, setSubjects] = useState<SubjectPerformance[]>([]);
    const [loading, setLoading] = useState(true);
    const [today, setToday] = useState('');

    useEffect(() => {
        setToday(DAY_NAMES[new Date().getDay() - 1] || 'Weekend');
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) { setLoading(false); return; }

            const headers = { 'Authorization': `Bearer ${token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [scheduleRes, subjectsRes] = await Promise.all([
                fetch(`${baseUrl}/student/schedule/today`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/performance/subjects`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (scheduleRes.ok) setSchedule(await scheduleRes.json());
            if (subjectsRes.ok) setSubjects(await subjectsRes.json());
        } catch (error) {
            console.error('Failed to fetch class data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getBarColor = (pct: number) => {
        if (pct >= 80) return 'bg-emerald-500';
        if (pct >= 60) return 'bg-amber-500';
        return 'bg-red-500';
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-emerald-600';
        if (score >= 60) return 'text-amber-600';
        return 'text-red-600';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
                    <p className="mt-4 text-slate-500">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">My Classes</h1>
                <p className="text-slate-500 mt-1">Your subjects and today&apos;s timetable</p>
            </div>

            {/* Today's Timetable */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-blue-500" />
                        Today&apos;s Timetable ({today})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {schedule.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Time</TableHead>
                                    <TableHead>Subject</TableHead>
                                    <TableHead>Teacher</TableHead>
                                    <TableHead>Room</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {schedule.map((item, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{item.time}</TableCell>
                                        <TableCell className="font-medium">{item.subject}</TableCell>
                                        <TableCell>{item.teacher}</TableCell>
                                        <TableCell>{item.room}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="py-8 text-center text-slate-500">
                            <Clock className="h-10 w-10 mx-auto mb-3 text-slate-300" />
                            <p>No classes scheduled for today</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Subject Performance */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-emerald-500" />
                        My Subjects
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {subjects.length > 0 ? (
                        <div className="space-y-4">
                            {subjects.map((subject, idx) => (
                                <div key={idx} className="p-4 rounded-lg border border-slate-200">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-medium text-slate-900">{subject.subject}</span>
                                        <span className={`text-lg font-bold ${getScoreColor(subject.percentage)}`}>
                                            {subject.percentage}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2.5">
                                        <div
                                            className={`h-2.5 rounded-full ${getBarColor(subject.percentage)}`}
                                            style={{ width: `${Math.min(subject.percentage, 100)}%` }}
                                        ></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="py-8 text-center text-slate-500">
                            <BookOpen className="h-10 w-10 mx-auto mb-3 text-slate-300" />
                            <p>No subject data available yet</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
