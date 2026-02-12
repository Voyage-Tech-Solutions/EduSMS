"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Users, TrendingUp, DollarSign, Download, FileText } from "lucide-react";

export default function ReportsPage() {
  const [summary, setSummary] = useState<any>({});
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportType, setReportType] = useState("");

  useEffect(() => {
    fetchSummary();
  }, [dateRange]);

  const fetchSummary = async () => {
    const params = new URLSearchParams();
    if (dateRange.start) params.append("start_date", dateRange.start);
    if (dateRange.end) params.append("end_date", dateRange.end);
    
    const res = await fetch(`/api/v1/reports/summary?${params}`);
    const data = await res.json();
    setSummary(data);
  };

  const handleGenerateReport = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const endpoint = reportType === "student-directory" ? "/api/v1/reports/student-directory" : "/api/v1/reports/attendance-summary";
    
    const res = await fetch(endpoint, {
      method: "GET"
    });
    const data = await res.json();
    
    console.log("Report data:", data);
    setShowReportModal(false);
  };

  const setQuickRange = (range: string) => {
    const today = new Date();
    let start = new Date();
    
    switch(range) {
      case "today":
        start = today;
        break;
      case "week":
        start.setDate(today.getDate() - 7);
        break;
      case "month":
        start.setMonth(today.getMonth() - 1);
        break;
    }
    
    setDateRange({
      start: start.toISOString().split('T')[0],
      end: today.toISOString().split('T')[0]
    });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Reports & Analytics</h1>
          <p className="text-gray-600">Analytics and insights for your school</p>
        </div>
        <div className="flex gap-2">
          <Select onValueChange={setQuickRange}>
            <SelectTrigger className="w-40"><SelectValue placeholder="This Month" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export All</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Enrollment</p>
              <p className="text-2xl font-bold">{summary.total_enrollment || 0}</p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Attendance</p>
              <p className="text-2xl font-bold">{summary.avg_attendance?.toFixed(1) || 0}%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Fee Collection</p>
              <p className="text-2xl font-bold">${summary.fee_collection || 0}</p>
            </div>
            <DollarSign className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Collection Rate</p>
              <p className="text-2xl font-bold">{summary.collection_rate?.toFixed(1) || 0}%</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Reports</h3>
          <div className="space-y-2">
            <Button variant="outline" className="w-full justify-start" onClick={() => { setReportType("student-directory"); setShowReportModal(true); }}>
              <FileText className="w-4 h-4 mr-2" />Student Directory
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={() => { setReportType("fee-statement"); setShowReportModal(true); }}>
              <FileText className="w-4 h-4 mr-2" />Fee Statement
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={() => { setReportType("attendance-summary"); setShowReportModal(true); }}>
              <FileText className="w-4 h-4 mr-2" />Attendance Summary
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={() => { setReportType("grade-report"); setShowReportModal(true); }}>
              <FileText className="w-4 h-4 mr-2" />Grade Report
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Date Range Filter</h3>
          <div className="space-y-4">
            <div>
              <Label>Start Date</Label>
              <Input type="date" value={dateRange.start} onChange={(e) => setDateRange({...dateRange, start: e.target.value})} />
            </div>
            <div>
              <Label>End Date</Label>
              <Input type="date" value={dateRange.end} onChange={(e) => setDateRange({...dateRange, end: e.target.value})} />
            </div>
            <Button onClick={fetchSummary} className="w-full">Apply Filter</Button>
          </div>
        </Card>
      </div>

      <Dialog open={showReportModal} onOpenChange={setShowReportModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Generate Report</DialogTitle></DialogHeader>
          <form onSubmit={handleGenerateReport} className="space-y-4">
            {reportType === "student-directory" && (
              <>
                <div><Label>Grade</Label><Input name="grade_id" /></div>
                <div><Label>Class</Label><Input name="class_id" /></div>
              </>
            )}
            {reportType === "attendance-summary" && (
              <>
                <div><Label>Start Date</Label><Input name="start_date" type="date" /></div>
                <div><Label>End Date</Label><Input name="end_date" type="date" /></div>
              </>
            )}
            <div className="flex gap-2">
              <Button type="submit">Generate</Button>
              <Button type="button" variant="outline">Export PDF</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
