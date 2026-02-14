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
import { Users, AlertTriangle, TrendingDown, UserX, Download, Flag } from "lucide-react";

export default function PrincipalStudentsPage() {
  const [students, setStudents] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [filters, setFilters] = useState({ search: "", grade: "", status: "active", risk: "" });
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [interventionModal, setInterventionModal] = useState(false);
  const [statusModal, setStatusModal] = useState(false);
  const [notifyModal, setNotifyModal] = useState(false);

  useEffect(() => {
    fetchSummary();
    fetchStudents();
  }, [filters]);

  const fetchSummary = async () => {
    try {
      const res = await authFetch("/api/v1/principal/students/summary");
      const data = await res.json();
      setSummary(data || {});
    } catch (error) {
      console.error('Failed to fetch summary:', error);
      setSummary({});
    }
  };

  const fetchStudents = async () => {
    try {
      const params = new URLSearchParams(filters as any);
      const res = await authFetch(`/api/v1/principal/students?${params}`);
      const data = await res.json();
      setStudents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch students:', error);
      setStudents([]);
    }
  };

  const handleFlagIntervention = async (data: any) => {
    await authFetch("/api/v1/principal/students/risk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, student_id: selectedStudent.id })
    });
    setInterventionModal(false);
    fetchStudents();
  };

  const handleChangeStatus = async (data: any) => {
    await authFetch(`/api/v1/principal/students/${selectedStudent.id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    setStatusModal(false);
    fetchStudents();
  };

  const getRiskBadge = (student: any) => {
    const risks = [];
    if (student.attendance_rate < 75) risks.push("Attendance");
    if (student.academic_avg < 50) risks.push("Academic");
    if (student.outstanding > 0) risks.push("Finance");
    if (risks.length === 0) return <span className="text-green-600">None</span>;
    if (risks.length > 1) return <span className="text-red-600 font-semibold">Multi-risk</span>;
    return <span className="text-orange-600">{risks[0]}</span>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Students</h1>
          <p className="text-gray-600">Monitor student population health and risks</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 cursor-pointer" onClick={() => setFilters({...filters, status: "active"})}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Students</p>
              <p className="text-3xl font-bold">{summary.total || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer bg-orange-50" onClick={() => setFilters({...filters, risk: "any"})}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Students At Risk</p>
              <p className="text-3xl font-bold text-orange-600">{summary.at_risk || 0}</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-orange-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer" onClick={() => setFilters({...filters, risk: "attendance"})}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Chronic Absentees</p>
              <p className="text-3xl font-bold">{summary.chronic_absent || 0}</p>
            </div>
            <TrendingDown className="w-10 h-10 text-red-500" />
          </div>
        </Card>

        <Card className="p-4 cursor-pointer" onClick={() => setFilters({...filters, status: "inactive"})}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Inactive</p>
              <p className="text-3xl font-bold">{summary.inactive || 0}</p>
            </div>
            <UserX className="w-10 h-10 text-gray-500" />
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Input placeholder="Search name or admission #" value={filters.search} onChange={(e) => setFilters({...filters, search: e.target.value})} />
          <Select value={filters.grade} onValueChange={(val) => setFilters({...filters, grade: val})}>
            <SelectTrigger><SelectValue placeholder="All Grades" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Grades</SelectItem>
              <SelectItem value="grade1">Grade 1</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.status} onValueChange={(val) => setFilters({...filters, status: val})}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
              <SelectItem value="transferred">Transferred</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.risk} onValueChange={(val) => setFilters({...filters, risk: val})}>
            <SelectTrigger><SelectValue placeholder="All Risk Levels" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Risk Levels</SelectItem>
              <SelectItem value="any">Any Risk</SelectItem>
              <SelectItem value="attendance">Attendance Risk</SelectItem>
              <SelectItem value="academic">Academic Risk</SelectItem>
              <SelectItem value="finance">Finance Risk</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchStudents}>Apply Filters</Button>
        </div>
      </Card>

      {/* Students Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Admission #</th>
                <th className="p-3 text-left">Name</th>
                <th className="p-3 text-left">Grade</th>
                <th className="p-3 text-left">Status</th>
                <th className="p-3 text-left">Attendance %</th>
                <th className="p-3 text-left">Academic Avg</th>
                <th className="p-3 text-left">Outstanding</th>
                <th className="p-3 text-left">Risk</th>
                <th className="p-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-gray-500">
                    No students found matching the filters
                  </td>
                </tr>
              ) : students.map((student) => (
                <tr key={student.id} className="border-t hover:bg-gray-50">
                  <td className="p-3">{student.admission_number}</td>
                  <td className="p-3 font-medium">{student.first_name} {student.last_name}</td>
                  <td className="p-3">{student.grade_name}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${student.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {student.status}
                    </span>
                  </td>
                  <td className="p-3">{student.attendance_rate || 0}%</td>
                  <td className="p-3">{student.academic_avg || 'N/A'}</td>
                  <td className="p-3">${student.outstanding || 0}</td>
                  <td className="p-3">{getRiskBadge(student)}</td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => { setSelectedStudent(student); setInterventionModal(true); }}>
                        <Flag className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => { setSelectedStudent(student); setStatusModal(true); }}>
                        Status
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Flag Intervention Modal */}
      <Dialog open={interventionModal} onOpenChange={setInterventionModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Flag for Intervention</DialogTitle>
          </DialogHeader>
          <form onSubmit={(e) => { e.preventDefault(); const formData = new FormData(e.currentTarget); handleFlagIntervention(Object.fromEntries(formData)); }} className="space-y-4">
            <div>
              <Label>Risk Type</Label>
              <Select name="risk_type" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="attendance">Attendance</SelectItem>
                  <SelectItem value="academic">Academic</SelectItem>
                  <SelectItem value="financial">Financial</SelectItem>
                  <SelectItem value="behavioral">Behavioral</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Severity</Label>
              <Select name="severity" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea name="notes" required />
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={() => setInterventionModal(false)}>Cancel</Button>
              <Button type="submit">Create Intervention</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Change Status Modal */}
      <Dialog open={statusModal} onOpenChange={setStatusModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Student Status</DialogTitle>
          </DialogHeader>
          <form onSubmit={(e) => { e.preventDefault(); const formData = new FormData(e.currentTarget); handleChangeStatus(Object.fromEntries(formData)); }} className="space-y-4">
            <div>
              <Label>New Status</Label>
              <Select name="status" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="transferred">Transferred</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Reason</Label>
              <Textarea name="reason" required />
            </div>
            <div>
              <Label>Effective Date</Label>
              <Input type="date" name="effective_date" required />
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={() => setStatusModal(false)}>Cancel</Button>
              <Button type="submit">Update Status</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
