"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { DollarSign, Download, CreditCard } from "lucide-react";

export default function ParentFeesPage() {
  const [invoices, setInvoices] = useState<any>({ invoices: [], summary: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    const studentId = "student-id";
    const response = await fetch(`/api/v1/parent/invoices?student_id=${studentId}`);
    const data = await response.json();
    setInvoices(data);
    setLoading(false);
  };

  const getStatusBadge = (status: string) => {
    const variants: any = { paid: "default", pending: "destructive", partial: "secondary" };
    return <Badge variant={variants[status] || "outline"}>{status}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Fees & Payments</h1>
        <p className="text-muted-foreground">Manage school fees and payments</p>
      </div>

      {/* Financial Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Billed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${invoices.summary.total_billed || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Paid</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">${invoices.summary.total_paid || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-red-200 bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Outstanding Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">${invoices.summary.balance || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Invoices Table */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Paid</TableHead>
                <TableHead>Balance</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">Loading...</TableCell>
                </TableRow>
              ) : invoices.invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">No invoices found</TableCell>
                </TableRow>
              ) : (
                invoices.invoices.map((invoice: any) => (
                  <TableRow key={invoice.id}>
                    <TableCell className="font-mono">{invoice.invoice_number}</TableCell>
                    <TableCell>{invoice.description || "School Fees"}</TableCell>
                    <TableCell>${invoice.amount}</TableCell>
                    <TableCell className="text-green-600">${invoice.paid_amount}</TableCell>
                    <TableCell className="text-red-600">${invoice.amount - invoice.paid_amount}</TableCell>
                    <TableCell>{new Date(invoice.due_date).toLocaleDateString()}</TableCell>
                    <TableCell>{getStatusBadge(invoice.status)}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {invoice.status !== "paid" && (
                          <PaymentDialog invoice={invoice} onSuccess={fetchInvoices} />
                        )}
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Payment History */}
      <Card>
        <CardHeader>
          <CardTitle>Payment History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">Payment history will appear here</p>
        </CardContent>
      </Card>
    </div>
  );
}

function PaymentDialog({ invoice, onSuccess }: any) {
  const [open, setOpen] = useState(false);
  const [payment, setPayment] = useState({
    amount: invoice.amount - invoice.paid_amount,
    payment_method: "card",
    transaction_reference: ""
  });

  const handlePayment = async () => {
    await fetch("/api/v1/parent/payments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ invoice_id: invoice.id, ...payment }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <CreditCard className="w-4 h-4 mr-1" />
          Pay Now
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Make Payment</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Invoice Number</Label>
            <p className="text-sm font-mono">{invoice.invoice_number}</p>
          </div>
          <div>
            <Label>Amount Due</Label>
            <p className="text-2xl font-bold text-red-600">${invoice.amount - invoice.paid_amount}</p>
          </div>
          <div>
            <Label>Payment Amount</Label>
            <Input
              type="number"
              value={payment.amount}
              onChange={(e) => setPayment({ ...payment, amount: parseFloat(e.target.value) })}
            />
          </div>
          <div>
            <Label>Payment Method</Label>
            <Select value={payment.payment_method} onValueChange={(v) => setPayment({ ...payment, payment_method: v })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="card">Credit/Debit Card</SelectItem>
                <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                <SelectItem value="cash">Cash</SelectItem>
                <SelectItem value="mobile_money">Mobile Money</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Transaction Reference (Optional)</Label>
            <Input
              placeholder="Enter reference number"
              value={payment.transaction_reference}
              onChange={(e) => setPayment({ ...payment, transaction_reference: e.target.value })}
            />
          </div>
          <Button onClick={handlePayment} className="w-full">
            <DollarSign className="w-4 h-4 mr-2" />
            Process Payment
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
