"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DollarSign, TrendingUp, AlertCircle, Download, Plus } from "lucide-react";

export default function FeesPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<any>(null);
  const [filters, setFilters] = useState({ status: "", term: "", search: "" });

  useEffect(() => {
    fetchSummary();
    fetchInvoices();
  }, [filters]);

  const fetchSummary = async () => {
    const res = await fetch("/api/v1/fees/summary");
    const data = await res.json();
    setSummary(data);
  };

  const fetchInvoices = async () => {
    const params = new URLSearchParams();
    if (filters.status) params.append("status", filters.status);
    if (filters.term) params.append("term_id", filters.term);
    
    const res = await fetch(`/api/v1/fees/invoices?${params}`);
    const data = await res.json();
    setInvoices(data);
  };

  const handleCreateInvoice = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    await fetch("/api/v1/fees/invoices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: formData.get("student_id"),
        description: formData.get("description"),
        amount: parseFloat(formData.get("amount") as string),
        term_id: formData.get("term_id"),
        due_date: formData.get("due_date")
      })
    });
    
    setShowCreateModal(false);
    fetchInvoices();
    fetchSummary();
  };

  const handleRecordPayment = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    await fetch("/api/v1/fees/payments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        invoice_id: selectedInvoice.id,
        amount: parseFloat(formData.get("amount") as string),
        payment_method: formData.get("payment_method"),
        payment_date: formData.get("payment_date"),
        reference_number: formData.get("reference_number")
      })
    });
    
    setShowPaymentModal(false);
    fetchInvoices();
    fetchSummary();
  };

  const getStatusColor = (status: string) => {
    const colors: any = {
      unpaid: "bg-gray-500",
      partial: "bg-blue-500",
      paid: "bg-green-500",
      overdue: "bg-red-500",
      cancelled: "bg-gray-400"
    };
    return colors[status] || "bg-gray-500";
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Fees & Billing</h1>
          <p className="text-gray-600">Manage invoices, payments, and fee structures</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
          <Button onClick={() => setShowCreateModal(true)}><Plus className="w-4 h-4 mr-2" />Create Invoice</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Billed</p>
              <p className="text-2xl font-bold">${summary.total_billed || 0}</p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Collected</p>
              <p className="text-2xl font-bold">${summary.total_collected || 0}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Collection Rate</p>
              <p className="text-2xl font-bold">{summary.collection_rate || 0}%</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Outstanding</p>
              <p className="text-2xl font-bold">${summary.outstanding || 0}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overdue</p>
              <p className="text-2xl font-bold text-red-600">${summary.overdue || 0}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex gap-4 mb-4">
          <Input placeholder="Search student..." value={filters.search} onChange={(e) => setFilters({...filters, search: e.target.value})} />
          <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="unpaid">Unpaid</SelectItem>
              <SelectItem value="partial">Partial</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
              <SelectItem value="overdue">Overdue</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Invoice #</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Student</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Description</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Amount</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Paid</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Due Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">{inv.invoice_no}</td>
                  <td className="px-4 py-3 text-sm">{inv.students?.first_name} {inv.students?.last_name}</td>
                  <td className="px-4 py-3 text-sm">{inv.description}</td>
                  <td className="px-4 py-3 text-sm">${inv.amount}</td>
                  <td className="px-4 py-3 text-sm">${inv.paid_amount}</td>
                  <td className="px-4 py-3 text-sm">{new Date(inv.due_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3"><Badge className={getStatusColor(inv.status)}>{inv.status}</Badge></td>
                  <td className="px-4 py-3">
                    <Button size="sm" variant="outline" onClick={() => { setSelectedInvoice(inv); setShowPaymentModal(true); }}>Record Payment</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Invoice</DialogTitle></DialogHeader>
          <form onSubmit={handleCreateInvoice} className="space-y-4">
            <div><Label>Student ID</Label><Input name="student_id" required /></div>
            <div><Label>Description</Label><Input name="description" required /></div>
            <div><Label>Amount</Label><Input name="amount" type="number" step="0.01" required /></div>
            <div><Label>Term ID</Label><Input name="term_id" required /></div>
            <div><Label>Due Date</Label><Input name="due_date" type="date" required /></div>
            <Button type="submit">Create Invoice</Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Record Payment</DialogTitle></DialogHeader>
          <form onSubmit={handleRecordPayment} className="space-y-4">
            <div><Label>Amount</Label><Input name="amount" type="number" step="0.01" max={selectedInvoice?.balance} required /></div>
            <div><Label>Payment Method</Label>
              <Select name="payment_method" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="card">Card</SelectItem>
                  <SelectItem value="transfer">Bank Transfer</SelectItem>
                  <SelectItem value="mobile">Mobile Money</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Payment Date</Label><Input name="payment_date" type="date" required /></div>
            <div><Label>Reference Number</Label><Input name="reference_number" /></div>
            <Button type="submit">Record Payment</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
