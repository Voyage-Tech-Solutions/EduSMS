"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Download, Flag, Mail, Edit } from "lucide-react";

export default function PrincipalStudentsPage() {
  const [students, setStudents] = useState<any>([]);
  const [summary, setSummary] = useState<any>({});
  const [filters, setFilters] = useState({ search: "", status: "", risk_level: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudents();
  }, [filters]);

  const fetchStudents = async () => {
    setLoading(true);
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/v1/principal/students?${params}`);
    const data = await response.json();
    setStudents(data.students || []);
    setSummary(data.summary || {});
    setLoading(false);
  };

  const getRiskBadge = (risk: string) => {
    if (!risk) return <Badge variant="outline">None</Badge>;
    const colors: any = { attendance: "bg-orange-500", academic: "bg-red-500", financial: "bg-yellow-500" };
    return <Badge className={colors[risk]}>{risk}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Students</h1>
          <p className="text-muted-foreground">Monitor student population health</p>
        </div>
        <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {[
          { label: "Total", value: summary.total || 0, color: "" },
          { label: "Active", value: summary.active || 0, color: "text-green-600" },
          { label: "Inactive", value: summary.inactive || 0, color: "text-gray-600" },
          { label: "Transferred", value: summary.transferred || 0, color: "text-blue-600" },
          { label: "At Risk", value: summary.at_risk || 0, color: "text-red-600" },
          { label: "Chronic Absent", value: summary.chronic_absentees || 0, color: "text-orange-600" },
          { label: "Below Pass", value: summary.academic_below_pass || 0, color: "text-red-600" },
        ].map((card, i) => (
          <Card key={i} className="cursor-pointer hover:bg-accent">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">{card.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input placeholder="Search name or admission #" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
            <Select value={filters.status} onValueChange={(v) => setFilters({ ...filters, status: v })}>
              <SelectTrigger><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.risk_level} onValueChange={(v) => setFilters({ ...filters, risk_level: v })}>
              <SelectTrigger><SelectValue placeholder="Risk Level" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Risk</SelectItem>
                <SelectItem value="attendance">Attendance</SelectItem>
                <SelectItem value="academic">Academic</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => setFilters({ search: "", status: "", risk_level: "" })}>Clear</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Admission #</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Grade</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Attendance %</TableHead>
                <TableHead>Academic Avg</TableHead>
                <TableHead>Outstanding</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={9} className="text-center">Loading...</TableCell></TableRow>
              ) : students.length === 0 ? (
                <TableRow><TableCell colSpan={9} className="text-center">No students found</TableCell></TableRow>
              ) : (
                students.map((student: any) => (
                  <TableRow key={student.id}>
                    <TableCell>{student.admission_number}</TableCell>
                    <TableCell className="font-medium">{student.name}</TableCell>
                    <TableCell>{student.grade}</TableCell>
                    <TableCell><Badge variant={student.status === "active" ? "default" : "secondary"}>{student.status}</Badge></TableCell>
                    <TableCell>{student.attendance_percentage}%</TableCell>
                    <TableCell>{student.academic_average}%</TableCell>
                    <TableCell>${student.outstanding_fees}</TableCell>
                    <TableCell>{getRiskBadge(student.risk_level)}</TableCell>
                    <TableCell><StudentActions student={student} onUpdate={fetchStudents} /></TableCell>
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

function StudentActions({ student, onUpdate }: any) {
  const [open, setOpen] = useState(false);
  const [intervention, setIntervention] = useState({ risk_type: "attendance", severity: "medium", notes: "" });

  const handleFlag = async () => {
    await fetch("/api/v1/principal/students/risk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: student.id, ...intervention }),
    });
    setOpen(false);
    onUpdate();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">Actions</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Actions - {student.name}</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="border p-4 rounded space-y-3">
            <h3 className="font-semibold flex items-center gap-2"><Flag className="w-4 h-4" />Flag Intervention</h3>
            <Select value={intervention.risk_type} onValueChange={(v) => setIntervention({ ...intervention, risk_type: v })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="attendance">Attendance</SelectItem>
                <SelectItem value="academic">Academic</SelectItem>
                <SelectItem value="financial">Financial</SelectItem>
              </SelectContent>
            </Select>
            <Select value={intervention.severity} onValueChange={(v) => setIntervention({ ...intervention, severity: v })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
            <Textarea placeholder="Notes" value={intervention.notes} onChange={(e) => setIntervention({ ...intervention, notes: e.target.value })} />
            <Button onClick={handleFlag} className="w-full">Flag</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
