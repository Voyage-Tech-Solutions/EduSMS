"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Search, Filter, Download, RefreshCw, Eye, User, Clock,
  FileText, Edit, Trash2, LogIn, LogOut, Plus, Shield
} from "lucide-react";

interface AuditLog {
  id: string;
  user_id: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id: string;
  description: string;
  old_value: any;
  new_value: any;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [resourceFilter, setResourceFilter] = useState("all");
  const [dateRange, setDateRange] = useState("last_7_days");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 50, total: 0 });

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, resourceFilter, dateRange, pagination.page]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        limit: pagination.limit.toString(),
        range: dateRange
      });
      if (actionFilter !== "all") params.append("action", actionFilter);
      if (resourceFilter !== "all") params.append("resource_type", resourceFilter);
      if (searchQuery) params.append("search", searchQuery);

      const res = await authFetch(`/api/v1/system/audit?${params}`);
      const data = await res.json();
      setLogs(data.logs || []);
      setPagination(prev => ({ ...prev, total: data.total || 0 }));
    } catch (error) {
      console.error("Failed to fetch audit logs", error);
    }
    setLoading(false);
  };

  const exportLogs = async () => {
    try {
      const params = new URLSearchParams({ range: dateRange, format: "csv" });
      if (actionFilter !== "all") params.append("action", actionFilter);
      if (resourceFilter !== "all") params.append("resource_type", resourceFilter);

      window.open(`/api/v1/system/audit/export?${params}`, "_blank");
    } catch (error) {
      console.error("Failed to export logs", error);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "create": return <Plus className="w-4 h-4 text-green-500" />;
      case "update": return <Edit className="w-4 h-4 text-blue-500" />;
      case "delete": return <Trash2 className="w-4 h-4 text-red-500" />;
      case "login": return <LogIn className="w-4 h-4 text-purple-500" />;
      case "logout": return <LogOut className="w-4 h-4 text-gray-500" />;
      case "read": return <Eye className="w-4 h-4 text-gray-500" />;
      default: return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case "create": return "bg-green-100 text-green-800";
      case "update": return "bg-blue-100 text-blue-800";
      case "delete": return "bg-red-100 text-red-800";
      case "login": return "bg-purple-100 text-purple-800";
      case "logout": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const filteredLogs = logs.filter(log =>
    log.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.user_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.resource_type?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Audit Logs</h1>
          <p className="text-gray-600">Track all system activities and changes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportLogs}>
            <Download className="w-4 h-4 mr-2" /> Export
          </Button>
          <Button variant="outline" onClick={fetchLogs} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-gray-500" />
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <Select value={actionFilter} onValueChange={setActionFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Action" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Actions</SelectItem>
              <SelectItem value="create">Create</SelectItem>
              <SelectItem value="read">Read</SelectItem>
              <SelectItem value="update">Update</SelectItem>
              <SelectItem value="delete">Delete</SelectItem>
              <SelectItem value="login">Login</SelectItem>
              <SelectItem value="logout">Logout</SelectItem>
            </SelectContent>
          </Select>

          <Select value={resourceFilter} onValueChange={setResourceFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Resource" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Resources</SelectItem>
              <SelectItem value="student">Students</SelectItem>
              <SelectItem value="teacher">Teachers</SelectItem>
              <SelectItem value="user">Users</SelectItem>
              <SelectItem value="grade">Grades</SelectItem>
              <SelectItem value="attendance">Attendance</SelectItem>
              <SelectItem value="payment">Payments</SelectItem>
              <SelectItem value="settings">Settings</SelectItem>
            </SelectContent>
          </Select>

          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Date Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="last_7_days">Last 7 Days</SelectItem>
              <SelectItem value="last_30_days">Last 30 Days</SelectItem>
              <SelectItem value="last_90_days">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Entries</p>
              <p className="text-xl font-bold">{pagination.total.toLocaleString()}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded">
              <Plus className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Creates</p>
              <p className="text-xl font-bold">{logs.filter(l => l.action === 'create').length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded">
              <Edit className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Updates</p>
              <p className="text-xl font-bold">{logs.filter(l => l.action === 'update').length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded">
              <Trash2 className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Deletes</p>
              <p className="text-xl font-bold">{logs.filter(l => l.action === 'delete').length}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Logs Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-3 font-medium">Timestamp</th>
                <th className="text-left p-3 font-medium">User</th>
                <th className="text-left p-3 font-medium">Action</th>
                <th className="text-left p-3 font-medium">Resource</th>
                <th className="text-left p-3 font-medium">Description</th>
                <th className="text-left p-3 font-medium">IP Address</th>
                <th className="text-left p-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-500">Loading...</td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-500">No audit logs found</td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">{log.user_name || 'System'}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getActionColor(log.action)}`}>
                        {getActionIcon(log.action)}
                        {log.action}
                      </span>
                    </td>
                    <td className="p-3">
                      <Badge variant="outline">{log.resource_type}</Badge>
                    </td>
                    <td className="p-3">
                      <span className="text-sm text-gray-600 line-clamp-1">{log.description}</span>
                    </td>
                    <td className="p-3">
                      <span className="text-sm text-gray-500">{log.ip_address}</span>
                    </td>
                    <td className="p-3">
                      <Button variant="ghost" size="sm" onClick={() => setSelectedLog(log)}>
                        <Eye className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <p className="text-sm text-gray-500">
            Showing {((pagination.page - 1) * pagination.limit) + 1} to {Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total} entries
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page === 1}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page * pagination.limit >= pagination.total}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {/* Log Detail Modal */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Audit Log Details</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-500">Timestamp</Label>
                  <p className="font-medium">{new Date(selectedLog.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <Label className="text-gray-500">User</Label>
                  <p className="font-medium">{selectedLog.user_name || 'System'}</p>
                </div>
                <div>
                  <Label className="text-gray-500">Action</Label>
                  <p className="font-medium capitalize">{selectedLog.action}</p>
                </div>
                <div>
                  <Label className="text-gray-500">Resource Type</Label>
                  <p className="font-medium">{selectedLog.resource_type}</p>
                </div>
                <div>
                  <Label className="text-gray-500">Resource ID</Label>
                  <p className="font-medium font-mono text-sm">{selectedLog.resource_id || 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-gray-500">IP Address</Label>
                  <p className="font-medium">{selectedLog.ip_address || 'N/A'}</p>
                </div>
              </div>

              <div>
                <Label className="text-gray-500">Description</Label>
                <p className="mt-1">{selectedLog.description}</p>
              </div>

              <div>
                <Label className="text-gray-500">User Agent</Label>
                <p className="mt-1 text-sm text-gray-600 break-all">{selectedLog.user_agent || 'N/A'}</p>
              </div>

              {selectedLog.old_value && (
                <div>
                  <Label className="text-gray-500">Previous Value</Label>
                  <pre className="mt-1 p-3 bg-gray-100 rounded text-sm overflow-x-auto">
                    {JSON.stringify(selectedLog.old_value, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.new_value && (
                <div>
                  <Label className="text-gray-500">New Value</Label>
                  <pre className="mt-1 p-3 bg-gray-100 rounded text-sm overflow-x-auto">
                    {JSON.stringify(selectedLog.new_value, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
