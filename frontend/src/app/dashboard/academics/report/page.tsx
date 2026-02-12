'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    GraduationCap,
    Award,
    Users,
    BookOpen,
    UserCheck,
    ArrowLeft,
    CheckCircle,
    XCircle,
} from 'lucide-react';
import Link from 'next/link';

interface GradePerformance {
    grade: string;
    grade_id: string;
    pass_rate: number;
    average_score: number;
    student_count: number;
    entries_count: number;
}

interface SubjectPerformance {
    subject: string;
    subject_id: string;
    average_score: number;
    pass_rate: number;
    entries_count: number;
}

interface TeacherPerformance {
    teacher: string;
    teacher_id: string;
    average_student_score: number;
    entries_graded: number;
    subjects: string[];
}

interface TeacherCompletion {
    teacher: string;
    teacher_id: string;
    has_submitted: boolean;
}

interface FullReport {
    school_pass_rate: number;
    total_entries: number;
    total_students: number;
    total_subjects: number;
    total_teachers: number;
    grade_performance: GradePerformance[];
    subject_performance: SubjectPerformance[];
    teacher_performance: TeacherPerformance[];
    teacher_completion: TeacherCompletion[];
}

export default function AcademicReportPage() {
    const [report, setReport] = useState<FullReport | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchReport();
    }, []);

    const fetchReport = async () => {
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            if (!session?.access_token) { setLoading(false); return; }

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
            const res = await fetch(`${baseUrl}/principal/academic/full-report`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` },
            });
            if (res.ok) setReport(await res.json());
        } catch (error) {
            console.error('Failed to fetch academic report:', error);
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
                    <p className="mt-4 text-slate-500">Loading academic report...</p>
                </div>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="space-y-6">
                <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700">
                    <ArrowLeft className="h-4 w-4" /> Back to Dashboard
                </Link>
                <p className="text-slate-500">Unable to load academic report.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-2">
                        <ArrowLeft className="h-4 w-4" /> Back to Dashboard
                    </Link>
                    <h1 className="text-3xl font-bold text-slate-900">Full Academic Report</h1>
                    <p className="text-slate-500 mt-1">Comprehensive school-wide academic performance analysis</p>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <p className={`text-3xl font-bold ${getScoreColor(report.school_pass_rate)}`}>{report.school_pass_rate}%</p>
                        <p className="text-sm text-slate-500 mt-1">School Pass Rate</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-3xl font-bold text-slate-900">{report.total_students}</p>
                        <p className="text-sm text-slate-500 mt-1">Active Students</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-3xl font-bold text-slate-900">{report.total_subjects}</p>
                        <p className="text-sm text-slate-500 mt-1">Subjects</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-3xl font-bold text-slate-900">{report.total_teachers}</p>
                        <p className="text-sm text-slate-500 mt-1">Teachers</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-3xl font-bold text-slate-900">{report.total_entries}</p>
                        <p className="text-sm text-slate-500 mt-1">Grade Entries</p>
                    </CardContent>
                </Card>
            </div>

            {/* Grade-Level Performance */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <GraduationCap className="h-5 w-5 text-blue-500" />
                        Grade-Level Performance
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {report.grade_performance.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Grade</TableHead>
                                    <TableHead>Students</TableHead>
                                    <TableHead>Assessments</TableHead>
                                    <TableHead>Average Score</TableHead>
                                    <TableHead>Pass Rate</TableHead>
                                    <TableHead>Performance</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {report.grade_performance.map((g) => (
                                    <TableRow key={g.grade_id}>
                                        <TableCell className="font-medium">{g.grade}</TableCell>
                                        <TableCell>{g.student_count}</TableCell>
                                        <TableCell>{g.entries_count}</TableCell>
                                        <TableCell className={`font-bold ${getScoreColor(g.average_score)}`}>
                                            {g.average_score}%
                                        </TableCell>
                                        <TableCell className={`font-bold ${getScoreColor(g.pass_rate)}`}>
                                            {g.pass_rate}%
                                        </TableCell>
                                        <TableCell>
                                            <div className="w-full bg-slate-100 rounded-full h-2.5 max-w-[120px]">
                                                <div
                                                    className={`h-2.5 rounded-full ${getBarColor(g.average_score)}`}
                                                    style={{ width: `${Math.min(g.average_score, 100)}%` }}
                                                ></div>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <p className="text-slate-500 text-center py-6">No grade data available yet</p>
                    )}
                </CardContent>
            </Card>

            {/* Best Performing Subjects */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-emerald-500" />
                        Subject Performance Rankings
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {report.subject_performance.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-12">Rank</TableHead>
                                    <TableHead>Subject</TableHead>
                                    <TableHead>Assessments</TableHead>
                                    <TableHead>Average Score</TableHead>
                                    <TableHead>Pass Rate</TableHead>
                                    <TableHead>Performance</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {report.subject_performance.map((s, idx) => (
                                    <TableRow key={s.subject_id}>
                                        <TableCell>
                                            {idx < 3 ? (
                                                <Badge className={
                                                    idx === 0 ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100' :
                                                    idx === 1 ? 'bg-slate-200 text-slate-700 hover:bg-slate-200' :
                                                    'bg-amber-100 text-amber-800 hover:bg-amber-100'
                                                }>#{idx + 1}</Badge>
                                            ) : (
                                                <span className="text-slate-500 ml-2">#{idx + 1}</span>
                                            )}
                                        </TableCell>
                                        <TableCell className="font-medium">{s.subject}</TableCell>
                                        <TableCell>{s.entries_count}</TableCell>
                                        <TableCell className={`font-bold ${getScoreColor(s.average_score)}`}>
                                            {s.average_score}%
                                        </TableCell>
                                        <TableCell className={`font-bold ${getScoreColor(s.pass_rate)}`}>
                                            {s.pass_rate}%
                                        </TableCell>
                                        <TableCell>
                                            <div className="w-full bg-slate-100 rounded-full h-2.5 max-w-[120px]">
                                                <div
                                                    className={`h-2.5 rounded-full ${getBarColor(s.average_score)}`}
                                                    style={{ width: `${Math.min(s.average_score, 100)}%` }}
                                                ></div>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <p className="text-slate-500 text-center py-6">No subject data available yet</p>
                    )}
                </CardContent>
            </Card>

            {/* Teacher Performance */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Award className="h-5 w-5 text-purple-500" />
                        Teacher Performance (by Student Outcomes)
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {report.teacher_performance.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-12">Rank</TableHead>
                                    <TableHead>Teacher</TableHead>
                                    <TableHead>Subjects</TableHead>
                                    <TableHead>Entries Graded</TableHead>
                                    <TableHead>Avg Student Score</TableHead>
                                    <TableHead>Performance</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {report.teacher_performance.map((t, idx) => (
                                    <TableRow key={t.teacher_id}>
                                        <TableCell>
                                            {idx < 3 ? (
                                                <Badge className={
                                                    idx === 0 ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100' :
                                                    idx === 1 ? 'bg-slate-200 text-slate-700 hover:bg-slate-200' :
                                                    'bg-amber-100 text-amber-800 hover:bg-amber-100'
                                                }>#{idx + 1}</Badge>
                                            ) : (
                                                <span className="text-slate-500 ml-2">#{idx + 1}</span>
                                            )}
                                        </TableCell>
                                        <TableCell className="font-medium">{t.teacher}</TableCell>
                                        <TableCell>
                                            <div className="flex flex-wrap gap-1">
                                                {t.subjects.map((s, i) => (
                                                    <Badge key={i} variant="outline" className="text-xs">{s}</Badge>
                                                ))}
                                            </div>
                                        </TableCell>
                                        <TableCell>{t.entries_graded}</TableCell>
                                        <TableCell className={`font-bold ${getScoreColor(t.average_student_score)}`}>
                                            {t.average_student_score}%
                                        </TableCell>
                                        <TableCell>
                                            <div className="w-full bg-slate-100 rounded-full h-2.5 max-w-[120px]">
                                                <div
                                                    className={`h-2.5 rounded-full ${getBarColor(t.average_student_score)}`}
                                                    style={{ width: `${Math.min(t.average_student_score, 100)}%` }}
                                                ></div>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <p className="text-slate-500 text-center py-6">No teacher performance data available yet</p>
                    )}
                </CardContent>
            </Card>

            {/* Assessment Completion by Teacher */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <UserCheck className="h-5 w-5 text-indigo-500" />
                        Assessment Completion Status (Last 30 Days)
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {report.teacher_completion.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {report.teacher_completion.map((t) => (
                                <div
                                    key={t.teacher_id}
                                    className={`flex items-center gap-3 p-3 rounded-lg border ${
                                        t.has_submitted ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'
                                    }`}
                                >
                                    {t.has_submitted ? (
                                        <CheckCircle className="h-5 w-5 text-emerald-600 shrink-0" />
                                    ) : (
                                        <XCircle className="h-5 w-5 text-red-600 shrink-0" />
                                    )}
                                    <div>
                                        <p className="text-sm font-medium text-slate-900">{t.teacher}</p>
                                        <p className={`text-xs ${t.has_submitted ? 'text-emerald-600' : 'text-red-600'}`}>
                                            {t.has_submitted ? 'Marks submitted' : 'No submissions'}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-500 text-center py-6">No teacher data available</p>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
