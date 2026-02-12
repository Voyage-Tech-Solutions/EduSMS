'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    GraduationCap,
    Award,
    BookOpen,
    UserCheck,
    CheckCircle,
    XCircle,
    FileText,
    ArrowRight,
} from 'lucide-react';

interface FullReport {
    school_pass_rate: number;
    total_entries: number;
    total_students: number;
    total_subjects: number;
    total_teachers: number;
    grade_performance: {
        grade: string;
        grade_id: string;
        pass_rate: number;
        average_score: number;
        student_count: number;
        entries_count: number;
    }[];
    subject_performance: {
        subject: string;
        subject_id: string;
        average_score: number;
        pass_rate: number;
        entries_count: number;
    }[];
    teacher_performance: {
        teacher: string;
        teacher_id: string;
        average_student_score: number;
        entries_graded: number;
        subjects: string[];
    }[];
    teacher_completion: {
        teacher: string;
        teacher_id: string;
        has_submitted: boolean;
    }[];
}

export default function AcademicsPage() {
    const router = useRouter();
    const [data, setData] = useState<FullReport | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAcademicData();
    }, []);

    const fetchAcademicData = async () => {
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            if (!session?.access_token) { setLoading(false); return; }

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
            const res = await fetch(`${baseUrl}/principal/academic/full-report`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` },
            });
            if (res.ok) setData(await res.json());
        } catch (error) {
            console.error('Failed to fetch academic data:', error);
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
                    <p className="mt-4 text-slate-500">Loading academic data...</p>
                </div>
            </div>
        );
    }

    const submittedCount = data?.teacher_completion.filter(t => t.has_submitted).length || 0;
    const totalTeachers = data?.teacher_completion.length || 0;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Academic Performance</h1>
                <p className="text-slate-500 mt-1">School-wide academic insights and trends</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Award className="h-5 w-5 text-emerald-500" />
                            Pass Rate
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className={`text-3xl font-bold ${getScoreColor(data?.school_pass_rate || 0)}`}>
                            {data?.school_pass_rate || 0}%
                        </p>
                        <p className="text-sm text-slate-500 mt-1">Overall school performance</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <GraduationCap className="h-5 w-5 text-blue-500" />
                            Assessment Completion
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-slate-900">{data?.total_entries || 0}</p>
                        <p className="text-sm text-slate-500 mt-1">
                            Grade entries across {data?.total_students || 0} students
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5 text-indigo-500" />
                            Reports Submitted
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-slate-900">{submittedCount}/{totalTeachers}</p>
                        <p className="text-sm text-slate-500 mt-1">Teachers completed (last 30 days)</p>
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
                    {data?.grade_performance && data.grade_performance.length > 0 ? (
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
                                {data.grade_performance.map((g) => (
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
                        <p className="text-slate-500 text-center py-6">No grade-level data available yet</p>
                    )}
                </CardContent>
            </Card>

            {/* Top Subjects */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-emerald-500" />
                        Subject Performance Rankings
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {data?.subject_performance && data.subject_performance.length > 0 ? (
                        <div className="space-y-3">
                            {data.subject_performance.slice(0, 10).map((s, idx) => (
                                <div key={s.subject_id} className="flex items-center gap-4">
                                    <span className="text-sm font-medium text-slate-500 w-6">#{idx + 1}</span>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-sm font-medium text-slate-700">{s.subject}</span>
                                            <div className="flex items-center gap-3">
                                                <span className="text-xs text-slate-400">{s.entries_count} entries</span>
                                                <span className={`text-sm font-bold ${getScoreColor(s.average_score)}`}>
                                                    {s.average_score}%
                                                </span>
                                            </div>
                                        </div>
                                        <div className="w-full bg-slate-100 rounded-full h-2">
                                            <div
                                                className={`h-2 rounded-full ${getBarColor(s.average_score)}`}
                                                style={{ width: `${Math.min(s.average_score, 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-500 text-center py-6">No subject data available yet</p>
                    )}
                </CardContent>
            </Card>

            {/* Teacher Marking Status */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <UserCheck className="h-5 w-5 text-indigo-500" />
                        Teacher Marking Status (Last 30 Days)
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {data?.teacher_completion && data.teacher_completion.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {data.teacher_completion.map((t) => (
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

            {/* View Full Report Link */}
            <div className="flex justify-center">
                <Button
                    onClick={() => router.push('/dashboard/academics/report')}
                    className="gap-2"
                >
                    View Full Detailed Report
                    <ArrowRight className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
