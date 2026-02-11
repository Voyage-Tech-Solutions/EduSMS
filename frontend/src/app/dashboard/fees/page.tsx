'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { StatCard } from '@/components/dashboard';
import {
    Search,
    Plus,
    MoreHorizontal,
    Eye,
    CreditCard,
    Receipt,
    Download,
    DollarSign,
    AlertCircle,
    CheckCircle,
    Clock,
} from 'lucide-react';

// Mock data for invoices
const mockInvoices = [
    {
        id: '1',
        invoice_number: 'INV-202402-001',
        student_name: 'Emily Johnson',
        grade: 'Grade 5',
        amount: 5000,
        amount_paid: 5000,
        due_date: '2024-02-28',
        status: 'paid',
        description: 'Term 1 Tuition',
    },
    {
        id: '2',
        invoice_number: 'INV-202402-002',
        student_name: 'Michael Brown',
        grade: 'Grade 6',
        amount: 5000,
        amount_paid: 2500,
        due_date: '2024-02-28',
        status: 'partial',
        description: 'Term 1 Tuition',
    },
    {
        id: '3',
        invoice_number: 'INV-202402-003',
        student_name: 'Sarah Williams',
        grade: 'Grade 5',
        amount: 5000,
        amount_paid: 0,
        due_date: '2024-02-15',
        status: 'overdue',
        description: 'Term 1 Tuition',
    },
    {
        id: '4',
        invoice_number: 'INV-202402-004',
        student_name: 'James Davis',
        grade: 'Grade 7',
        amount: 5500,
        amount_paid: 0,
        due_date: '2024-03-15',
        status: 'pending',
        description: 'Term 1 Tuition',
    },
    {
        id: '5',
        invoice_number: 'INV-202402-005',
        student_name: 'Emma Miller',
        grade: 'Grade 6',
        amount: 5000,
        amount_paid: 5000,
        due_date: '2024-02-28',
        status: 'paid',
        description: 'Term 1 Tuition',
    },
];

const statusConfig = {
    paid: { color: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
    partial: { color: 'bg-amber-100 text-amber-800', icon: Clock },
    pending: { color: 'bg-blue-100 text-blue-800', icon: Clock },
    overdue: { color: 'bg-red-100 text-red-800', icon: AlertCircle },
};

export default function FeesPage() {
    const [invoices, setInvoices] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    useEffect(() => {
        loadInvoices();
    }, []);

    const loadInvoices = async () => {
        try {
            const response = await fetch('/api/v1/invoices');
            const data = await response.json();
            setInvoices(data);
        } catch (error) {
            console.error('Failed to load invoices:', error);
            setInvoices([]);
        }
    };

    const filteredInvoices = invoices.filter((invoice) => {
        const matchesSearch =
            invoice.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            invoice.invoice_number?.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesStatus = statusFilter === 'all' || invoice.status === statusFilter;

        return matchesSearch && matchesStatus;
    });

    const totalAmount = invoices.reduce((sum, inv) => sum + (inv.amount || 0), 0);
    const totalPaid = invoices.reduce((sum, inv) => sum + (inv.amount_paid || 0), 0);
    const totalOverdue = invoices.filter(inv => inv.status === 'overdue').reduce((sum, inv) => sum + ((inv.amount || 0) - (inv.amount_paid || 0)), 0);

    return (
        <div className="space-y-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Fees & Billing</h1>
                        <p className="text-slate-500 mt-1">Manage invoices, payments, and fee structures</p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            Export
                        </Button>
                        <Button className="bg-emerald-600 hover:bg-emerald-700">
                            <Plus className="mr-2 h-4 w-4" />
                            Create Invoice
                        </Button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        title="Total Billed"
                        value={`$${totalAmount.toLocaleString()}`}
                        description="this term"
                        icon={DollarSign}
                    />
                    <StatCard
                        title="Total Collected"
                        value={`$${totalPaid.toLocaleString()}`}
                        description={totalAmount > 0 ? `${Math.round((totalPaid / totalAmount) * 100)}% collection rate` : '0% collection rate'}
                        icon={CheckCircle}
                    />
                    <StatCard
                        title="Outstanding"
                        value={`$${(totalAmount - totalPaid).toLocaleString()}`}
                        description="pending payment"
                        icon={Clock}
                    />
                    <StatCard
                        title="Overdue"
                        value={`$${totalOverdue.toLocaleString()}`}
                        description="needs attention"
                        icon={AlertCircle}
                    />
                </div>

                {/* Filters */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search by student name or invoice number..."
                                    className="pl-10"
                                    value={searchQuery}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-full md:w-48">
                                    <SelectValue placeholder="Filter by status" />
                                </SelectTrigger>
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

                {/* Invoices Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>
                            Invoices
                            <Badge variant="secondary" className="ml-2">
                                {filteredInvoices.length} invoices
                            </Badge>
                        </CardTitle>
                    </CardHeader>
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
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredInvoices.map((invoice) => {
                                    const StatusIcon = statusConfig[invoice.status as keyof typeof statusConfig].icon;
                                    return (
                                        <TableRow key={invoice.id}>
                                            <TableCell className="font-mono text-sm">
                                                {invoice.invoice_number}
                                            </TableCell>
                                            <TableCell>
                                                <div>
                                                    <div className="font-medium">{invoice.student_name}</div>
                                                    <div className="text-sm text-slate-500">{invoice.grade}</div>
                                                </div>
                                            </TableCell>
                                            <TableCell>{invoice.description}</TableCell>
                                            <TableCell className="font-medium">
                                                ${invoice.amount.toLocaleString()}
                                            </TableCell>
                                            <TableCell>
                                                ${invoice.amount_paid.toLocaleString()}
                                            </TableCell>
                                            <TableCell>{invoice.due_date}</TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="secondary"
                                                    className={statusConfig[invoice.status as keyof typeof statusConfig].color}
                                                >
                                                    <StatusIcon className="h-3 w-3 mr-1" />
                                                    {invoice.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button variant="ghost" size="icon">
                                                            <MoreHorizontal className="h-4 w-4" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end">
                                                        <DropdownMenuItem>
                                                            <Eye className="mr-2 h-4 w-4" />
                                                            View Details
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem>
                                                            <CreditCard className="mr-2 h-4 w-4" />
                                                            Record Payment
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem>
                                                            <Receipt className="mr-2 h-4 w-4" />
                                                            Print Invoice
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>

                        {filteredInvoices.length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                No invoices found matching your criteria.
                            </div>
                        )}
                    </CardContent>
                </Card>
        </div>
    );
}
