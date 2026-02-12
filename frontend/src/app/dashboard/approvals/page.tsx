'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import {
    CheckCircle, XCircle, Clock, AlertTriangle, Loader2, FileText, CreditCard, Users, BookOpen,
} from 'lucide-react';

interface ApprovalCategory {
    type: string;
    count: number;
    priority: 'high' | 'medium' | 'low';
    description: string;
}

const categoryIcons: Record<string, any> = {
    'Overdue Invoices': CreditCard,
    'Student Transfers': Users,
    'Late Submissions': BookOpen,
    'Inactive Students': AlertTriangle,
};

const priorityColors: Record<string, string> = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-amber-100 text-amber-800',
    low: 'bg-blue-100 text-blue-800',
};

export default function ApprovalsPage() {
    const [approvals, setApprovals] = useState<ApprovalCategory[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedApproval, setSelectedApproval] = useState<ApprovalCategory | null>(null);
    const [showDetailDialog, setShowDetailDialog] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => {
        fetchApprovals();
    }, []);

    const fetchApprovals = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const res = await fetch(`${baseUrl}/principal/approvals`, { headers });
            if (res.ok) {
                const data = await res.json();
                setApprovals(data);
            }
        } catch (error) {
            console.error('Failed to fetch approvals:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleReview = (approval: ApprovalCategory) => {
        setSelectedApproval(approval);
        setShowDetailDialog(true);
    };

    const handleAction = async (action: 'approve' | 'dismiss') => {
        setShowDetailDialog(false);
        setMessage({
            type: 'success',
            text: action === 'approve'
                ? `${selectedApproval?.type} items marked as reviewed.`
                : `${selectedApproval?.type} items dismissed.`,
        });
        setTimeout(() => setMessage(null), 4000);
    };

    const totalPending = approvals.reduce((sum, a) => sum + a.count, 0);
    const highPriority = approvals.filter(a => a.priority === 'high').reduce((sum, a) => sum + a.count, 0);

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Approvals Required</h1>
                <p className="text-slate-500 mt-1">Review and approve pending requests</p>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-full bg-amber-50">
                                <Clock className="h-6 w-6 text-amber-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-900">{totalPending}</p>
                                <p className="text-sm text-slate-500">Total Pending</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-full bg-red-50">
                                <AlertTriangle className="h-6 w-6 text-red-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-900">{highPriority}</p>
                                <p className="text-sm text-slate-500">High Priority</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-full bg-emerald-50">
                                <CheckCircle className="h-6 w-6 text-emerald-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-900">{approvals.filter(a => a.count === 0).length}</p>
                                <p className="text-sm text-slate-500">Categories Clear</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Pending Approvals</CardTitle>
                </CardHeader>
                <CardContent>
                    {approvals.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Category</TableHead>
                                    <TableHead>Count</TableHead>
                                    <TableHead>Priority</TableHead>
                                    <TableHead>Description</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {approvals.map((approval, idx) => {
                                    const Icon = categoryIcons[approval.type] || FileText;
                                    return (
                                        <TableRow key={idx}>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    <Icon className="h-4 w-4 text-slate-500" />
                                                    <span className="font-medium">{approval.type}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className={approval.count > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}>
                                                    {approval.count}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge className={priorityColors[approval.priority]}>
                                                    {approval.priority}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-sm text-slate-500 max-w-xs">
                                                {approval.description || `${approval.count} items require attention`}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button size="sm" variant="outline" onClick={() => handleReview(approval)} disabled={approval.count === 0}>
                                                    <CheckCircle className="h-4 w-4 mr-1" />
                                                    Review
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="text-center py-12 text-slate-500">
                            <CheckCircle className="h-12 w-12 mx-auto text-emerald-400 mb-3" />
                            <p className="font-medium">All clear!</p>
                            <p className="text-sm mt-1">No pending approvals at this time.</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Review Detail Dialog */}
            <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Review: {selectedApproval?.type}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div className="p-4 rounded-lg bg-slate-50">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-medium text-slate-700">Items to Review</span>
                                <Badge variant="secondary">{selectedApproval?.count}</Badge>
                            </div>
                            <p className="text-sm text-slate-500">
                                {selectedApproval?.description || `There are ${selectedApproval?.count} items in this category that require your attention.`}
                            </p>
                        </div>
                        <div className="p-4 rounded-lg border border-amber-200 bg-amber-50">
                            <p className="text-sm text-amber-800">
                                <strong>Priority:</strong> {selectedApproval?.priority} — {
                                    selectedApproval?.priority === 'high' ? 'Requires immediate attention.' :
                                    selectedApproval?.priority === 'medium' ? 'Should be reviewed soon.' :
                                    'Can be reviewed at your convenience.'
                                }
                            </p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => handleAction('dismiss')}>
                            <XCircle className="h-4 w-4 mr-1" /> Dismiss
                        </Button>
                        <Button onClick={() => handleAction('approve')} className="bg-emerald-600 hover:bg-emerald-700">
                            <CheckCircle className="h-4 w-4 mr-1" /> Mark Reviewed
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
