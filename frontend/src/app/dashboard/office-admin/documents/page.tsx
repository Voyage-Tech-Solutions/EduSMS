"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileText, CheckCircle, AlertTriangle, Upload, Download } from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);
  const [filters, setFilters] = useState({ status: "", type: "", search: "" });

  useEffect(() => {
    fetchSummary();
    fetchDocuments();
  }, [filters]);

  const fetchSummary = async () => {
    const res = await fetch("/api/v1/documents/compliance-summary");
    const data = await res.json();
    setSummary(data);
  };

  const fetchDocuments = async () => {
    const params = new URLSearchParams();
    if (filters.status) params.append("status", filters.status);
    if (filters.type) params.append("document_type", filters.type);
    
    const res = await fetch(`/api/v1/documents/documents?${params}`);
    const data = await res.json();
    setDocuments(data);
  };

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    await fetch("/api/v1/documents/documents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_type: formData.get("entity_type"),
        entity_id: formData.get("entity_id"),
        document_type: formData.get("document_type"),
        file_url: formData.get("file_url"),
        file_name: formData.get("file_name"),
        file_size: 0,
        mime_type: "application/pdf"
      })
    });
    
    setShowUploadModal(false);
    fetchDocuments();
    fetchSummary();
  };

  const handleVerify = async (verified: boolean) => {
    await fetch(`/api/v1/documents/documents/${selectedDoc.id}/verify`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verified })
    });
    
    setShowVerifyModal(false);
    fetchDocuments();
    fetchSummary();
  };

  const getStatusColor = (status: string) => {
    const colors: any = {
      missing: "bg-gray-500",
      uploaded: "bg-orange-500",
      verified: "bg-green-500",
      expired: "bg-red-500",
      rejected: "bg-red-700"
    };
    return colors[status] || "bg-gray-500";
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Documents & Compliance</h1>
          <p className="text-gray-600">Manage and verify school documentation</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
          <Button onClick={() => setShowUploadModal(true)}><Upload className="w-4 h-4 mr-2" />Upload Document</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Students</p>
              <p className="text-2xl font-bold">{summary.total_students || 0}</p>
            </div>
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Fully Compliant</p>
              <p className="text-2xl font-bold text-green-600">{summary.fully_compliant || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Missing Documents</p>
              <p className="text-2xl font-bold text-red-600">{summary.missing_docs || 0}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Expired Documents</p>
              <p className="text-2xl font-bold text-orange-600">{summary.expired_docs || 0}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Verification</p>
              <p className="text-2xl font-bold">{summary.pending_verification || 0}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex gap-4 mb-4">
          <Input placeholder="Search student..." value={filters.search} onChange={(e) => setFilters({...filters, search: e.target.value})} />
          <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="missing">Missing</SelectItem>
              <SelectItem value="uploaded">Uploaded</SelectItem>
              <SelectItem value="verified">Verified</SelectItem>
              <SelectItem value="expired">Expired</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Student</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Document Type</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Uploaded</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Verified</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Expiry</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">{doc.entity_id}</td>
                  <td className="px-4 py-3 text-sm">{doc.document_type}</td>
                  <td className="px-4 py-3"><Badge className={getStatusColor(doc.status)}>{doc.status}</Badge></td>
                  <td className="px-4 py-3 text-sm">{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "-"}</td>
                  <td className="px-4 py-3 text-sm">{doc.verified ? "Yes" : "No"}</td>
                  <td className="px-4 py-3 text-sm">{doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString() : "-"}</td>
                  <td className="px-4 py-3">
                    {doc.status === "uploaded" && (
                      <Button size="sm" variant="outline" onClick={() => { setSelectedDoc(doc); setShowVerifyModal(true); }}>Verify</Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Upload Document</DialogTitle></DialogHeader>
          <form onSubmit={handleUpload} className="space-y-4">
            <div><Label>Entity Type</Label>
              <Select name="entity_type" required>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="student">Student</SelectItem>
                  <SelectItem value="parent">Parent</SelectItem>
                  <SelectItem value="staff">Staff</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Entity ID</Label><Input name="entity_id" required /></div>
            <div><Label>Document Type</Label><Input name="document_type" required /></div>
            <div><Label>File URL</Label><Input name="file_url" required /></div>
            <div><Label>File Name</Label><Input name="file_name" required /></div>
            <Button type="submit">Upload</Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showVerifyModal} onOpenChange={setShowVerifyModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Verify Document</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <p>Document: {selectedDoc?.document_type}</p>
            <p>Status: {selectedDoc?.status}</p>
            <div className="flex gap-2">
              <Button onClick={() => handleVerify(true)} className="bg-green-600">Verify</Button>
              <Button onClick={() => handleVerify(false)} variant="destructive">Reject</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
