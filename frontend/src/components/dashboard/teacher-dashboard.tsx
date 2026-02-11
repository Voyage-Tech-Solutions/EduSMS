'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Clock,
    BookOpen,
    AlertCircle,
    CheckCircle,
} from 'lucide-react';

export function TeacherDashboard() {
    const [schedule, setSchedule] = useState<any[]>([]);
    const [gradingQueue, setGradingQueue] = useState<any[]>([]);
    const [classes, setClasses] = useState<any[]>([]);
    const [attentionItems, setAttentionItems] = useState<any[]>([]);
    const [planning, setPlanning] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setLoading(false);
                return;
            }
            
            const headers = { 'Authorization': `Bearer ${token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [scheduleRes, gradingRes, classesRes, attentionRes, planningRes] = await Promise.all([
                fetch(`${baseUrl}/teacher/schedule/today`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/teacher/grading/queue`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/teacher/classes/snapshot`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/teacher/attention/items`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/teacher/planning/status`, { headers }).catch(() => ({ ok: false } as Response))
            ]);

            if (scheduleRes.ok) setSchedule(await scheduleRes.json());
            if (gradingRes.ok) setGradingQueue(await gradingRes.json());
            if (classesRes.ok) setClasses(await classesRes.json());
            if (attentionRes.ok) setAttentionItems(await attentionRes.json());
            if (planningRes.ok) setPlanning(await planningRes.json());
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
                        <p className="mt-4 text-slate-500">Loading dashboard...</p>
                    </div>
                </div>
            </div>
        );
    }

    const totalClasses = schedule.length;
    const totalGrading = gradingQueue.reduce((sum, item) => sum + item.pending, 0);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Today's Teaching Overview</h1>
                <p className="text-slate-500 mt-1">You have {totalClasses} classes and {totalGrading} grading tasks pending</p>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-3">
                <Button className="bg-emerald-600 hover:bg-emerald-700">Take Attendance (Next Class)</Button>
                <Button variant="outline">Open Gradebook</Button>
                <Button variant="outline">Add Assignment</Button>
            </div>

            {/* Today's Schedule */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-blue-500" />
                        Today's Schedule
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Time</TableHead>
                                <TableHead>Subject</TableHead>
                                <TableHead>Class</TableHead>
                                <TableHead>Room</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {schedule.map((item, idx) => (
                                <TableRow key={idx}>
                                    <TableCell className="font-medium">{item.time}</TableCell>
                                    <TableCell>{item.subject}</TableCell>
                                    <TableCell>{item.class}</TableCell>
                                    <TableCell>{item.room}</TableCell>
                                    <TableCell>
                                        <Badge variant={item.status === 'upcoming' ? 'secondary' : 'default'}>
                                            {item.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button size="sm">Start Class</Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Grading Queue */}
            {gradingQueue.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BookOpen className="h-5 w-5 text-amber-500" />
                            Grading Queue
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Class</TableHead>
                                    <TableHead>Task</TableHead>
                                    <TableHead>Submissions Pending</TableHead>
                                    <TableHead className="text-right">Action</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {gradingQueue.map((item, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell>{item.type}</TableCell>
                                        <TableCell>{item.class}</TableCell>
                                        <TableCell>{item.task}</TableCell>
                                        <TableCell>
                                            <Badge variant="destructive">{item.pending}</Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button size="sm">Open Grading Panel</Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            {/* My Classes Snapshot */}
            <Card>
                <CardHeader>
                    <CardTitle>My Classes Snapshot</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Class</TableHead>
                                <TableHead>Students</TableHead>
                                <TableHead>Attendance Avg</TableHead>
                                <TableHead>Class Avg</TableHead>
                                <TableHead>Coverage</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {classes.map((cls, idx) => (
                                <TableRow key={idx} className="cursor-pointer hover:bg-slate-50">
                                    <TableCell className="font-medium">{cls.class}</TableCell>
                                    <TableCell>{cls.students}</TableCell>
                                    <TableCell>{cls.attendance_avg}%</TableCell>
                                    <TableCell>{cls.class_avg}%</TableCell>
                                    <TableCell>
                                        <Badge variant="outline">{cls.coverage}</Badge>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Lesson Planning Status */}
            {planning.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Lesson Planning Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Class</TableHead>
                                    <TableHead>Term Plan</TableHead>
                                    <TableHead>Coverage</TableHead>
                                    <TableHead>Next Topic</TableHead>
                                    <TableHead className="text-right">Action</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {planning.map((item, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{item.class}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary">{item.term_plan}</Badge>
                                        </TableCell>
                                        <TableCell>{item.coverage}</TableCell>
                                        <TableCell>{item.next_topic}</TableCell>
                                        <TableCell className="text-right">
                                            <Button size="sm" variant="outline">Update Coverage</Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            {/* Attention Items */}
            {attentionItems.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertCircle className="h-5 w-5 text-red-500" />
                            Attention Items
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {attentionItems.map((item, idx) => (
                                <div key={idx} className="p-3 rounded-lg border border-amber-200 bg-amber-50 flex items-center gap-3">
                                    <AlertCircle className="h-5 w-5 text-amber-600" />
                                    <p className="text-sm font-medium text-slate-900">{item}</p>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
