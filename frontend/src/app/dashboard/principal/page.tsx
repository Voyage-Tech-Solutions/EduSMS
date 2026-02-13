"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Users, TrendingUp, AlertTriangle, DollarSign, Download, RefreshCw, Calendar } from "lucide-react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function PrincipalDashboardPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<any>({});
  const [dateRange, setDateRange] = useState("last_30_days");
  const [loading, setLoading] = useState(true);
  const [customDateModal, setCustomDateModal] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  useEffect(() => {
    fetchSummary();
  }, [dateRange]);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`/api/v1/principal/summary?range=${dateRange}`);
      const data = await res.json();
      setSummary(data);
    } catch (error) {
      console.error("Failed to fetch summary", error);
    }
    setLoading(false);
  };

  const handleExportDashboard = async () => {
    window.open(`/api/v1/principal/export-dashboard?range=${dateRange}&format=pdf`, "_blank");
  };

  const handleCustomDateRange = () => {
    if (startDate && endDate) {
      setDateRange(`custom_${startDate}_${endDate}`);
      setCustomDateModal(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">School Performance Overview</h1>
          <p className="text-gray-600">Key insights, approvals, and risks across your school</p>
        </div>
        <div className="flex gap-2">
          <Select value={dateRange} onValueChange={(val) => val === "custom" ? setCustomDateModal(true) : setDateRange(val)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="this_week">This Week</SelectItem>
              <SelectItem value="last_30_days">Last 30 Days</SelectItem>
              <SelectItem value="this_term">This Term</SelectItem>
              <SelectItem value="custom">Custom Range</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchSummary} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />Refresh
          </Button>
          <Button variant="outline" onClick={handleExportDashboard}>
            <Download className="w-4 h-4 mr-2" />Export Dashboard
          </Button>
        </div>
      </div>

      {/* Enrollment & Risk Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/dashboard/principal/students')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Students</p>
              <p className="text-3xl font-bold">{summary.total_students || 0}</p>
              <Button variant="link" className="p-0 h-auto text-sm">View Students</Button>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/dashboard/principal/attendance')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Attendance Rate</p>
              <p className="text-3xl font-bold">{summary.attendance_rate || 0}%</p>
              <Button variant="link" className="p-0 h-auto text-sm">View Breakdown</Button>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer hover:shadow-lg transition bg-orange-50" onClick={() => router.push('/dashboard/principal/risk')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Students At Risk</p>
              <p className="text-3xl font-bold text-orange-600">{summary.students_at_risk || 0}</p>
              <Button variant="link" className="p-0 h-auto text-sm text-orange-600">Review Risk List</Button>
            </div>
            <AlertTriangle className="w-10 h-10 text-orange-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/dashboard/principal/finance')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Fee Collection</p>
              <p className="text-3xl font-bold">{summary.fee_collection_rate || 0}%</p>
              <p className="text-sm text-red-600">${summary.outstanding_balance || 0} outstanding</p>
              <Button variant="link" className="p-0 h-auto text-sm">View Arrears</Button>
            </div>
            <DollarSign className="w-10 h-10 text-green-500" />
          </div>
        </Card>
      </div>

      {/* Academic Performance Section */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Academic Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Pass Rate</p>
            <p className="text-2xl font-bold">{summary.academic?.pass_rate || 'N/A'}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Assessment Completion</p>
            <p className="text-2xl font-bold">{summary.academic?.assessment_completion || 'N/A'}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Reports Submitted</p>
            <p className="text-2xl font-bold">{summary.academic?.reports_submitted || 0}/{summary.academic?.reports_expected || 0}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => router.push('/dashboard/principal/academic')}>View Full Report</Button>
          <Button variant="outline">Request Missing Reports</Button>
          <Button variant="outline">Set Academic Targets</Button>
        </div>
      </Card>

      {/* Finance Overview Section */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Finance Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Collection Rate</p>
            <p className="text-2xl font-bold">{summary.finance?.collection_rate || 0}%</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Outstanding Balance</p>
            <p className="text-2xl font-bold">${summary.finance?.outstanding || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Overdue (30+ days)</p>
            <p className="text-2xl font-bold text-red-600">${summary.finance?.overdue_30 || 0}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => router.push('/dashboard/principal/finance')}>View Arrears List</Button>
          <Button variant="outline">Send Payment Reminder</Button>
          <Button variant="outline">Export Finance Summary</Button>
        </div>
      </Card>

      {/* Staff Insight Section */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Staff Insight</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Active Teachers</p>
            <p className="text-2xl font-bold">{summary.staff?.active_teachers || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Marking Complete</p>
            <p className="text-2xl font-bold">{summary.staff?.marking_complete_rate || 0}%</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Staff Absent Today</p>
            <p className="text-2xl font-bold">{summary.staff?.absent_today || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Late Submissions</p>
            <p className="text-2xl font-bold">{summary.staff?.late_submissions || 0}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => router.push('/dashboard/principal/staff')}>View Staff Attendance</Button>
          <Button variant="outline">Chase Late Submissions</Button>
          <Button variant="outline">Staff Performance Report</Button>
        </div>
      </Card>

      {/* Custom Date Range Modal */}
      <Dialog open={customDateModal} onOpenChange={setCustomDateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Custom Date Range</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Start Date</Label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div>
              <Label>End Date</Label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setCustomDateModal(false)}>Cancel</Button>
              <Button onClick={handleCustomDateRange}>Apply</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
