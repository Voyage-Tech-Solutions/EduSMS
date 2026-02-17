"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart3, TrendingUp, Users, DollarSign, Calendar, Download,
  RefreshCw, FileText, PieChart, ArrowUp, ArrowDown, Minus
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface KPI {
  name: string;
  current: number;
  previous: number;
  target: number;
  unit: string;
  trend: string;
  change_percent: number;
}

interface AnalyticsSummary {
  kpis: KPI[];
  enrollment: any;
  academic: any;
  attendance: any;
  financial: any;
}

export default function AnalyticsDashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [dateRange, setDateRange] = useState("last_30_days");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [reports, setReports] = useState<any[]>([]);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    fetchAnalytics();
    fetchReports();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`/api/v1/analytics/dashboard?range=${dateRange}`);
      const data = await res.json();
      setSummary(data);
    } catch (error) {
      console.error("Failed to fetch analytics", error);
    }
    setLoading(false);
  };

  const fetchReports = async () => {
    try {
      const res = await authFetch(`/api/v1/analytics/reports`);
      const data = await res.json();
      setReports(data.reports || []);
    } catch (error) {
      console.error("Failed to fetch reports", error);
    }
  };

  const generateReport = async (reportType: string) => {
    setGeneratingReport(true);
    try {
      const res = await authFetch(`/api/v1/analytics/reports/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: reportType, format: "pdf" })
      });
      const data = await res.json();
      if (data.id) {
        fetchReports();
      }
    } catch (error) {
      console.error("Failed to generate report", error);
    }
    setGeneratingReport(false);
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up": return <ArrowUp className="w-4 h-4 text-green-500" />;
      case "down": return <ArrowDown className="w-4 h-4 text-red-500" />;
      default: return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string, isPositiveGood: boolean = true) => {
    if (trend === "up") return isPositiveGood ? "text-green-600" : "text-red-600";
    if (trend === "down") return isPositiveGood ? "text-red-600" : "text-green-600";
    return "text-gray-600";
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive insights and performance metrics</p>
        </div>
        <div className="flex gap-2">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="this_week">This Week</SelectItem>
              <SelectItem value="last_30_days">Last 30 Days</SelectItem>
              <SelectItem value="this_term">This Term</SelectItem>
              <SelectItem value="this_year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchAnalytics} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="enrollment">Enrollment</TabsTrigger>
          <TabsTrigger value="academic">Academic</TabsTrigger>
          <TabsTrigger value="attendance">Attendance</TabsTrigger>
          <TabsTrigger value="financial">Financial</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {summary?.kpis?.map((kpi, index) => (
              <Card key={index} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-600">{kpi.name}</p>
                    <p className="text-2xl font-bold">
                      {kpi.current}{kpi.unit === "percent" ? "%" : kpi.unit === "currency" ? "" : ""}
                    </p>
                    <div className={`flex items-center gap-1 text-sm ${getTrendColor(kpi.trend)}`}>
                      {getTrendIcon(kpi.trend)}
                      <span>{Math.abs(kpi.change_percent)}% vs previous</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant={kpi.current >= kpi.target ? "default" : "secondary"}>
                      Target: {kpi.target}{kpi.unit === "percent" ? "%" : ""}
                    </Badge>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Quick Reports */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Generate Reports</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button
                variant="outline"
                className="h-20 flex-col"
                onClick={() => generateReport("enrollment_summary")}
                disabled={generatingReport}
              >
                <Users className="w-6 h-6 mb-2" />
                Enrollment Report
              </Button>
              <Button
                variant="outline"
                className="h-20 flex-col"
                onClick={() => generateReport("academic_performance")}
                disabled={generatingReport}
              >
                <BarChart3 className="w-6 h-6 mb-2" />
                Academic Report
              </Button>
              <Button
                variant="outline"
                className="h-20 flex-col"
                onClick={() => generateReport("attendance_analysis")}
                disabled={generatingReport}
              >
                <Calendar className="w-6 h-6 mb-2" />
                Attendance Report
              </Button>
              <Button
                variant="outline"
                className="h-20 flex-col"
                onClick={() => generateReport("financial_summary")}
                disabled={generatingReport}
              >
                <DollarSign className="w-6 h-6 mb-2" />
                Financial Report
              </Button>
            </div>
          </Card>

          {/* Recent Reports */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Reports</h3>
            <div className="space-y-2">
              {reports.length === 0 ? (
                <p className="text-gray-500">No reports generated yet</p>
              ) : (
                reports.slice(0, 5).map((report) => (
                  <div key={report.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-gray-500" />
                      <div>
                        <p className="font-medium">{report.title}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(report.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={report.status === "completed" ? "default" : "secondary"}>
                        {report.status}
                      </Badge>
                      {report.file_url && (
                        <Button size="sm" variant="outline" asChild>
                          <a href={report.file_url} target="_blank" rel="noopener noreferrer">
                            <Download className="w-4 h-4" />
                          </a>
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Enrollment Tab */}
        <TabsContent value="enrollment" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Total Enrollment</h3>
              <p className="text-4xl font-bold">{summary?.enrollment?.total || 0}</p>
              <p className="text-sm text-gray-500">Current academic year</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">New Admissions</h3>
              <p className="text-4xl font-bold text-green-600">{summary?.enrollment?.new_admissions || 0}</p>
              <p className="text-sm text-gray-500">This term</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Withdrawals</h3>
              <p className="text-4xl font-bold text-red-600">{summary?.enrollment?.withdrawals || 0}</p>
              <p className="text-sm text-gray-500">This term</p>
            </Card>
          </div>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Enrollment by Grade</h3>
            <div className="space-y-3">
              {summary?.enrollment?.by_grade?.map((grade: any) => (
                <div key={grade.grade_id} className="flex items-center gap-4">
                  <span className="w-24 font-medium">{grade.grade_name}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-6">
                    <div
                      className="bg-blue-500 h-6 rounded-full flex items-center justify-end pr-2"
                      style={{ width: `${(grade.count / (summary?.enrollment?.total || 1)) * 100}%` }}
                    >
                      <span className="text-white text-sm font-medium">{grade.count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Academic Tab */}
        <TabsContent value="academic" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Pass Rate</h3>
              <p className="text-4xl font-bold">{summary?.academic?.pass_rate || 0}%</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Average Score</h3>
              <p className="text-4xl font-bold">{summary?.academic?.average_score || 0}%</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Honor Roll</h3>
              <p className="text-4xl font-bold text-green-600">{summary?.academic?.honor_roll || 0}</p>
              <p className="text-sm text-gray-500">students</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Needs Support</h3>
              <p className="text-4xl font-bold text-orange-600">{summary?.academic?.needs_support || 0}</p>
              <p className="text-sm text-gray-500">students</p>
            </Card>
          </div>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Performance by Subject</h3>
            <div className="space-y-3">
              {summary?.academic?.by_subject?.map((subject: any) => (
                <div key={subject.subject_id} className="flex items-center gap-4">
                  <span className="w-32 font-medium">{subject.subject_name}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-6">
                    <div
                      className={`h-6 rounded-full flex items-center justify-end pr-2 ${
                        subject.average >= 70 ? 'bg-green-500' : subject.average >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${subject.average}%` }}
                    >
                      <span className="text-white text-sm font-medium">{subject.average}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Attendance Tab */}
        <TabsContent value="attendance" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Overall Rate</h3>
              <p className="text-4xl font-bold">{summary?.attendance?.overall_rate || 0}%</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Present Today</h3>
              <p className="text-4xl font-bold text-green-600">{summary?.attendance?.present_today || 0}</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Absent Today</h3>
              <p className="text-4xl font-bold text-red-600">{summary?.attendance?.absent_today || 0}</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Chronic Absence</h3>
              <p className="text-4xl font-bold text-orange-600">{summary?.attendance?.chronic_absence || 0}</p>
              <p className="text-sm text-gray-500">students (&gt;10% absent)</p>
            </Card>
          </div>
        </TabsContent>

        {/* Financial Tab */}
        <TabsContent value="financial" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Collection Rate</h3>
              <p className="text-4xl font-bold">{summary?.financial?.collection_rate || 0}%</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Total Collected</h3>
              <p className="text-4xl font-bold text-green-600">
                ${(summary?.financial?.total_collected || 0).toLocaleString()}
              </p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Outstanding</h3>
              <p className="text-4xl font-bold text-orange-600">
                ${(summary?.financial?.outstanding || 0).toLocaleString()}
              </p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Overdue (30+ days)</h3>
              <p className="text-4xl font-bold text-red-600">
                ${(summary?.financial?.overdue_30 || 0).toLocaleString()}
              </p>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
