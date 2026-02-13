"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Plus, Edit, Trash2 } from "lucide-react";

interface Grade {
  id: string;
  name: string;
  order_index: number;
  active: boolean;
  description?: string;
  student_count?: number;
}

export default function GradesPage() {
  const [grades, setGrades] = useState<Grade[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingGrade, setEditingGrade] = useState<Grade | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    order_index: 1,
    active: true,
    description: "",
  });

  useEffect(() => {
    loadGrades();
  }, []);

  const loadGrades = async () => {
    // API call
  };

  const handleSubmit = async () => {
    // API call
    setShowDialog(false);
    resetForm();
  };

  const handleDelete = async (grade: Grade) => {
    if (grade.student_count && grade.student_count > 0) {
      alert("Cannot delete grade with students. Deactivate instead.");
      return;
    }
    // API call
  };

  const resetForm = () => {
    setFormData({ name: "", order_index: 1, active: true, description: "" });
    setEditingGrade(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Grade Management</h1>
          <p className="text-gray-600 mt-1">Configure academic grade structure</p>
        </div>
        <Button onClick={() => { resetForm(); setShowDialog(true); }}>
          <Plus className="mr-2 h-4 w-4" /> Add Grade
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Grades ({grades.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order</TableHead>
                <TableHead>Grade Name</TableHead>
                <TableHead>Students</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {grades.map((grade) => (
                <TableRow key={grade.id}>
                  <TableCell>{grade.order_index}</TableCell>
                  <TableCell className="font-medium">{grade.name}</TableCell>
                  <TableCell>{grade.student_count || 0}</TableCell>
                  <TableCell>
                    <Badge variant={grade.active ? "default" : "secondary"}>
                      {grade.active ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => { setEditingGrade(grade); setFormData({ ...grade, description: grade.description || "" }); setShowDialog(true); }}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(grade)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingGrade ? "Edit Grade" : "Add Grade"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Grade Name *</Label>
              <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Grade 1" />
            </div>
            <div>
              <Label>Order Index *</Label>
              <Input type="number" value={formData.order_index} onChange={(e) => setFormData({ ...formData, order_index: parseInt(e.target.value) })} />
            </div>
            <div>
              <Label>Description</Label>
              <Input value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="Optional" />
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={formData.active} onCheckedChange={(checked) => setFormData({ ...formData, active: checked })} />
              <Label>Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
            <Button onClick={handleSubmit}>{editingGrade ? "Save" : "Add Grade"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
