"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Download, RefreshCw, Send } from "lucide-react";

export default function PrincipalAcademicPage() {
  const [summary, setSummary] = useState<any>({});
  const [grades, setGrades] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [showRequestModal, setShowRequestModal] = useState(false);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    const res = await authFetch("/api/v1/principal-dashboard/academic/summary");
    setSummary(await res.json());
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Academic Performance</h1>
          <p className="text-gray-600">Monitor school-wide academic visibility</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}><RefreshCw className="w-4 h-4 mr-2" />Refresh</Button>
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <p className="text-sm text-gray-600">Pass Rate</p>
          <p className="text-4xl font-bold">{summary.pass_rate || "N/A"}%</p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-gray-600">Assessment Completion</p>
          <p className="text-4xl font-bold">{summary.assessment_completion?.completion_rate || 0}%</p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-gray-600">Reports Submitted</p>
          <p className="text-4xl font-bold">{summary.reports_submitted?.submitted || 0}/{summary.reports_submitted?.expected || 0}</p>
        </Card>
      </div>

      <div className="flex gap-2">
        <Button>View Full Report</Button>
        <Button variant="outline" onClick={() => setShowRequestModal(true)}><Send className="w-4 h-4 mr-2" />Request Marking</Button>
      </div>

      <Dialog open={showRequestModal} onOpenChange={setShowRequestModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Request Marking Completion</DialogTitle></DialogHeader>
          <form className="space-y-4">
            <div><Label>Deadline</Label><Input type="date" required /></div>
            <div><Label>Message</Label><Textarea rows={4} /></div>
            <Button type="submit">Send Reminder</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
