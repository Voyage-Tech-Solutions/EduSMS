'use client';

import { useEffect, useState } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DollarSign, CreditCard, FileText, Tag } from 'lucide-react';

export default function BillingPage() {
    const [subscriptions, setSubscriptions] = useState<any[]>([]);
    const [invoices, setInvoices] = useState<any[]>([]);
    const [payments, setPayments] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [subs, invs, pays] = await Promise.all([
                authFetch('/api/v1/sysadmin/billing/subscriptions').then(r => r.json()),
                authFetch('/api/v1/sysadmin/billing/invoices').then(r => r.json()),
                authFetch('/api/v1/sysadmin/billing/payments').then(r => r.json()),
            ]);
            setSubscriptions(subs);
            setInvoices(invs);
            setPayments(pays);
        } catch (error) {
            console.error('Failed to load billing data:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Billing & Subscriptions</h1>
                <p className="text-slate-500 mt-1">Manage subscriptions, invoices, and payments</p>
            </div>

            <Tabs defaultValue="subscriptions" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="subscriptions">
                        <CreditCard className="h-4 w-4 mr-2" />
                        Subscriptions
                    </TabsTrigger>
                    <TabsTrigger value="invoices">
                        <FileText className="h-4 w-4 mr-2" />
                        Invoices
                    </TabsTrigger>
                    <TabsTrigger value="payments">
                        <DollarSign className="h-4 w-4 mr-2" />
                        Payments
                    </TabsTrigger>
                </TabsList>

                {/* Subscriptions */}
                <TabsContent value="subscriptions">
                    <Card>
                        <CardHeader>
                            <CardTitle>Active Subscriptions</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Tenant</TableHead>
                                        <TableHead>Plan</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Billing Cycle</TableHead>
                                        <TableHead>Amount</TableHead>
                                        <TableHead>Next Billing</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                        </TableRow>
                                    ) : subscriptions.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center text-slate-500">
                                                No subscriptions found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        subscriptions.map((sub) => (
                                            <TableRow key={sub.id}>
                                                <TableCell className="font-medium">
                                                    {sub.schools?.name || 'Unknown'}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="outline" className="capitalize">
                                                        {sub.plan_type}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant={sub.status === 'active' ? 'default' : 'secondary'}>
                                                        {sub.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="capitalize">{sub.billing_cycle}</TableCell>
                                                <TableCell className="font-mono">
                                                    ${sub.amount} {sub.currency}
                                                </TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {sub.ends_at ? new Date(sub.ends_at).toLocaleDateString() : 'N/A'}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button variant="ghost" size="sm">
                                                        Manage
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Invoices */}
                <TabsContent value="invoices">
                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Invoices</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Invoice #</TableHead>
                                        <TableHead>Tenant</TableHead>
                                        <TableHead>Amount</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Due Date</TableHead>
                                        <TableHead>Paid At</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                        </TableRow>
                                    ) : invoices.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center text-slate-500">
                                                No invoices found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        invoices.map((invoice) => (
                                            <TableRow key={invoice.id}>
                                                <TableCell className="font-mono text-sm">
                                                    {invoice.invoice_number}
                                                </TableCell>
                                                <TableCell className="font-medium">
                                                    {invoice.schools?.name || 'Unknown'}
                                                </TableCell>
                                                <TableCell className="font-mono">
                                                    ${invoice.amount} {invoice.currency}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant={
                                                            invoice.status === 'paid'
                                                                ? 'default'
                                                                : invoice.status === 'pending'
                                                                ? 'secondary'
                                                                : 'destructive'
                                                        }
                                                    >
                                                        {invoice.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : 'N/A'}
                                                </TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {invoice.paid_at ? new Date(invoice.paid_at).toLocaleDateString() : '-'}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button variant="ghost" size="sm">
                                                        View PDF
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Payments */}
                <TabsContent value="payments">
                    <Card>
                        <CardHeader>
                            <CardTitle>Payment Attempts</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Tenant</TableHead>
                                        <TableHead>Amount</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Method</TableHead>
                                        <TableHead>Provider</TableHead>
                                        <TableHead>Attempted At</TableHead>
                                        <TableHead>Failed Reason</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                        </TableRow>
                                    ) : payments.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="text-center text-slate-500">
                                                No payment attempts found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        payments.map((payment) => (
                                            <TableRow key={payment.id}>
                                                <TableCell className="font-medium">
                                                    {payment.schools?.name || 'Unknown'}
                                                </TableCell>
                                                <TableCell className="font-mono">
                                                    ${payment.amount} {payment.currency}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant={
                                                            payment.status === 'succeeded'
                                                                ? 'default'
                                                                : payment.status === 'pending'
                                                                ? 'secondary'
                                                                : 'destructive'
                                                        }
                                                    >
                                                        {payment.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="capitalize">{payment.payment_method}</TableCell>
                                                <TableCell className="capitalize">{payment.provider}</TableCell>
                                                <TableCell className="text-sm text-slate-500">
                                                    {new Date(payment.attempted_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell className="text-sm text-red-600">
                                                    {payment.failed_reason || '-'}
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
