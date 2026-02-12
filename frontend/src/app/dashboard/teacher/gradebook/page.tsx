"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Upload, Download, Lock, FileSpreadsheet } from "lucide-react";

export default function TeacherGradebookPage() {
  const [gradebook, setGradebook] = useState<any>({ assessments: [], students: [] });
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [termId, setTermId] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchGradebook = async () => {
    if (!classId || !subjectId) return;
    setLoading(true);
    const response = await fetch(`/api/v1/teacher/gradebook?class_id=${classId}&subject_id=${subjectId}&term_id=${termId}`);
    const data = await response.json();
    setGradebook(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchGradebook();
  }, [classId, subjectId, termId]);

  const updateScore = async (assessmentId: string, studentId: string, score: number) => {
    await fetch(`/api/v1/teacher/gradebook/assessments/${assessmentId}/scores`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([{ student_id: studentId, score }]),
    });
    fetchGradebook();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Gradebook</h1>
          <p className="text-muted-foreground">Manage assessments and marks</p>
        </div>
        <div className="flex gap-2">
          <AddAssessmentDialog onSuccess={fetchGradebook} classId={classId} subjectId={subjectId} termId={termId} />
          <ImportMarksDialog onSuccess={fetchGradebook} />
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
          {!gradebook.is_locked && <LockGradebookDialog classId={classId} subjectId={subjectId} termId={termId} onSuccess={fetchGradebook} />}
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select value={classId} onValueChange={setClassId}>
              <SelectTrigger><SelectValue placeholder="Select Class" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="class1">Class 1</SelectItem>
                <SelectItem value="class2">Class 2</SelectItem>
              </SelectContent>
            </Select>
            <Select value={subjectId} onValueChange={setSubjectId}>
              <SelectTrigger><SelectValue placeholder="Select Subject" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="math">Mathematics</SelectItem>
                <SelectItem value="english">English</SelectItem>
              </SelectContent>
            </Select>
            <Select value={termId} onValueChange={setTermId}>
              <SelectTrigger><SelectValue placeholder="Select Term" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="term1">Term 1</SelectItem>
                <SelectItem value="term2">Term 2</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {gradebook.is_locked && (
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-yellow-600" />
              <p className="font-semibold text-yellow-800">Gradebook is locked. Request unlock from principal to edit.</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="spreadsheet">
        <TabsList>
          <TabsTrigger value="spreadsheet">Spreadsheet View</TabsTrigger>
          <TabsTrigger value="assessments">Assessments</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="spreadsheet">
          <Card>
            <CardContent className="pt-6 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="sticky left-0 bg-background">Admission #</TableHead>
                    <TableHead className="sticky left-20 bg-background">Name</TableHead>
                    {gradebook.assessments.map((assessment: any) => (
                      <TableHead key={assessment.id} className="text-center min-w-[100px]">
                        {assessment.title}
                        <br />
                        <span className="text-xs text-muted-foreground">/{assessment.total_marks}</span>
                      </TableHead>
                    ))}
                    <TableHead className="text-center">Average %</TableHead>
                    <TableHead className="text-center">Rank</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={100} className="text-center">Loading...</TableCell></TableRow>
                  ) : gradebook.students.length === 0 ? (
                    <TableRow><TableCell colSpan={100} className="text-center">No students found</TableCell></TableRow>
                  ) : (
                    gradebook.students.map((student: any) => (
                      <TableRow key={student.student_id}>
                        <TableCell className="sticky left-0 bg-background">{student.admission_number}</TableCell>
                        <TableCell className="sticky left-20 bg-background font-medium">{student.name}</TableCell>
                        {gradebook.assessments.map((assessment: any) => (
                          <TableCell key={assessment.id} className="text-center">
                            <Input
                              type="number"
                              className="w-20 text-center"
                              value={student.scores[assessment.id] || ""}
                              onChange={(e) => updateScore(assessment.id, student.student_id, parseFloat(e.target.value))}
                              disabled={gradebook.is_locked}
                              max={assessment.total_marks}
                            />
                          </TableCell>
                        ))}
                        <TableCell className="text-center font-semibold">{student.average}%</TableCell>
                        <TableCell className="text-center">{student.rank}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assessments">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Total Marks</TableHead>
                    <TableHead>Entries</TableHead>
                    <TableHead>Missing</TableHead>
                    <TableHead>Class Avg</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gradebook.assessments.map((assessment: any) => (
                    <TableRow key={assessment.id}>
                      <TableCell className="font-medium">{assessment.title}</TableCell>
                      <TableCell>{assessment.type}</TableCell>
                      <TableCell>{assessment.date_assigned}</TableCell>
                      <TableCell>{assessment.total_marks}</TableCell>
                      <TableCell>0</TableCell>
                      <TableCell>0</TableCell>
                      <TableCell>0%</TableCell>
                      <TableCell>
                        <Button variant="outline" size="sm">Edit</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">Analytics charts coming soon</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AddAssessmentDialog({ onSuccess, classId, subjectId, termId }: any) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ title: "", type: "test", total_marks: 100, date_assigned: new Date().toISOString().split('T')[0] });

  const handleSubmit = async () => {
    await fetch("/api/v1/teacher/gradebook/assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, class_id: classId, subject_id: subjectId, term_id: termId }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Plus className="w-4 h-4 mr-2" />Add Assessment</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Add Assessment</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Title</Label>
            <Input value={data.title} onChange={(e) => setData({ ...data, title: e.target.value })} />
          </div>
          <div>
            <Label>Type</Label>
            <Select value={data.type} onValueChange={(v) => setData({ ...data, type: v })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="test">Test</SelectItem>
                <SelectItem value="exam">Exam</SelectItem>
                <SelectItem value="assignment">Assignment</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Total Marks</Label>
            <Input type="number" value={data.total_marks} onChange={(e) => setData({ ...data, total_marks: parseFloat(e.target.value) })} />
          </div>
          <div>
            <Label>Date</Label>
            <Input type="date" value={data.date_assigned} onChange={(e) => setData({ ...data, date_assigned: e.target.value })} />
          </div>
          <Button onClick={handleSubmit} className="w-full">Create Assessment</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ImportMarksDialog({ onSuccess }: any) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline"><Upload className="w-4 h-4 mr-2" />Import</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Import Marks</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Upload CSV with columns: admission_number, score</p>
          <Input type="file" accept=".csv" />
          <Button className="w-full">Import</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function LockGradebookDialog({ classId, subjectId, termId, onSuccess }: any) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");

  const handleLock = async () => {
    await fetch("/api/v1/teacher/gradebook/lock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ class_id: classId, subject_id: subjectId, term_id: termId, reason }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline"><Lock className="w-4 h-4 mr-2" />Lock</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Lock Gradebook</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Locking prevents further edits. Unlock requires principal approval.</p>
          <Textarea placeholder="Reason (optional)" value={reason} onChange={(e) => setReason(e.target.value)} />
          <Button onClick={handleLock} className="w-full">Lock Gradebook</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
