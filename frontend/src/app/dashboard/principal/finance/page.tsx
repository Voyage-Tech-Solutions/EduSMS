"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Download, Send } from "lucide-react";

export default function PrincipalFinancePage() {
  const [summary, setSummary] = useState<any>({});
  const [invoices, setInvoices] = useState<any[]>([]);
  const [showWriteoffModal, setShowWriteoffModal] = useState(false);
  const [showPaymentPlanModal, setShowPaymentPlanModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<any>(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    const res = await authFetch("/api/v1/principal-dashboard/finance/summary");
    setSummary(await res.json());
    const invRes = await authFetch("/api/v1/principal-dashboard/finance/arrears");
    setInvoices(await invRes.json());
  };

  const handleWriteoff = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    await authFetch("/api/v1/principal-dashboard/finance/writeoff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        invoice_id: selectedInvoice.id,
        amount: parseFloat(formData.get("amount") as string),
        reason: formData.get("reason"),
        notes: formData.get("notes")
      })
    });
    setShowWriteoffModal(false);
    fetchData();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Fees & Billing</h1>
          <p className="text-gray-600">Monitor revenue health and financial risk</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-gray-600">Total Billed</p>
          <p className="text-3xl font-bold">${summary.total_billed || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Total Collected</p>
          <p className="text-3xl font-bold text-green-600">${summary.total_collected || 0}</p>
          <p className="text-sm">{summary.collection_rate || 0}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Outstanding</p>
          <p className="text-3xl font-bold text-orange-600">${summary.outstanding || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Overdue (30+ days)</p>
          <p className="text-3xl font-bold text-red-600">${summary.overdue_30 || 0}</p>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Arrears List</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">Invoice #</th>
                <th className="px-4 py-3 text-left">Student</th>
                <th className="px-4 py-3 text-left">Amount</th>
                <th className="px-4 py-3 text-left">Paid</th>
                <th className="px-4 py-3 text-left">Balance</th>
                <th className="px-4 py-3 text-left">Due Date</th>
                <th className="px-4 py-3 text-left">Risk</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td className="px-4 py-3">{inv.invoice_number}</td>
                  <td className="px-4 py-3">{inv.students?.first_name} {inv.students?.last_name}</td>
                  <td className="px-4 py-3">${inv.amount}</td>
                  <td className="px-4 py-3">${inv.amount_paid}</td>
                  <td className="px-4 py-3">${inv.amount - inv.amount_paid}</td>
                  <td className="px-4 py-3">{new Date(inv.due_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <Badge className="bg-red-500">High</Badge>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <Button size="sm" variant="outline">Send Reminder</Button>
                    <Button size="sm" variant="outline" onClick={() => { setSelectedInvoice(inv); setShowWriteoffModal(true); }}>Write-off</Button>
                    <Button size="sm" variant="outline" onClick={() => { setSelectedInvoice(inv); setShowPaymentPlanModal(true); }}>Payment Plan</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={showWriteoffModal} onOpenChange={setShowWriteoffModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Approve Write-Off</DialogTitle></DialogHeader>
          <form onSubmit={handleWriteoff} className="space-y-4">
            <div><Label>Amount</Label><Input name="amount" type="number" step="0.01" max={selectedInvoice?.amount - selectedInvoice?.amount_paid} required /></div>
            <div><Label>Reason</Label><Textarea name="reason" required /></div>
            <div><Label>Notes</Label><Textarea name="notes" /></div>
            <Button type="submit">Approve Write-Off</Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showPaymentPlanModal} onOpenChange={setShowPaymentPlanModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Payment Plan</DialogTitle></DialogHeader>
          <form className="space-y-4">
            <div><Label>Installment Count</Label><Input type="number" required /></div>
            <div><Label>Start Date</Label><Input type="date" required /></div>
            <Button type="submit">Create Plan</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
