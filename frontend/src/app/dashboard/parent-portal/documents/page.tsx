"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Upload, Download, FileText, CheckCircle, XCircle, Clock } from "lucide-react";

export default function ParentDocumentsPage() {
  const [documents, setDocuments] = useState<any>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    const studentId = "student-id";
    const response = await authFetch(`/api/v1/parent/documents?student_id=${studentId}`);
    const data = await response.json();
    setDocuments(data.documents || []);
    setLoading(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "verified": return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "pending": return <Clock className="w-5 h-5 text-yellow-500" />;
      case "missing": return <XCircle className="w-5 h-5 text-red-500" />;
      case "expired": return <XCircle className="w-5 h-5 text-orange-500" />;
      default: return <FileText className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: any = {
      verified: "bg-green-100 text-green-800",
      pending: "bg-yellow-100 text-yellow-800",
      missing: "bg-red-100 text-red-800",
      expired: "bg-orange-100 text-orange-800"
    };
    return <Badge className={colors[status] || ""}>{status}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Documents</h1>
          <p className="text-muted-foreground">Manage student documents</p>
        </div>
        <UploadDocumentDialog onSuccess={fetchDocuments} />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{documents.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Verified</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {documents.filter((d: any) => d.status === "verified").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {documents.filter((d: any) => d.status === "pending").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Missing/Expired</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {documents.filter((d: any) => d.status === "missing" || d.status === "expired").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>Document List</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Document Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Uploaded Date</TableHead>
                <TableHead>Expiry Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">Loading...</TableCell>
                </TableRow>
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">No documents found</TableCell>
                </TableRow>
              ) : (
                documents.map((doc: any) => (
                  <TableRow key={doc.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(doc.status)}
                        <span className="font-medium">{doc.document_type}</span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(doc.status)}</TableCell>
                    <TableCell>{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "N/A"}</TableCell>
                    <TableCell>{doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString() : "N/A"}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {doc.file_url && (
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4" />
                          </Button>
                        )}
                        {doc.status === "missing" && (
                          <UploadDocumentDialog documentType={doc.document_type} onSuccess={fetchDocuments} />
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

function UploadDocumentDialog({ documentType, onSuccess }: any) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({
    document_type: documentType || "",
    file_url: "",
    expiry_date: ""
  });

  const handleUpload = async () => {
    const studentId = "student-id";
    await authFetch("/api/v1/parent/documents/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, ...data }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Upload className="w-4 h-4 mr-2" />
          Upload Document
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Document Type</Label>
            <Select value={data.document_type} onValueChange={(v) => setData({ ...data, document_type: v })}>
              <SelectTrigger>
                <SelectValue placeholder="Select document type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="birth_certificate">Birth Certificate</SelectItem>
                <SelectItem value="medical_records">Medical Records</SelectItem>
                <SelectItem value="immunization_card">Immunization Card</SelectItem>
                <SelectItem value="previous_report">Previous Report Card</SelectItem>
                <SelectItem value="id_copy">ID Copy</SelectItem>
                <SelectItem value="passport_photo">Passport Photo</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Upload File</Label>
            <Input type="file" onChange={(e) => setData({ ...data, file_url: e.target.value })} />
            <p className="text-xs text-muted-foreground mt-1">Max file size: 5MB. Accepted formats: PDF, JPG, PNG</p>
          </div>
          <div>
            <Label>Expiry Date (Optional)</Label>
            <Input type="date" value={data.expiry_date} onChange={(e) => setData({ ...data, expiry_date: e.target.value })} />
          </div>
          <Button onClick={handleUpload} className="w-full">Upload Document</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
