"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Plus, Copy, Download, Upload, CheckCircle } from "lucide-react";

export default function TeacherPlanningPage() {
  const [plan, setPlan] = useState<any>({ weekly_grid: {}, resources: [] });
  const [week, setWeek] = useState("2024-W01");
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchPlan = async () => {
    if (!classId || !subjectId) return;
    setLoading(true);
    const response = await fetch(`/api/v1/teacher/planning?week=${week}&class_id=${classId}&subject_id=${subjectId}`);
    const data = await response.json();
    setPlan(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchPlan();
  }, [week, classId, subjectId]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Planning</h1>
          <p className="text-muted-foreground">Plan lessons, content coverage, and assessments</p>
        </div>
        <div className="flex gap-2">
          <AddLessonDialog onSuccess={fetchPlan} classId={classId} subjectId={subjectId} />
          <CopyWeekDialog currentWeek={week} onSuccess={fetchPlan} />
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input type="week" value={week} onChange={(e) => setWeek(e.target.value)} />
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
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="weekly">
        <TabsList>
          <TabsTrigger value="weekly">Weekly Planner</TabsTrigger>
          <TabsTrigger value="coverage">Curriculum Coverage</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="assessments">Assessment Plans</TabsTrigger>
        </TabsList>

        <TabsContent value="weekly">
          <div className="grid grid-cols-1 gap-4">
            {Object.entries(plan.weekly_grid || {}).map(([date, dayData]: any) => (
              <Card key={date}>
                <CardHeader>
                  <CardTitle className="text-lg">{new Date(date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</CardTitle>
                </CardHeader>
                <CardContent>
                  {dayData.lessons.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No lessons planned</p>
                  ) : (
                    <div className="space-y-3">
                      {dayData.lessons.map((lesson: any) => (
                        <div key={lesson.id} className="border p-3 rounded space-y-2">
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="font-semibold">{lesson.topic}</h4>
                              <p className="text-sm text-muted-foreground">{lesson.time_slot}</p>
                            </div>
                            <Badge variant={lesson.status === "delivered" ? "default" : "outline"}>{lesson.status}</Badge>
                          </div>
                          <p className="text-sm">{lesson.objectives}</p>
                          {lesson.homework && <p className="text-sm text-muted-foreground">Homework: {lesson.homework}</p>}
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => markDelivered(lesson.id)}>
                              <CheckCircle className="w-4 h-4 mr-1" />Mark Delivered
                            </Button>
                            <Button size="sm" variant="outline">Edit</Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="coverage">
          <Card>
            <CardContent className="pt-6">
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">Coverage Progress</span>
                  <span className="text-sm font-semibold">0%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: "0%" }}></div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground text-center py-8">Curriculum units will appear here</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Resources Library</CardTitle>
                <UploadResourceDialog onSuccess={fetchPlan} classId={classId} subjectId={subjectId} />
              </div>
            </CardHeader>
            <CardContent>
              {plan.resources.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No resources uploaded</p>
              ) : (
                <div className="space-y-2">
                  {plan.resources.map((resource: any) => (
                    <div key={resource.id} className="border p-3 rounded flex justify-between items-center">
                      <div>
                        <h4 className="font-medium">{resource.title}</h4>
                        <p className="text-sm text-muted-foreground">{resource.type}</p>
                      </div>
                      <Button size="sm" variant="outline">View</Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assessments">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Assessment Plans</CardTitle>
                <AddAssessmentPlanDialog onSuccess={fetchPlan} classId={classId} subjectId={subjectId} />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center py-8">No assessment plans</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );

  async function markDelivered(lessonId: string) {
    await fetch(`/api/v1/teacher/planning/lessons/${lessonId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "delivered" }),
    });
    fetchPlan();
  }
}

function AddLessonDialog({ onSuccess, classId, subjectId }: any) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ date: new Date().toISOString().split('T')[0], topic: "", objectives: "", homework: "" });

  const handleSubmit = async () => {
    await fetch("/api/v1/teacher/planning/lessons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, class_id: classId, subject_id: subjectId, term_id: "term1" }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Plus className="w-4 h-4 mr-2" />Add Lesson</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Add Lesson Plan</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Date</Label>
            <Input type="date" value={data.date} onChange={(e) => setData({ ...data, date: e.target.value })} />
          </div>
          <div>
            <Label>Topic</Label>
            <Input value={data.topic} onChange={(e) => setData({ ...data, topic: e.target.value })} />
          </div>
          <div>
            <Label>Learning Objectives</Label>
            <Textarea value={data.objectives} onChange={(e) => setData({ ...data, objectives: e.target.value })} />
          </div>
          <div>
            <Label>Homework</Label>
            <Input value={data.homework} onChange={(e) => setData({ ...data, homework: e.target.value })} />
          </div>
          <Button onClick={handleSubmit} className="w-full">Save Lesson Plan</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function CopyWeekDialog({ currentWeek, onSuccess }: any) {
  const [open, setOpen] = useState(false);

  const handleCopy = async () => {
    await fetch("/api/v1/teacher/planning/copy-week", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_week: currentWeek, to_week: currentWeek, copy_resources: true }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline"><Copy className="w-4 h-4 mr-2" />Copy Week</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Copy Previous Week</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Copy lesson plans from previous week</p>
          <Button onClick={handleCopy} className="w-full">Copy</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function UploadResourceDialog({ onSuccess, classId, subjectId }: any) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ title: "", type: "file", url: "" });

  const handleSubmit = async () => {
    await fetch("/api/v1/teacher/planning/resources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, class_id: classId, subject_id: subjectId }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Upload className="w-4 h-4 mr-2" />Upload</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Upload Resource</DialogTitle></DialogHeader>
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
                <SelectItem value="file">File</SelectItem>
                <SelectItem value="link">Link</SelectItem>
                <SelectItem value="video">Video</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>URL</Label>
            <Input value={data.url} onChange={(e) => setData({ ...data, url: e.target.value })} />
          </div>
          <Button onClick={handleSubmit} className="w-full">Upload</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AddAssessmentPlanDialog({ onSuccess, classId, subjectId }: any) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ title: "", type: "test", planned_date: new Date().toISOString().split('T')[0] });

  const handleSubmit = async () => {
    await fetch("/api/v1/teacher/planning/assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, class_id: classId, subject_id: subjectId, term_id: "term1" }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Plus className="w-4 h-4 mr-2" />Add Plan</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Add Assessment Plan</DialogTitle></DialogHeader>
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
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Planned Date</Label>
            <Input type="date" value={data.planned_date} onChange={(e) => setData({ ...data, planned_date: e.target.value })} />
          </div>
          <Button onClick={handleSubmit} className="w-full">Save Plan</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
