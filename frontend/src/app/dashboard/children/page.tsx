'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Users,
    CalendarCheck,
    BookOpen,
    FileText,
    MessageSquare,
    TrendingUp,
    TrendingDown,
    Minus,
} from 'lucide-react';

interface ChildDetail {
    name: string;
    class: string;
    attendance_rate: number;
    average_grade: number;
    pending_assignments: number;
    outstanding_fees: number;
    student_id: string;
}

interface AcademicProgress {
    name: string;
    student_id: string;
    trend: string;
    recent_grades: { subject: string; assessment: string; score: number }[];
    attendance_trend: number;
}

export default function MyChildrenPage() {
    const [children, setChildren] = useState<ChildDetail[]>([]);
    const [progress, setProgress] = useState<AcademicProgress[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) { setLoading(false); return; }

            const headers = { 'Authorization': `Bearer ${token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const [childrenRes, progressRes] = await Promise.all([
                fetch(`${baseUrl}/parent/children/overview`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/parent/academic/progress`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (childrenRes.ok) setChildren(await childrenRes.json());
            if (progressRes.ok) setProgress(await progressRes.json());
        } catch (error) {
            console.error('Failed to fetch children data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'improving': return <TrendingUp className="h-4 w-4 text-emerald-500" />;
            case 'declining': return <TrendingDown className="h-4 w-4 text-red-500" />;
            default: return <Minus className="h-4 w-4 text-slate-400" />;
        }
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
                <h1 className="text-3xl font-bold text-slate-900">My Children</h1>
                <p className="text-slate-500 mt-1">Detailed view of each child&apos;s academic profile</p>
            </div>

            {children.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center text-slate-500">
                        <Users className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                        <p className="font-medium">No children linked to your account.</p>
                        <p className="text-sm mt-1">Contact your school administration to link your children.</p>
                    </CardContent>
                </Card>
            ) : (
                children.map((child, idx) => {
                    const childProgress = progress.find(p => p.student_id === child.student_id);

                    return (
                        <Card key={idx}>
                            <CardHeader className="bg-slate-50">
                                <CardTitle className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Users className="h-5 w-5 text-emerald-600" />
                                        {child.name} &ndash; {child.class}
                                    </div>
                                    {childProgress && (
                                        <div className="flex items-center gap-1 text-sm font-normal">
                                            {getTrendIcon(childProgress.trend)}
                                            <span className="text-slate-500 capitalize">{childProgress.trend}</span>
                                        </div>
                                    )}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-6 space-y-6">
                                {/* Quick Stats */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                                        <CalendarCheck className="h-5 w-5 mx-auto mb-1 text-blue-500" />
                                        <p className="text-2xl font-bold">{child.attendance_rate}%</p>
                                        <p className="text-xs text-slate-500">Attendance</p>
                                    </div>
                                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                                        <BookOpen className="h-5 w-5 mx-auto mb-1 text-emerald-500" />
                                        <p className="text-2xl font-bold">{child.average_grade}%</p>
                                        <p className="text-xs text-slate-500">Average Grade</p>
                                    </div>
                                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                                        <FileText className="h-5 w-5 mx-auto mb-1 text-amber-500" />
                                        <p className="text-2xl font-bold">{child.pending_assignments}</p>
                                        <p className="text-xs text-slate-500">Pending Tasks</p>
                                    </div>
                                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                                        <span className="text-lg font-bold block mb-1">$</span>
                                        <p className={`text-2xl font-bold ${child.outstanding_fees > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                            {child.outstanding_fees}
                                        </p>
                                        <p className="text-xs text-slate-500">Outstanding</p>
                                    </div>
                                </div>

                                {/* Recent Grades */}
                                {childProgress && childProgress.recent_grades.length > 0 && (
                                    <div>
                                        <h4 className="font-medium text-slate-700 mb-2">Recent Grades</h4>
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>Subject</TableHead>
                                                    <TableHead>Assessment</TableHead>
                                                    <TableHead className="text-right">Score</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {childProgress.recent_grades.map((grade, gIdx) => (
                                                    <TableRow key={gIdx}>
                                                        <TableCell>{grade.subject}</TableCell>
                                                        <TableCell>{grade.assessment}</TableCell>
                                                        <TableCell className={`text-right font-bold ${getScoreColor(grade.score)}`}>
                                                            {grade.score}%
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="flex gap-2 pt-2 border-t">
                                    <Button variant="outline" size="sm">
                                        <FileText className="h-4 w-4 mr-1" />
                                        View Report Card
                                    </Button>
                                    <Button variant="outline" size="sm">
                                        <CalendarCheck className="h-4 w-4 mr-1" />
                                        View Attendance
                                    </Button>
                                    <Button variant="outline" size="sm">
                                        <MessageSquare className="h-4 w-4 mr-1" />
                                        Message Teacher
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })
            )}
        </div>
    );
}
