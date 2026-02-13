"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Plus } from "lucide-react";

export default function RiskManagementPage() {
  const [riskCases, setRiskCases] = useState<any[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInterventionModal, setShowInterventionModal] = useState(false);
  const [selectedCase, setSelectedCase] = useState<any>(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    const res = await authFetch("/api/v1/principal-dashboard/risk-cases");
    setRiskCases(await res.json());
  };

  const getSeverityColor = (severity: string) => {
    const colors: any = { low: "bg-yellow-500", medium: "bg-orange-500", high: "bg-red-500", critical: "bg-red-700" };
    return colors[severity] || "bg-gray-500";
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Students At Risk</h1>
          <p className="text-gray-600">Intervention queue and risk management</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}><Plus className="w-4 h-4 mr-2" />Open Case</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-gray-600">Total At Risk</p>
          <p className="text-3xl font-bold text-orange-600">{riskCases.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Open Cases</p>
          <p className="text-3xl font-bold">{riskCases.filter(c => c.status === 'open').length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">In Progress</p>
          <p className="text-3xl font-bold">{riskCases.filter(c => c.status === 'in_progress').length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Critical</p>
          <p className="text-3xl font-bold text-red-600">{riskCases.filter(c => c.severity === 'critical').length}</p>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">At Risk List</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">Student</th>
                <th className="px-4 py-3 text-left">Risk Type</th>
                <th className="px-4 py-3 text-left">Severity</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Opened</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {riskCases.map((riskCase) => (
                <tr key={riskCase.id}>
                  <td className="px-4 py-3">{riskCase.students?.first_name} {riskCase.students?.last_name}</td>
                  <td className="px-4 py-3">{riskCase.risk_type}</td>
                  <td className="px-4 py-3"><Badge className={getSeverityColor(riskCase.severity)}>{riskCase.severity}</Badge></td>
                  <td className="px-4 py-3"><Badge>{riskCase.status}</Badge></td>
                  <td className="px-4 py-3">{new Date(riskCase.opened_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <Button size="sm" variant="outline" onClick={() => { setSelectedCase(riskCase); setShowInterventionModal(true); }}>Add Intervention</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Open Risk Case</DialogTitle></DialogHeader>
          <form className="space-y-4">
            <div><Label>Student ID</Label><Input name="student_id" required /></div>
            <div><Label>Risk Type</Label>
              <Select name="risk_type" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="attendance">Attendance</SelectItem>
                  <SelectItem value="academic">Academic</SelectItem>
                  <SelectItem value="financial">Financial</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Severity</Label>
              <Select name="severity" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit">Open Case</Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showInterventionModal} onOpenChange={setShowInterventionModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Intervention</DialogTitle></DialogHeader>
          <form className="space-y-4">
            <div><Label>Intervention Type</Label>
              <Select name="intervention_type" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="call_parent">Call Parent</SelectItem>
                  <SelectItem value="meeting">Meeting</SelectItem>
                  <SelectItem value="counseling">Counseling</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Due Date</Label><Input name="due_date" type="date" required /></div>
            <div><Label>Notes</Label><Textarea name="notes" required /></div>
            <Button type="submit">Create Intervention</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
