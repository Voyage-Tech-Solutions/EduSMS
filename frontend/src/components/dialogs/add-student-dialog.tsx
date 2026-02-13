"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

interface AddStudentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: any) => void;
}

export function AddStudentDialog({ open, onOpenChange, onSubmit }: AddStudentDialogProps) {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    gender: "",
    admission_date: new Date().toISOString().split('T')[0],
    grade: "",
    address: "",
    guardian_name: "",
    guardian_phone: "",
    guardian_email: "",
    guardian_relationship: "",
    blood_group: "",
    allergies: "",
    medical_conditions: "",
    emergency_contact: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({
      first_name: "",
      last_name: "",
      date_of_birth: "",
      gender: "",
      admission_date: new Date().toISOString().split('T')[0],
      grade: "",
      address: "",
      guardian_name: "",
      guardian_phone: "",
      guardian_email: "",
      guardian_relationship: "",
      blood_group: "",
      allergies: "",
      medical_conditions: "",
      emergency_contact: "",
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add Student</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">First Name</Label>
                <Input id="first_name" value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="last_name">Last Name</Label>
                <Input id="last_name" value={formData.last_name} onChange={(e) => setFormData({ ...formData, last_name: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="date_of_birth">Date of Birth</Label>
                <Input id="date_of_birth" type="date" placeholder="yyyy/mm/dd" value={formData.date_of_birth} onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="gender">Gender</Label>
                <Select value={formData.gender} onValueChange={(value) => setFormData({ ...formData, gender: value })}>
                  <SelectTrigger><SelectValue placeholder="Select gender" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="admission_date">Admission Date</Label>
                <Input id="admission_date" type="date" value={formData.admission_date} onChange={(e) => setFormData({ ...formData, admission_date: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="grade">Grade</Label>
                <Select value={formData.grade} onValueChange={(value) => setFormData({ ...formData, grade: value })}>
                  <SelectTrigger><SelectValue placeholder="Select grade" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="nursery">Nursery</SelectItem>
                    <SelectItem value="kg">KG</SelectItem>
                    <SelectItem value="1">Grade 1</SelectItem>
                    <SelectItem value="2">Grade 2</SelectItem>
                    <SelectItem value="3">Grade 3</SelectItem>
                    <SelectItem value="4">Grade 4</SelectItem>
                    <SelectItem value="5">Grade 5</SelectItem>
                    <SelectItem value="6">Grade 6</SelectItem>
                    <SelectItem value="7">Grade 7</SelectItem>
                    <SelectItem value="8">Grade 8</SelectItem>
                    <SelectItem value="9">Grade 9</SelectItem>
                    <SelectItem value="10">Grade 10</SelectItem>
                    <SelectItem value="11">Grade 11</SelectItem>
                    <SelectItem value="12">Grade 12</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2">
                <Label htmlFor="address">Address</Label>
                <Textarea id="address" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} rows={2} />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Parent Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="guardian_name">Guardian Name</Label>
                <Input id="guardian_name" value={formData.guardian_name} onChange={(e) => setFormData({ ...formData, guardian_name: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="guardian_relationship">Relationship</Label>
                <Select value={formData.guardian_relationship} onValueChange={(value) => setFormData({ ...formData, guardian_relationship: value })}>
                  <SelectTrigger><SelectValue placeholder="Select relationship" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="father">Father</SelectItem>
                    <SelectItem value="mother">Mother</SelectItem>
                    <SelectItem value="guardian">Guardian</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="guardian_phone">Phone Number</Label>
                <Input id="guardian_phone" type="tel" value={formData.guardian_phone} onChange={(e) => setFormData({ ...formData, guardian_phone: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="guardian_email">Email</Label>
                <Input id="guardian_email" type="email" value={formData.guardian_email} onChange={(e) => setFormData({ ...formData, guardian_email: e.target.value })} />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Medical Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="blood_group">Blood Group</Label>
                <Select value={formData.blood_group} onValueChange={(value) => setFormData({ ...formData, blood_group: value })}>
                  <SelectTrigger><SelectValue placeholder="Select blood group" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A+">A+</SelectItem>
                    <SelectItem value="A-">A-</SelectItem>
                    <SelectItem value="B+">B+</SelectItem>
                    <SelectItem value="B-">B-</SelectItem>
                    <SelectItem value="AB+">AB+</SelectItem>
                    <SelectItem value="AB-">AB-</SelectItem>
                    <SelectItem value="O+">O+</SelectItem>
                    <SelectItem value="O-">O-</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="emergency_contact">Emergency Contact</Label>
                <Input id="emergency_contact" type="tel" value={formData.emergency_contact} onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })} />
              </div>
              <div className="col-span-2">
                <Label htmlFor="allergies">Allergies</Label>
                <Textarea id="allergies" value={formData.allergies} onChange={(e) => setFormData({ ...formData, allergies: e.target.value })} placeholder="List any known allergies" rows={2} />
              </div>
              <div className="col-span-2">
                <Label htmlFor="medical_conditions">Medical Conditions</Label>
                <Textarea id="medical_conditions" value={formData.medical_conditions} onChange={(e) => setFormData({ ...formData, medical_conditions: e.target.value })} placeholder="List any medical conditions" rows={2} />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit">Add Student</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
