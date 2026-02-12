'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { StatCard } from '@/components/dashboard';
import { Search, CheckCircle, XCircle, AlertTriangle, FileText, Send, Loader2, MoreHorizontal } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const statusConfig: Record<string, { color: string; icon: any }> = {
    missing: { color: 'bg-slate-100 text-slate-800', icon: AlertTriangle },
    uploaded: { color: 'bg-amber-100 text-amber-800', icon: FileText },
    verified: { color: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
    expired: { color: 'bg-red-100 text-red-800', icon: XCircle },
    rejected: { color: 'bg-red-100 text-red-800', icon: XCircle },
};

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<any[]>([]);
    const [summary, setSummary] = useState({ total_students: 0, fully_compliant: 0, missing_docs: 0, expired_docs: 0, pending_verification: 0 });
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [showVerifyDialog, setShowVerifyDialog] = useState(false);
    const [showReminderDialog, setShowReminderDialog] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState<any>(null);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [reminderForm, setReminderForm] = useState({ target: 'missing', message: 'Please upload the required document.' });

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => {
        loadData();
    }, [statusFilter]);

    const loadData = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const [summaryRes, docsRes] = await Promise.all([
                fetch(`${baseUrl}/documents/compliance/summary`, { headers }),
                fetch(`${baseUrl}/documents?${statusFilter !== 'all' ? `status=${statusFilter}` : ''}`, { headers }),
            ]);
            if (summaryRes.ok) setSummary(await summaryRes.json());
            if (docsRes.ok) {
                const data = await docsRes.json();
                setDocuments(data.data || []);
            }
        } catch (error) {
            console.error('Failed to load documents:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async (action: 'verify' | 'reject') => {
        if (!selectedDoc) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/documents/${selectedDoc.id}/verify`, {
                method: 'PATCH',
                headers,
                body: JSON.stringify({ action })
            });
            if (res.ok) {
                setShowVerifyDialog(false);
                setSelectedDoc(null);
                setMessage({ type: 'success', text: `Document ${action}d successfully.` });
                loadData();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || `Failed to ${action} document.` });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const handleBulkReminder = async () => {
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/documents/bulk-reminder`, {
                method: 'POST',
                headers,
                body: JSON.stringify(reminderForm)
            });
            if (res.ok) {
                const data = await res.json();
                setShowReminderDialog(false);
                setMessage({ type: 'success', text: `Reminders sent to ${data.sent} students.` });
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to send reminders.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const filteredDocs = documents.filter(doc => {
        if (!search) return true;
        const q = search.toLowerCase();
        return doc.students?.first_name?.toLowerCase().includes(q) || doc.students?.last_name?.toLowerCase().includes(q);
    });

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Documents & Compliance</h1>
                    <p className="text-slate-500 mt-1">Manage and verify school documentation</p>
                </div>
                <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => setShowReminderDialog(true)}>
                    <Send className="mr-2 h-4 w-4" />Send Bulk Reminder
                </Button>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                <StatCard title="Total Students" value={summary.total_students} icon={FileText} />
                <StatCard title="Fully Compliant" value={summary.fully_compliant} icon={CheckCircle} />
                <StatCard title="Missing Documents" value={summary.missing_docs} icon={AlertTriangle} />
                <StatCard title="Expired Documents" value={summary.expired_docs} icon={XCircle} />
                <StatCard title="Pending Verification" value={summary.pending_verification} icon={FileText} />
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input placeholder="Search by student name..." className="pl-10" value={search} onChange={e => setSearch(e.target.value)} />
                        </div>
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                {Object.keys(statusConfig).map(key => (
                                    <SelectItem key={key} value={key}>{key}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>Documents <Badge variant="secondary" className="ml-2">{filteredDocs.length}</Badge></CardTitle></CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Student</TableHead>
                                <TableHead>Document Type</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Uploaded</TableHead>
                                <TableHead>Verified</TableHead>
                                <TableHead>Expiry</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredDocs.length > 0 ? filteredDocs.map(doc => {
                                const StatusIcon = statusConfig[doc.status]?.icon || FileText;
                                return (
                                    <TableRow key={doc.id}>
                                        <TableCell className="font-medium">{doc.students?.first_name} {doc.students?.last_name}</TableCell>
                                        <TableCell>{doc.document_type}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary" className={statusConfig[doc.status]?.color}>
                                                <StatusIcon className="h-3 w-3 mr-1" />{doc.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{doc.uploaded ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}</TableCell>
                                        <TableCell>{doc.verified ? '✓' : '-'}</TableCell>
                                        <TableCell>{doc.expiry_date || 'N/A'}</TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    {doc.status === 'uploaded' && (
                                                        <DropdownMenuItem onClick={() => { setSelectedDoc(doc); setShowVerifyDialog(true); }}>
                                                            <CheckCircle className="mr-2 h-4 w-4" />Verify
                                                        </DropdownMenuItem>
                                                    )}
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                );
                            }) : (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-slate-500 py-8">No documents found.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Dialog open={showVerifyDialog} onOpenChange={setShowVerifyDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Verify Document</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-50 rounded-lg">
                            <p className="text-sm text-slate-600">Document: <strong>{selectedDoc?.document_type}</strong></p>
                            <p className="text-sm text-slate-600">Student: <strong>{selectedDoc?.students?.first_name} {selectedDoc?.students?.last_name}</strong></p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => handleVerify('reject')} disabled={saving}>Reject</Button>
                        <Button onClick={() => handleVerify('verify')} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Verifying...' : 'Verify'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <Dialog open={showReminderDialog} onOpenChange={setShowReminderDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Send Bulk Reminder</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label>Target</Label>
                            <Select value={reminderForm.target} onValueChange={v => setReminderForm({ ...reminderForm, target: v })}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="missing">Missing Documents</SelectItem>
                                    <SelectItem value="expired">Expired Documents</SelectItem>
                                    <SelectItem value="uploaded">Pending Verification</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Message</Label>
                            <Input value={reminderForm.message} onChange={e => setReminderForm({ ...reminderForm, message: e.target.value })} />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowReminderDialog(false)}>Cancel</Button>
                        <Button onClick={handleBulkReminder} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Sending...' : 'Send Reminders'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
