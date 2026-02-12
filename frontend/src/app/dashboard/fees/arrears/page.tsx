'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import {
    DollarSign,
    AlertTriangle,
    ArrowLeft,
    Clock,
    Search,
    TrendingDown,
} from 'lucide-react';
import Link from 'next/link';

interface ArrearsData {
    summary: {
        total_expected: number;
        total_collected: number;
        total_outstanding: number;
        total_overdue: number;
        collection_rate: number;
    };
    aging: {
        days_30: number;
        days_60: number;
        days_90_plus: number;
    };
    grade_arrears: {
        grade: string;
        outstanding: number;
        student_count: number;
    }[];
    student_arrears: {
        student_name: string;
        student_id: string;
        grade: string;
        class: string;
        description: string;
        amount_owed: number;
        due_date: string;
        days_overdue: number;
        status: string;
    }[];
}

export default function ArrearsPage() {
    const [data, setData] = useState<ArrearsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchArrears();
    }, []);

    const fetchArrears = async () => {
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            if (!session?.access_token) { setLoading(false); return; }

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
            const res = await fetch(`${baseUrl}/principal/finance/arrears`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` },
            });
            if (res.ok) setData(await res.json());
        } catch (error) {
            console.error('Failed to fetch arrears:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredArrears = data?.student_arrears.filter(a =>
        a.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        a.grade.toLowerCase().includes(searchTerm.toLowerCase()) ||
        a.class.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    const getOverdueBadge = (days: number) => {
        if (days >= 90) return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">90+ days</Badge>;
        if (days >= 60) return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">60+ days</Badge>;
        if (days >= 30) return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">30+ days</Badge>;
        if (days > 0) return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">{days} days</Badge>;
        return <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100">Current</Badge>;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
                    <p className="mt-4 text-slate-500">Loading arrears data...</p>
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="space-y-6">
                <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700">
                    <ArrowLeft className="h-4 w-4" /> Back to Dashboard
                </Link>
                <p className="text-slate-500">Unable to load arrears data.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-2">
                    <ArrowLeft className="h-4 w-4" /> Back to Dashboard
                </Link>
                <h1 className="text-3xl font-bold text-slate-900">Fee Arrears Report</h1>
                <p className="text-slate-500 mt-1">Detailed view of outstanding balances and overdue payments</p>
            </div>

            {/* Collection Summary */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-2xl font-bold text-slate-900">${data.summary.total_expected.toLocaleString()}</p>
                        <p className="text-sm text-slate-500 mt-1">Total Expected</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-2xl font-bold text-emerald-600">${data.summary.total_collected.toLocaleString()}</p>
                        <p className="text-sm text-slate-500 mt-1">Total Collected</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-2xl font-bold text-amber-600">${data.summary.total_outstanding.toLocaleString()}</p>
                        <p className="text-sm text-slate-500 mt-1">Outstanding</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-2xl font-bold text-red-600">${data.summary.total_overdue.toLocaleString()}</p>
                        <p className="text-sm text-slate-500 mt-1">Overdue</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <p className={`text-2xl font-bold ${data.summary.collection_rate >= 80 ? 'text-emerald-600' : data.summary.collection_rate >= 60 ? 'text-amber-600' : 'text-red-600'}`}>
                            {data.summary.collection_rate}%
                        </p>
                        <p className="text-sm text-slate-500 mt-1">Collection Rate</p>
                    </CardContent>
                </Card>
            </div>

            {/* Overdue Aging Buckets */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-amber-500" />
                        Overdue Aging
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 rounded-lg border border-amber-200 bg-amber-50">
                            <p className="text-sm font-medium text-amber-800">30-59 Days Overdue</p>
                            <p className="text-2xl font-bold text-amber-700 mt-1">${data.aging.days_30.toLocaleString()}</p>
                        </div>
                        <div className="p-4 rounded-lg border border-orange-200 bg-orange-50">
                            <p className="text-sm font-medium text-orange-800">60-89 Days Overdue</p>
                            <p className="text-2xl font-bold text-orange-700 mt-1">${data.aging.days_60.toLocaleString()}</p>
                        </div>
                        <div className="p-4 rounded-lg border border-red-200 bg-red-50">
                            <p className="text-sm font-medium text-red-800">90+ Days Overdue</p>
                            <p className="text-2xl font-bold text-red-700 mt-1">${data.aging.days_90_plus.toLocaleString()}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Arrears by Grade */}
            {data.grade_arrears.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingDown className="h-5 w-5 text-blue-500" />
                            Arrears by Grade
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Grade</TableHead>
                                    <TableHead>Students Owing</TableHead>
                                    <TableHead>Total Outstanding</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {data.grade_arrears.map((g, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{g.grade}</TableCell>
                                        <TableCell>{g.student_count}</TableCell>
                                        <TableCell className="font-bold text-amber-600">${g.outstanding.toLocaleString()}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            {/* Student Arrears List */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                            Student Arrears List
                        </div>
                        <div className="relative w-64">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Search by name, grade, class..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-9"
                            />
                        </div>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {filteredArrears.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Student</TableHead>
                                    <TableHead>Grade</TableHead>
                                    <TableHead>Class</TableHead>
                                    <TableHead>Description</TableHead>
                                    <TableHead>Amount Owed</TableHead>
                                    <TableHead>Due Date</TableHead>
                                    <TableHead>Overdue</TableHead>
                                    <TableHead>Status</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredArrears.map((a, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{a.student_name}</TableCell>
                                        <TableCell>{a.grade}</TableCell>
                                        <TableCell>{a.class}</TableCell>
                                        <TableCell>{a.description}</TableCell>
                                        <TableCell className="font-bold text-red-600">${a.amount_owed.toLocaleString()}</TableCell>
                                        <TableCell>{new Date(a.due_date).toLocaleDateString()}</TableCell>
                                        <TableCell>{getOverdueBadge(a.days_overdue)}</TableCell>
                                        <TableCell>
                                            <Badge className={
                                                a.status === 'overdue' ? 'bg-red-100 text-red-700 hover:bg-red-100' :
                                                a.status === 'partial' ? 'bg-amber-100 text-amber-700 hover:bg-amber-100' :
                                                'bg-slate-100 text-slate-700 hover:bg-slate-100'
                                            }>
                                                {a.status}
                                            </Badge>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="py-8 text-center text-slate-500">
                            <DollarSign className="h-10 w-10 mx-auto mb-3 text-slate-300" />
                            <p className="font-medium">{searchTerm ? 'No matching records found' : 'No outstanding arrears'}</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
