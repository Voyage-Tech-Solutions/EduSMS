'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileText, CheckCircle } from 'lucide-react';

interface AssignmentItem {
    task: string;
    subject: string;
    due: string;
    due_date: string;
    assignment_id: string;
}

export default function AssignmentsPage() {
    const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAssignments();
    }, []);

    const fetchAssignments = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) { setLoading(false); return; }

            const headers = { 'Authorization': `Bearer ${token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const res = await fetch(`${baseUrl}/student/assignments/today`, { headers }).catch(() => ({ ok: false } as Response));
            if (res.ok) setAssignments(await res.json());
        } catch (error) {
            console.error('Failed to fetch assignments:', error);
        } finally {
            setLoading(false);
        }
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
                <h1 className="text-3xl font-bold text-slate-900">Assignments</h1>
                <p className="text-slate-500 mt-1">Track your upcoming and pending assignments</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-indigo-500" />
                        Upcoming Assignments
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {assignments.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Task</TableHead>
                                    <TableHead>Subject</TableHead>
                                    <TableHead>Due Date</TableHead>
                                    <TableHead>Status</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {assignments.map((task, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{task.task}</TableCell>
                                        <TableCell>{task.subject}</TableCell>
                                        <TableCell>
                                            <Badge variant={task.due === 'Today' ? 'destructive' : task.due === 'Tomorrow' ? 'secondary' : 'outline'}>
                                                {task.due}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Pending</Badge>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="py-12 text-center text-slate-500">
                            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-emerald-300" />
                            <p className="font-medium text-emerald-600">All caught up!</p>
                            <p className="text-sm mt-1">No pending assignments for the next 7 days.</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
