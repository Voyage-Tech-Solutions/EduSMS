"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Users, Download } from "lucide-react";

export default function MyChildrenPage() {
  const [children, setChildren] = useState<any[]>([]);

  useEffect(() => {
    authFetch("/api/v1/parent/children")
      .then(res => res.json())
      .then(data => setChildren(data.children || []));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="w-8 h-8" />
            My Children
          </h1>
          <p className="text-muted-foreground">Manage and monitor all your children</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Children Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Grade</TableHead>
                <TableHead>Attendance %</TableHead>
                <TableHead>Academic Avg</TableHead>
                <TableHead>Outstanding Fees</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {children.map((child) => (
                <TableRow key={child.student_id}>
                  <TableCell className="font-medium">{child.student_name}</TableCell>
                  <TableCell>{child.grade_name}</TableCell>
                  <TableCell>{child.attendance_rate}%</TableCell>
                  <TableCell>{child.academic_average}%</TableCell>
                  <TableCell className="text-red-600">${child.outstanding_fees}</TableCell>
                  <TableCell>
                    <Badge variant={child.status === "active" ? "default" : "destructive"}>{child.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => window.location.href = `/dashboard/parent-portal?student_id=${child.student_id}`}>
                        View Dashboard
                      </Button>
                      <Button size="sm" variant="outline">
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
