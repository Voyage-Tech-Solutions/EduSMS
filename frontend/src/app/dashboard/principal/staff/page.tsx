"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Download, Plus } from "lucide-react";

export default function PrincipalStaffPage() {
  const [staff, setStaff] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState<any>(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const res = await fetch("/api/v1/principal-dashboard/staff");
      if (res.ok) {
        setStaff(await res.json());
      } else {
        setStaff([]);
      }
    } catch (error) {
      console.error("Failed to fetch staff:", error);
      setStaff([]);
    }
  };

  const handleAddStaff = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const formData = new FormData(e.currentTarget);
      await fetch("/api/v1/staff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: formData.get("first_name"),
          last_name: formData.get("last_name"),
          email: formData.get("email"),
          phone: formData.get("phone"),
          role: formData.get("role")
        })
      });
      setShowAddModal(false);
      fetchData();
    } catch (error) {
      console.error("Failed to add staff:", error);
    }
  };

  const handleDeactivate = async () => {
    try {
      await fetch(`/api/v1/principal-dashboard/staff/${selectedStaff.id}/deactivate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Principal deactivation" })
      });
      setShowDeactivateModal(false);
      fetchData();
    } catch (error) {
      console.error("Failed to deactivate staff:", error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Staff Management</h1>
          <p className="text-gray-600">Manage school staff and teachers</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowAddModal(true)}><Plus className="w-4 h-4 mr-2" />Add Staff</Button>
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-gray-600">Total Staff</p>
          <p className="text-3xl font-bold">{staff.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Active Staff</p>
          <p className="text-3xl font-bold">{staff.filter(s => s.is_active).length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Teachers</p>
          <p className="text-3xl font-bold">{staff.filter(s => s.role === 'teacher').length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Admin Staff</p>
          <p className="text-3xl font-bold">{staff.filter(s => s.role === 'office_admin').length}</p>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Staff List</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Phone</th>
                <th className="px-4 py-3 text-left">Role</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {staff.map((member) => (
                <tr key={member.id}>
                  <td className="px-4 py-3">{member.first_name} {member.last_name}</td>
                  <td className="px-4 py-3">{member.email}</td>
                  <td className="px-4 py-3">{member.phone}</td>
                  <td className="px-4 py-3">{member.role}</td>
                  <td className="px-4 py-3">
                    <Badge className={member.is_active ? "bg-green-500" : "bg-gray-500"}>
                      {member.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <Button size="sm" variant="outline">View Profile</Button>
                    <Button size="sm" variant="outline">Edit</Button>
                    {member.is_active && (
                      <Button size="sm" variant="destructive" onClick={() => { setSelectedStaff(member); setShowDeactivateModal(true); }}>Deactivate</Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Staff Member</DialogTitle></DialogHeader>
          <form onSubmit={handleAddStaff} className="space-y-4">
            <div><Label>First Name</Label><Input name="first_name" required /></div>
            <div><Label>Last Name</Label><Input name="last_name" required /></div>
            <div><Label>Email</Label><Input name="email" type="email" required /></div>
            <div><Label>Phone</Label><Input name="phone" /></div>
            <div>
              <Label>Role</Label>
              <Select name="role" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="teacher">Teacher</SelectItem>
                  <SelectItem value="office_admin">Office Admin</SelectItem>
                  <SelectItem value="finance">Finance Officer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit">Add Staff</Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showDeactivateModal} onOpenChange={setShowDeactivateModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Deactivate Staff Member</DialogTitle></DialogHeader>
          <p>Are you sure you want to deactivate {selectedStaff?.first_name} {selectedStaff?.last_name}?</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setShowDeactivateModal(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeactivate}>Deactivate</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
