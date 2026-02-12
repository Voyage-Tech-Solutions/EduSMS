"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Upload, FileText, Clock, BookOpen } from "lucide-react";

export default function ParentAssignmentsPage() {
  const [assignments, setAssignments] = useState<any>([]);
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/parent/children")
      .then(res => res.json())
      .then(data => {
        setChildren(data.children || []);
        if (data.children?.length > 0) setSelectedChild(data.children[0].student_id);
      });
  }, []);

  useEffect(() => {
    if (selectedChild) fetchAssignments();
  }, [selectedChild]);

  const fetchAssignments = async () => {
    const response = await fetch(`/api/v1/parent/assignments?student_id=${selectedChild}`);
    const data = await response.json();
    setAssignments(data.assignments || []);
    setLoading(false);
  };

  const getStatusBadge = (status: string) => {
    const colors: any = {
      pending: "bg-yellow-100 text-yellow-800",
      submitted: "bg-blue-100 text-blue-800",
      late: "bg-red-100 text-red-800",
      graded: "bg-green-100 text-green-800"
    };
    return <Badge className={colors[status] || ""}>{status}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BookOpen className="w-8 h-8" />
            Assignments & Homework
          </h1>
          <p className="text-muted-foreground">Track and submit assignments</p>
        </div>
        {children.length > 1 && (
          <Select value={selectedChild} onValueChange={setSelectedChild}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select Child" />
            </SelectTrigger>
            <SelectContent>
              {children.map((child) => (
                <SelectItem key={child.student_id} value={child.student_id}>
                  {child.student_name} - {child.grade_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assignments.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {assignments.filter((a: any) => a.assignment_submissions?.[0]?.status === "pending").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Submitted</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {assignments.filter((a: any) => a.assignment_submissions?.[0]?.status === "submitted").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Graded</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {assignments.filter((a: any) => a.assignment_submissions?.[0]?.status === "graded").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Assignments Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Assignments</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center">Loading...</TableCell>
                </TableRow>
              ) : assignments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center">No assignments found</TableCell>
                </TableRow>
              ) : (
                assignments.map((assignment: any) => (
                  <TableRow key={assignment.id}>
                    <TableCell className="font-medium">{assignment.title}</TableCell>
                    <TableCell>{assignment.subjects?.name || "N/A"}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {new Date(assignment.due_date).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(assignment.assignment_submissions?.[0]?.status || "pending")}</TableCell>
                    <TableCell>{assignment.assignment_submissions?.[0]?.score || "-"}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <AssignmentDetailsDialog assignment={assignment} />
                        {assignment.assignment_submissions?.[0]?.status !== "graded" && (
                          <SubmitAssignmentDialog assignment={assignment} onSuccess={fetchAssignments} />
                        )}
                      </div>
                    </TableCell>
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

function AssignmentDetailsDialog({ assignment }: any) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm"><FileText className="w-4 h-4" /></Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{assignment.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Description</Label>
            <p className="text-sm text-muted-foreground">{assignment.description || "No description"}</p>
          </div>
          <div>
            <Label>Due Date</Label>
            <p className="text-sm">{new Date(assignment.due_date).toLocaleDateString()}</p>
          </div>
          {assignment.attachment_url && (
            <div>
              <Label>Attachment</Label>
              <Button variant="outline" size="sm" className="w-full">Download</Button>
            </div>
          )}
          {assignment.assignment_submissions?.[0]?.feedback && (
            <div>
              <Label>Teacher Feedback</Label>
              <p className="text-sm text-muted-foreground">{assignment.assignment_submissions[0].feedback}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SubmitAssignmentDialog({ assignment, onSuccess }: any) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState("");
  const [selectedChild, setSelectedChild] = useState("");

  useEffect(() => {
    fetch("/api/v1/parent/children")
      .then(res => res.json())
      .then(data => {
        if (data.children?.length > 0) setSelectedChild(data.children[0].student_id);
      });
  }, []);

  const handleSubmit = async () => {
    await fetch("/api/v1/parent/assignments/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assignment_id: assignment.id,
        student_id: selectedChild,
        submission_url: file
      }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Upload className="w-4 h-4 mr-1" />Submit</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Submit Assignment</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Upload File</Label>
            <Input type="file" onChange={(e) => setFile(e.target.value)} />
          </div>
          <div>
            <Label>Notes (Optional)</Label>
            <Textarea placeholder="Add any notes..." />
          </div>
          <Button onClick={handleSubmit} className="w-full">Submit Assignment</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
