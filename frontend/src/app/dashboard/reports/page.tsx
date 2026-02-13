'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { StatCard } from '@/components/dashboard';
import { FileText, Download, Users, DollarSign, CalendarCheck, GraduationCap, Loader2 } from 'lucide-react';

export default function ReportsPage() {
    const [summary, setSummary] = useState({ total_enrollment: 0, avg_attendance: 0, fee_collection: 0, collection_rate: 0, academic_avg: 0 });
    const [loading, setLoading] = useState(true);
    const [showReportDialog, setShowReportDialog] = useState(false);
    const [reportType, setReportType] = useState('');
    const [generating, setGenerating] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [dateRange, setDateRange] = useState({ start: '', end: '' });

    useEffect(() => {
        const today = new Date().toISOString().split('T')[0];
        setDateRange({ start: today, end: today });
    }, []);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => {
        loadSummary();
    }, [dateRange]);

    const loadSummary = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const res = await fetch(`${baseUrl}/reports/summary?start_date=${dateRange.start}&end_date=${dateRange.end}`, { headers });
            if (res.ok) setSummary(await res.json());
        } catch (error) {
            console.error('Failed to load summary:', error);
        } finally {
            setLoading(false);
        }
    };

    const generateReport = async (type: string) => {
        setGenerating(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/reports/${type}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({})
            });
            if (res.ok) {
                const data = await res.json();
                setMessage({ type: 'success', text: `Report generated with ${data.total || data.data?.length || 0} records.` });
                setShowReportDialog(false);
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to generate report.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setGenerating(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const openReportDialog = (type: string) => {
        setReportType(type);
        setShowReportDialog(true);
    };

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Reports & Analytics</h1>
                    <p className="text-slate-500 mt-1">Analytics and insights for your school</p>
                </div>
                <div className="flex gap-3">
                    <Select value="this_month" onValueChange={() => {}}>
                        <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="today">Today</SelectItem>
                            <SelectItem value="this_week">This Week</SelectItem>
                            <SelectItem value="this_month">This Month</SelectItem>
                            <SelectItem value="this_term">This Term</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button variant="outline">
                        <Download className="mr-2 h-4 w-4" />Export All
                    </Button>
                </div>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                <StatCard title="Total Enrollment" value={summary.total_enrollment} icon={Users} />
                <StatCard title="Avg Attendance" value={`${summary.avg_attendance}%`} icon={CalendarCheck} />
                <StatCard title="Fee Collection" value={`$${summary.fee_collection.toLocaleString()}`} icon={DollarSign} />
                <StatCard title="Collection Rate" value={`${summary.collection_rate}%`} icon={DollarSign} />
                <StatCard title="Academic Avg" value={summary.academic_avg || 'N/A'} icon={GraduationCap} />
            </div>

            <Card>
                <CardHeader><CardTitle>Quick Reports</CardTitle></CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center" onClick={() => openReportDialog('student-directory')}>
                            <Users className="h-6 w-6 mb-2" />
                            <span>Student Directory</span>
                        </Button>
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center" onClick={() => openReportDialog('fee-statement')}>
                            <DollarSign className="h-6 w-6 mb-2" />
                            <span>Fee Statement</span>
                        </Button>
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center" onClick={() => openReportDialog('attendance-summary')}>
                            <CalendarCheck className="h-6 w-6 mb-2" />
                            <span>Attendance Summary</span>
                        </Button>
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center" onClick={() => openReportDialog('academic-summary')}>
                            <GraduationCap className="h-6 w-6 mb-2" />
                            <span>Grade Report</span>
                        </Button>
                    </div>
                </CardContent>
            </Card>

            <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Generate Report</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-50 rounded-lg">
                            <p className="text-sm text-slate-600">Report Type: <strong>{reportType.replace('-', ' ')}</strong></p>
                        </div>
                        <div className="space-y-2">
                            <Label>Options</Label>
                            <p className="text-sm text-slate-500">Report will be generated with current filters</p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowReportDialog(false)}>Cancel</Button>
                        <Button onClick={() => generateReport(reportType)} disabled={generating} className="bg-emerald-600 hover:bg-emerald-700">
                            {generating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />}
                            {generating ? 'Generating...' : 'Generate'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
