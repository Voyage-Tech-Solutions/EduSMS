'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Trophy, BookOpen } from 'lucide-react';

interface GradeItem {
    assignment: string;
    subject: string;
    score: number;
}

interface SubjectPerformance {
    subject: string;
    percentage: number;
}

export default function GradesPage() {
    const [recentGrades, setRecentGrades] = useState<GradeItem[]>([]);
    const [subjects, setSubjects] = useState<SubjectPerformance[]>([]);
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

            const [gradesRes, subjectsRes] = await Promise.all([
                fetch(`${baseUrl}/student/grades/recent`, { headers }).catch(() => ({ ok: false } as Response)),
                fetch(`${baseUrl}/student/performance/subjects`, { headers }).catch(() => ({ ok: false } as Response)),
            ]);

            if (gradesRes.ok) setRecentGrades(await gradesRes.json());
            if (subjectsRes.ok) setSubjects(await subjectsRes.json());
        } catch (error) {
            console.error('Failed to fetch grades:', error);
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-emerald-600';
        if (score >= 60) return 'text-amber-600';
        return 'text-red-600';
    };

    const getBarColor = (pct: number) => {
        if (pct >= 80) return 'bg-emerald-500';
        if (pct >= 60) return 'bg-amber-500';
        return 'bg-red-500';
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
                <h1 className="text-3xl font-bold text-slate-900">My Grades</h1>
                <p className="text-slate-500 mt-1">View your academic performance and recent results</p>
            </div>

            {/* Subject Averages */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-emerald-500" />
                        Subject Averages
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {subjects.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            {/* Recent Grades */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Trophy className="h-5 w-5 text-amber-500" />
                        Recent Results
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {recentGrades.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Assessment</TableHead>
                                    <TableHead>Subject</TableHead>
                                    <TableHead className="text-right">Score</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {recentGrades.map((grade, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{grade.assignment}</TableCell>
                                        <TableCell>{grade.subject}</TableCell>
                                        <TableCell className={`text-right font-bold ${getScoreColor(grade.score)}`}>
                                            {grade.score}%
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="py-8 text-center text-slate-500">
                            <Trophy className="h-10 w-10 mx-auto mb-3 text-slate-300" />
                            <p>No grades recorded yet</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
