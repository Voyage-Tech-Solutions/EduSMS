"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CheckCircle, XCircle, Clock, AlertCircle } from "lucide-react";

export default function PrincipalApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [selectedApproval, setSelectedApproval] = useState<any>(null);
  const [decisionModal, setDecisionModal] = useState(false);
  const [filter, setFilter] = useState("pending");

  useEffect(() => {
    fetchSummary();
    fetchApprovals();
  }, [filter]);

  const fetchSummary = async () => {
    const res = await authFetch("/api/v1/principal/approvals/summary");
    const data = await res.json();
    setSummary(data);
  };

  const fetchApprovals = async () => {
    const res = await authFetch(`/api/v1/principal/approvals?status=${filter}`);
    const data = await res.json();
    setApprovals(data);
  };

  const handleDecision = async (decision: string, notes: string) => {
    await authFetch(`/api/v1/principal/approvals/${selectedApproval.id}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes })
    });
    setDecisionModal(false);
    fetchApprovals();
    fetchSummary();
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      high: "bg-red-100 text-red-800",
      medium: "bg-orange-100 text-orange-800",
      low: "bg-blue-100 text-blue-800"
    };
    return <span className={`px-2 py-1 rounded text-xs ${colors[priority as keyof typeof colors]}`}>{priority}</span>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Approvals Required</h1>
          <p className="text-gray-600">Centralized approval queue for governance</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 cursor-pointer" onClick={() => setFilter("pending")}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Pending</p>
              <p className="text-3xl font-bold">{summary.total_pending || 0}</p>
            </div>
            <Clock className="w-10 h-10 text-orange-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer bg-red-50" onClick={() => setFilter("high_priority")}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">High Priority</p>
              <p className="text-3xl font-bold text-red-600">{summary.high_priority || 0}</p>
            </div>
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Approved Today</p>
              <p className="text-3xl font-bold text-green-600">{summary.approved_today || 0}</p>
            </div>
            <CheckCircle className="w-10 h-10 text-green-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Rejected Today</p>
              <p className="text-3xl font-bold">{summary.rejected_today || 0}</p>
            </div>
            <XCircle className="w-10 h-10 text-gray-500" />
          </div>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex gap-2">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="high_priority">High Priority</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Request ID</th>
                <th className="p-3 text-left">Type</th>
                <th className="p-3 text-left">Entity</th>
                <th className="p-3 text-left">Description</th>
                <th className="p-3 text-left">Priority</th>
                <th className="p-3 text-left">Submitted By</th>
                <th className="p-3 text-left">Date</th>
                <th className="p-3 text-left">Status</th>
                <th className="p-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {approvals.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center">
                    <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                    <p className="text-xl font-semibold text-green-600">All Clear!</p>
                    <p className="text-gray-600">No pending approvals at this time</p>
                  </td>
                </tr>
              ) : (
                approvals.map((approval) => (
                  <tr key={approval.id} className="border-t hover:bg-gray-50">
                    <td className="p-3 font-mono text-sm">{approval.id.slice(0, 8)}</td>
                    <td className="p-3">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                        {approval.type}
                      </span>
                    </td>
                    <td className="p-3">{approval.entity_name}</td>
                    <td className="p-3">{approval.description}</td>
                    <td className="p-3">{getPriorityBadge(approval.priority)}</td>
                    <td className="p-3">{approval.submitted_by_name}</td>
                    <td className="p-3">{new Date(approval.submitted_at).toLocaleDateString()}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        approval.status === 'pending' ? 'bg-orange-100 text-orange-800' :
                        approval.status === 'approved' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {approval.status}
                      </span>
                    </td>
                    <td className="p-3">
                      {approval.status === 'pending' && (
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => { setSelectedApproval(approval); setDecisionModal(true); }}>
                            Review
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={decisionModal} onOpenChange={setDecisionModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Approval Decision</DialogTitle>
          </DialogHeader>
          {selectedApproval && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Type</p>
                    <p className="font-semibold">{selectedApproval.type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Priority</p>
                    <p className="font-semibold">{selectedApproval.priority}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Entity</p>
                    <p className="font-semibold">{selectedApproval.entity_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Submitted By</p>
                    <p className="font-semibold">{selectedApproval.submitted_by_name}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-sm text-gray-600">Description</p>
                  <p>{selectedApproval.description}</p>
                </div>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); const formData = new FormData(e.currentTarget); handleDecision(formData.get("decision") as string, formData.get("notes") as string); }} className="space-y-4">
                <div>
                  <Label>Decision</Label>
                  <Select name="decision" required>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="approved">Approve</SelectItem>
                      <SelectItem value="rejected">Reject</SelectItem>
                      <SelectItem value="more_info">Request More Info</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Notes</Label>
                  <Textarea name="notes" placeholder="Add your decision notes..." required />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button type="button" variant="outline" onClick={() => setDecisionModal(false)}>Cancel</Button>
                  <Button type="submit">Submit Decision</Button>
                </div>
              </form>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
