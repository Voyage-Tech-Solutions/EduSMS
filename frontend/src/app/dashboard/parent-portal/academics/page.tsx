"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Download, TrendingUp, TrendingDown, GraduationCap } from "lucide-react";

export default function ParentAcademicsPage() {
  const [academics, setAcademics] = useState<any>({ subjects: [], assessments: [] });
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authFetch("/api/v1/parent/children")
      .then(res => res.json())
      .then(data => {
        setChildren(data.children || []);
        if (data.children?.length > 0) setSelectedChild(data.children[0].student_id);
      });
  }, []);

  useEffect(() => {
    if (selectedChild) fetchAcademics();
  }, [selectedChild]);

  const fetchAcademics = async () => {
    const response = await authFetch(`/api/v1/parent/academics?student_id=${selectedChild}`);
    const data = await response.json();
    setAcademics(data);
    setLoading(false);
  };

  const getStatusBadge = (status: string) => {
    const variants: any = { good: "default", at_risk: "destructive", failing: "destructive" };
    return <Badge variant={variants[status] || "outline"}>{status}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <GraduationCap className="w-8 h-8" />
            Academic Performance
          </h1>
          <p className="text-muted-foreground">Track your child's academic progress</p>
        </div>
        <div className="flex gap-2">
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
          <Button><Download className="w-4 h-4 mr-2" />Download Report Card</Button>
        </div>
      </div>

      {/* Overall Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold">{academics.overall_average || 0}%</div>
            <div className="flex-1">
              <Progress value={academics.overall_average || 0} className="h-3" />
            </div>
            <div>
              {academics.overall_average >= 70 ? (
                <TrendingUp className="w-6 h-6 text-green-500" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-500" />
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subject Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Subject Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Average</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {academics.subjects.map((subject: any) => (
                <TableRow key={subject.subject}>
                  <TableCell className="font-medium">{subject.subject}</TableCell>
                  <TableCell>{subject.average}%</TableCell>
                  <TableCell>
                    <Progress value={subject.average} className="w-32" />
                  </TableCell>
                  <TableCell>{getStatusBadge(subject.status)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Assessment History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Assessments</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Assessment</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Teacher Comment</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {academics.assessments.slice(0, 10).map((assessment: any) => (
                <TableRow key={assessment.id}>
                  <TableCell className="font-medium">{assessment.assessments?.title || "N/A"}</TableCell>
                  <TableCell>{assessment.assessments?.subjects?.name || "N/A"}</TableCell>
                  <TableCell>{assessment.score || "N/A"}</TableCell>
                  <TableCell>{assessment.assessments?.created_at ? new Date(assessment.assessments.created_at).toLocaleDateString() : "N/A"}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">-</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
