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
import {
    Search, Plus, Eye, CreditCard, Download, DollarSign, AlertCircle, CheckCircle, Clock, Loader2, MoreHorizontal
} from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const statusConfig: Record<string, { color: string; icon: any }> = {
    paid: { color: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
    partial: { color: 'bg-amber-100 text-amber-800', icon: Clock },
    pending: { color: 'bg-blue-100 text-blue-800', icon: Clock },
    overdue: { color: 'bg-red-100 text-red-800', icon: AlertCircle },
};

export default function FeesPage() {
    const [invoices, setInvoices] = useState<any[]>([]);
    const [students, setStudents] = useState<any[]>([]);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showPaymentDialog, setShowPaymentDialog] = useState(false);
    const [selectedInvoice, setSelectedInvoice] = useState<any>(null);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const [invoiceForm, setInvoiceForm] = useState({
        student_id: '', amount: '', due_date: '', description: ''
    });

    const [paymentForm, setPaymentForm] = useState({
        amount: '', payment_method: 'cash', reference: ''
    });

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        loadInvoices();
    }, [statusFilter]);

    const loadInitialData = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const studentsRes = await fetch(`${baseUrl}/students?limit=100`, { headers });
            if (studentsRes.ok) setStudents(await studentsRes.json());
        } catch (error) {
            console.error('Failed to load students:', error);
        }
        loadInvoices();
    };

    const loadInvoices = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const params = new URLSearchParams();
            if (statusFilter !== 'all') params.set('status', statusFilter);
            const res = await fetch(`${baseUrl}/fees/invoices?${params}`, { headers });
            if (res.ok) setInvoices(await res.json());
        } catch (error) {
            console.error('Failed to load invoices:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateInvoice = async () => {
        if (!invoiceForm.student_id || !invoiceForm.amount || !invoiceForm.due_date) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/fees/invoices`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    student_id: invoiceForm.student_id,
                    amount: parseFloat(invoiceForm.amount),
                    due_date: invoiceForm.due_date,
                    description: invoiceForm.description || 'Tuition Fee'
                })
            });
            if (res.ok) {
                setShowCreateDialog(false);
                resetInvoiceForm();
                setMessage({ type: 'success', text: 'Invoice created successfully.' });
                loadInvoices();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to create invoice.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const handleRecordPayment = async () => {
        if (!selectedInvoice || !paymentForm.amount) return;
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/fees/payments`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    invoice_id: selectedInvoice.id,
                    amount: parseFloat(paymentForm.amount),
                    payment_method: paymentForm.payment_method,
                    reference: paymentForm.reference || undefined
                })
            });
            if (res.ok) {
                setShowPaymentDialog(false);
                setSelectedInvoice(null);
                resetPaymentForm();
                setMessage({ type: 'success', text: 'Payment recorded successfully.' });
                loadInvoices();
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to record payment.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const resetInvoiceForm = () => {
        setInvoiceForm({ student_id: '', amount: '', due_date: '', description: '' });
    };

    const resetPaymentForm = () => {
        setPaymentForm({ amount: '', payment_method: 'cash', reference: '' });
    };

    const openPaymentDialog = (invoice: any) => {
        setSelectedInvoice(invoice);
        const remaining = invoice.amount - invoice.amount_paid;
        setPaymentForm({ ...paymentForm, amount: remaining.toString() });
        setShowPaymentDialog(true);
    };

    const getStudentName = (studentId: string) => {
        const student = students.find(s => s.id === studentId);
        return student ? `${student.first_name} ${student.last_name}` : 'Unknown';
    };

    const filteredInvoices = invoices.filter(inv => {
        if (!search) return true;
        const q = search.toLowerCase();
        return inv.invoice_number?.toLowerCase().includes(q) || getStudentName(inv.student_id).toLowerCase().includes(q);
    });

    const totalAmount = invoices.reduce((sum, inv) => sum + (inv.amount || 0), 0);
    const totalPaid = invoices.reduce((sum, inv) => sum + (inv.amount_paid || 0), 0);
    const totalOverdue = invoices.filter(inv => inv.status === 'overdue').reduce((sum, inv) => sum + ((inv.amount || 0) - (inv.amount_paid || 0)), 0);

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Fees & Billing</h1>
                    <p className="text-slate-500 mt-1">Manage invoices, payments, and fee structures</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
                    <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => { resetInvoiceForm(); setShowCreateDialog(true); }}>
                        <Plus className="mr-2 h-4 w-4" />Create Invoice
                    </Button>
                </div>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Total Billed" value={`$${totalAmount.toLocaleString()}`} description="this term" icon={DollarSign} />
                <StatCard title="Total Collected" value={`$${totalPaid.toLocaleString()}`} description={totalAmount > 0 ? `${Math.round((totalPaid / totalAmount) * 100)}% collection rate` : '0%'} icon={CheckCircle} />
                <StatCard title="Outstanding" value={`$${(totalAmount - totalPaid).toLocaleString()}`} description="pending payment" icon={Clock} />
                <StatCard title="Overdue" value={`$${totalOverdue.toLocaleString()}`} description="needs attention" icon={AlertCircle} />
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input placeholder="Search by student name or invoice number..." className="pl-10"
                                value={search} onChange={e => setSearch(e.target.value)} />
                        </div>
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                <SelectItem value="paid">Paid</SelectItem>
                                <SelectItem value="partial">Partial</SelectItem>
                                <SelectItem value="pending">Pending</SelectItem>
                                <SelectItem value="overdue">Overdue</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>Invoices <Badge variant="secondary" className="ml-2">{filteredInvoices.length}</Badge></CardTitle></CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Invoice #</TableHead>
                                <TableHead>Student</TableHead>
                                <TableHead>Description</TableHead>
                                <TableHead>Amount</TableHead>
                                <TableHead>Paid</TableHead>
                                <TableHead>Due Date</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredInvoices.length > 0 ? filteredInvoices.map(invoice => {
                                const StatusIcon = statusConfig[invoice.status]?.icon || Clock;
                                return (
                                    <TableRow key={invoice.id}>
                                        <TableCell className="font-mono text-sm">{invoice.invoice_number}</TableCell>
                                        <TableCell className="font-medium">{getStudentName(invoice.student_id)}</TableCell>
                                        <TableCell>{invoice.description}</TableCell>
                                        <TableCell className="font-medium">${invoice.amount.toLocaleString()}</TableCell>
                                        <TableCell>${invoice.amount_paid.toLocaleString()}</TableCell>
                                        <TableCell>{invoice.due_date}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary" className={statusConfig[invoice.status]?.color}>
                                                <StatusIcon className="h-3 w-3 mr-1" />{invoice.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem><Eye className="mr-2 h-4 w-4" />View Details</DropdownMenuItem>
                                                    {invoice.status !== 'paid' && (
                                                        <DropdownMenuItem onClick={() => openPaymentDialog(invoice)}>
                                                            <CreditCard className="mr-2 h-4 w-4" />Record Payment
                                                        </DropdownMenuItem>
                                                    )}
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                );
                            }) : (
                                <TableRow>
                                    <TableCell colSpan={8} className="text-center text-slate-500 py-8">
                                        No invoices found.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Create Invoice Dialog */}
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Create Invoice</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label>Student *</Label>
                            <Select value={invoiceForm.student_id} onValueChange={v => setInvoiceForm({ ...invoiceForm, student_id: v })}>
                                <SelectTrigger><SelectValue placeholder="Select student" /></SelectTrigger>
                                <SelectContent>
                                    {students.map(s => (
                                        <SelectItem key={s.id} value={s.id}>{s.first_name} {s.last_name} ({s.admission_number})</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Description</Label>
                            <Input value={invoiceForm.description} onChange={e => setInvoiceForm({ ...invoiceForm, description: e.target.value })} placeholder="e.g., Term 1 Tuition" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Amount *</Label>
                                <Input type="number" value={invoiceForm.amount} onChange={e => setInvoiceForm({ ...invoiceForm, amount: e.target.value })} placeholder="0.00" />
                            </div>
                            <div className="space-y-2">
                                <Label>Due Date *</Label>
                                <Input type="date" value={invoiceForm.due_date} onChange={e => setInvoiceForm({ ...invoiceForm, due_date: e.target.value })} />
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                        <Button onClick={handleCreateInvoice} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Creating...' : 'Create Invoice'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Record Payment Dialog */}
            <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Record Payment</DialogTitle></DialogHeader>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-50 rounded-lg">
                            <p className="text-sm text-slate-600">Invoice: <strong>{selectedInvoice?.invoice_number}</strong></p>
                            <p className="text-sm text-slate-600">Student: <strong>{getStudentName(selectedInvoice?.student_id)}</strong></p>
                            <p className="text-sm text-slate-600">Balance: <strong>${((selectedInvoice?.amount || 0) - (selectedInvoice?.amount_paid || 0)).toLocaleString()}</strong></p>
                        </div>
                        <div className="space-y-2">
                            <Label>Amount *</Label>
                            <Input type="number" value={paymentForm.amount} onChange={e => setPaymentForm({ ...paymentForm, amount: e.target.value })} placeholder="0.00" />
                        </div>
                        <div className="space-y-2">
                            <Label>Payment Method *</Label>
                            <Select value={paymentForm.payment_method} onValueChange={v => setPaymentForm({ ...paymentForm, payment_method: v })}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="cash">Cash</SelectItem>
                                    <SelectItem value="card">Card</SelectItem>
                                    <SelectItem value="transfer">Bank Transfer</SelectItem>
                                    <SelectItem value="mobile">Mobile Money</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Reference Number</Label>
                            <Input value={paymentForm.reference} onChange={e => setPaymentForm({ ...paymentForm, reference: e.target.value })} placeholder="Optional" />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>Cancel</Button>
                        <Button onClick={handleRecordPayment} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            {saving ? 'Recording...' : 'Record Payment'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
