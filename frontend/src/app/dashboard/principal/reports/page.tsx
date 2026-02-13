"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Download, FileText, TrendingUp, DollarSign, Users, BookOpen } from "lucide-react";

export default function PrincipalReportsPage() {
  const [summary, setSummary] = useState<any>({});
  const [dateRange, setDateRange] = useState("this_term");
  const [reportModal, setReportModal] = useState(false);
  const [reportType, setReportType] = useState("");

  useEffect(() => {
    fetchSummary();
  }, [dateRange]);

  const fetchSummary = async () => {
    const res = await authFetch(`/api/v1/principal/reports/summary?range=${dateRange}`);
    const data = await res.json();
    setSummary(data);
  };

  const generateReport = async (type: string, filters: any) => {
    if (typeof window === 'undefined') return;
    const res = await authFetch("/api/v1/principal/reports/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, filters, range: dateRange })
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${type}_report.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Reports & Analytics</h1>
          <p className="text-gray-600">Executive-level insights and performance tracking</p>
        </div>
        <div className="flex gap-2">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="this_month">This Month</SelectItem>
              <SelectItem value="this_term">This Term</SelectItem>
              <SelectItem value="this_year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button><Download className="w-4 h-4 mr-2" />Export All</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Enrollment</p>
              <p className="text-3xl font-bold">{summary.total_enrollment || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Attendance</p>
              <p className="text-3xl font-bold">{summary.avg_attendance || 0}%</p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Fee Collection</p>
              <p className="text-3xl font-bold">${summary.fee_collection || 0}</p>
            </div>
            <DollarSign className="w-10 h-10 text-green-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Academic Avg</p>
              <p className="text-3xl font-bold">{summary.academic_avg || 0}%</p>
            </div>
            <BookOpen className="w-10 h-10 text-purple-500" />
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Reports</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button variant="outline" className="h-20 flex flex-col items-start justify-center" onClick={() => { setReportType("student_directory"); setReportModal(true); }}>
            <FileText className="w-5 h-5 mb-2" />
            <span className="font-semibold">Student Directory</span>
          </Button>
          <Button variant="outline" className="h-20 flex flex-col items-start justify-center" onClick={() => { setReportType("fee_statement"); setReportModal(true); }}>
            <FileText className="w-5 h-5 mb-2" />
            <span className="font-semibold">Fee Statement</span>
          </Button>
          <Button variant="outline" className="h-20 flex flex-col items-start justify-center" onClick={() => { setReportType("attendance_summary"); setReportModal(true); }}>
            <FileText className="w-5 h-5 mb-2" />
            <span className="font-semibold">Attendance Summary</span>
          </Button>
          <Button variant="outline" className="h-20 flex flex-col items-start justify-center" onClick={() => { setReportType("grade_report"); setReportModal(true); }}>
            <FileText className="w-5 h-5 mb-2" />
            <span className="font-semibold">Grade Report</span>
          </Button>
        </div>
      </Card>

      <Dialog open={reportModal} onOpenChange={setReportModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Generate Report</DialogTitle></DialogHeader>
          <form onSubmit={(e) => { e.preventDefault(); const formData = new FormData(e.currentTarget); generateReport(reportType, Object.fromEntries(formData)); setReportModal(false); }} className="space-y-4">
            <div>
              <Label>Grade</Label>
              <Select name="grade">
                <SelectTrigger><SelectValue placeholder="All Grades" /></SelectTrigger>
                <SelectContent><SelectItem value="all">All Grades</SelectItem></SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={() => setReportModal(false)}>Cancel</Button>
              <Button type="submit">Generate</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
