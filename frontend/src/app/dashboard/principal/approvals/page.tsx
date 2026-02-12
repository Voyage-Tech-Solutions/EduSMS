"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { CheckCircle, XCircle, AlertCircle } from "lucide-react";

export default function PrincipalApprovalsPage() {
  const [approvals, setApprovals] = useState<any>([]);
  const [summary, setSummary] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApprovals();
  }, []);

  const fetchApprovals = async () => {
    setLoading(true);
    const response = await fetch("/api/v1/principal/approvals?status=pending");
    const data = await response.json();
    setApprovals(data.approvals || []);
    setSummary(data.summary || {});
    setLoading(false);
  };

  const getPriorityBadge = (priority: string) => {
    const colors: any = { low: "bg-gray-500", normal: "bg-blue-500", high: "bg-orange-500", urgent: "bg-red-500" };
    return <Badge className={colors[priority]}>{priority}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Approvals Required</h1>
        <p className="text-muted-foreground">Centralized approval queue for governance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_pending || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">High Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{summary.high_priority || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Categories Clear</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {summary.total_pending === 0 ? "✓ All Clear" : "Pending"}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Request ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Submitted By</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={8} className="text-center">Loading...</TableCell></TableRow>
              ) : approvals.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">
                    <div className="py-8">
                      <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                      <p className="text-lg font-semibold">All Clear!</p>
                      <p className="text-muted-foreground">No pending approvals</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                approvals.map((approval: any) => (
                  <TableRow key={approval.id}>
                    <TableCell className="font-mono">{approval.request_id}</TableCell>
                    <TableCell><Badge variant="outline">{approval.type}</Badge></TableCell>
                    <TableCell>{approval.entity_name}</TableCell>
                    <TableCell>{approval.description}</TableCell>
                    <TableCell>{getPriorityBadge(approval.priority)}</TableCell>
                    <TableCell>{approval.submitted_by}</TableCell>
                    <TableCell>{new Date(approval.submitted_at).toLocaleDateString()}</TableCell>
                    <TableCell><ApprovalActions approval={approval} onUpdate={fetchApprovals} /></TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function ApprovalActions({ approval, onUpdate }: any) {
  const [open, setOpen] = useState(false);
  const [decision, setDecision] = useState({ decision: "approved", notes: "", notify_requester: true });

  const handleDecision = async () => {
    await fetch(`/api/v1/principal/approvals/${approval.id}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(decision),
    });
    setOpen(false);
    onUpdate();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">Review</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Approval Decision</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Type</Label>
            <p className="text-sm text-muted-foreground">{approval.type}</p>
          </div>
          <div>
            <Label>Entity</Label>
            <p className="text-sm text-muted-foreground">{approval.entity_name}</p>
          </div>
          <div>
            <Label>Description</Label>
            <p className="text-sm text-muted-foreground">{approval.description}</p>
          </div>
          <div>
            <Label>Decision</Label>
            <div className="flex gap-2 mt-2">
              <Button
                variant={decision.decision === "approved" ? "default" : "outline"}
                onClick={() => setDecision({ ...decision, decision: "approved" })}
                className="flex-1"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Approve
              </Button>
              <Button
                variant={decision.decision === "rejected" ? "destructive" : "outline"}
                onClick={() => setDecision({ ...decision, decision: "rejected" })}
                className="flex-1"
              >
                <XCircle className="w-4 h-4 mr-2" />
                Reject
              </Button>
            </div>
          </div>
          <div>
            <Label>Notes {decision.decision === "rejected" && "(Required)"}</Label>
            <Textarea
              placeholder="Add notes..."
              value={decision.notes}
              onChange={(e) => setDecision({ ...decision, notes: e.target.value })}
              className="mt-2"
            />
          </div>
          <Button onClick={handleDecision} className="w-full" disabled={decision.decision === "rejected" && !decision.notes}>
            Submit Decision
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
