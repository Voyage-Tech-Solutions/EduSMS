"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Activity, Server, Database, Cpu, HardDrive, Clock,
  AlertTriangle, CheckCircle, XCircle, RefreshCw, Bell
} from "lucide-react";

interface ServiceStatus {
  name: string;
  status: string;
  latency_ms?: number;
  uptime_percent?: number;
  queue_size?: number;
  workers_active?: number;
}

interface SystemAlert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  is_active: boolean;
  acknowledged: boolean;
  created_at: string;
}

export default function SystemHealthPage() {
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [errors, setErrors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    await Promise.all([
      fetchHealth(),
      fetchServices(),
      fetchAlerts(),
      fetchMetrics(),
      fetchErrors()
    ]);
    setLoading(false);
  };

  const fetchHealth = async () => {
    try {
      const res = await authFetch(`/api/v1/system/health/status`);
      const data = await res.json();
      setHealthStatus(data);
    } catch (error) {
      console.error("Failed to fetch health status", error);
    }
  };

  const fetchServices = async () => {
    try {
      const res = await authFetch(`/api/v1/system/health/services`);
      const data = await res.json();
      setServices(data.services || []);
    } catch (error) {
      console.error("Failed to fetch services", error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await authFetch(`/api/v1/system/health/alerts`);
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error("Failed to fetch alerts", error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await authFetch(`/api/v1/system/health/metrics`);
      const data = await res.json();
      setMetrics(data);
    } catch (error) {
      console.error("Failed to fetch metrics", error);
    }
  };

  const fetchErrors = async () => {
    try {
      const res = await authFetch(`/api/v1/system/health/errors?hours=24`);
      const data = await res.json();
      setErrors(data.errors || []);
    } catch (error) {
      console.error("Failed to fetch errors", error);
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await authFetch(`/api/v1/system/health/alerts/${alertId}/acknowledge`, {
        method: "POST"
      });
      fetchAlerts();
    } catch (error) {
      console.error("Failed to acknowledge alert", error);
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      await authFetch(`/api/v1/system/health/alerts/${alertId}/resolve`, {
        method: "POST"
      });
      fetchAlerts();
    } catch (error) {
      console.error("Failed to resolve alert", error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "operational": return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "degraded": return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "down": return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "destructive";
      case "high": return "destructive";
      case "medium": return "default";
      default: return "secondary";
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">System Health</h1>
          <p className="text-gray-600">Monitor system status, services, and performance</p>
        </div>
        <Button variant="outline" onClick={fetchAll} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Status Banner */}
      <Card className={`p-4 ${
        healthStatus?.status === 'operational' ? 'bg-green-50 border-green-200' :
        healthStatus?.status === 'degraded' ? 'bg-yellow-50 border-yellow-200' :
        'bg-red-50 border-red-200'
      }`}>
        <div className="flex items-center gap-3">
          {getStatusIcon(healthStatus?.status)}
          <div>
            <p className="font-semibold capitalize">
              System Status: {healthStatus?.status || 'Unknown'}
            </p>
            <p className="text-sm text-gray-600">
              Last checked: {healthStatus?.timestamp ? new Date(healthStatus.timestamp).toLocaleString() : 'N/A'}
            </p>
          </div>
        </div>
      </Card>

      {/* Active Alerts */}
      {alerts.filter(a => a.is_active).length > 0 && (
        <Card className="p-4 border-orange-200 bg-orange-50">
          <div className="flex items-center gap-2 mb-3">
            <Bell className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold">Active Alerts ({alerts.filter(a => a.is_active).length})</h3>
          </div>
          <div className="space-y-2">
            {alerts.filter(a => a.is_active).map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded">
                <div className="flex items-center gap-3">
                  <Badge variant={getSeverityColor(alert.severity)}>{alert.severity}</Badge>
                  <div>
                    <p className="font-medium">{alert.title}</p>
                    <p className="text-sm text-gray-500">{alert.message}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {!alert.acknowledged && (
                    <Button size="sm" variant="outline" onClick={() => acknowledgeAlert(alert.id)}>
                      Acknowledge
                    </Button>
                  )}
                  <Button size="sm" onClick={() => resolveAlert(alert.id)}>
                    Resolve
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Cpu className="w-8 h-8 text-blue-500" />
                <div>
                  <p className="text-sm text-gray-600">CPU Usage</p>
                  <p className="text-2xl font-bold">{healthStatus?.cpu_percent || 0}%</p>
                </div>
              </div>
              <Progress value={healthStatus?.cpu_percent || 0} className="mt-2" />
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <HardDrive className="w-8 h-8 text-green-500" />
                <div>
                  <p className="text-sm text-gray-600">Memory Usage</p>
                  <p className="text-2xl font-bold">{healthStatus?.memory?.used_percent || 0}%</p>
                </div>
              </div>
              <Progress value={healthStatus?.memory?.used_percent || 0} className="mt-2" />
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Database className="w-8 h-8 text-purple-500" />
                <div>
                  <p className="text-sm text-gray-600">Database</p>
                  <p className="text-2xl font-bold">
                    {healthStatus?.database?.connected ? 'Connected' : 'Disconnected'}
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Clock className="w-8 h-8 text-orange-500" />
                <div>
                  <p className="text-sm text-gray-600">Uptime</p>
                  <p className="text-2xl font-bold">{healthStatus?.uptime || 'N/A'}</p>
                </div>
              </div>
            </Card>
          </div>

          {/* System Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">System Information</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Platform</p>
                <p className="font-medium">{healthStatus?.system?.platform || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Python Version</p>
                <p className="font-medium">{healthStatus?.system?.python_version || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Hostname</p>
                <p className="font-medium">{healthStatus?.system?.hostname || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Memory</p>
                <p className="font-medium">
                  {healthStatus?.memory?.available_gb || 0} GB available / {healthStatus?.memory?.total_gb || 0} GB total
                </p>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* Services Tab */}
        <TabsContent value="services">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Service Status</h3>
            <div className="space-y-3">
              {services.map((service, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(service.status)}
                    <div>
                      <p className="font-medium">{service.name}</p>
                      <p className="text-sm text-gray-500 capitalize">{service.status}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    {service.latency_ms !== undefined && (
                      <p className="text-sm">Latency: {service.latency_ms}ms</p>
                    )}
                    {service.uptime_percent !== undefined && (
                      <p className="text-sm text-gray-500">Uptime: {service.uptime_percent}%</p>
                    )}
                    {service.queue_size !== undefined && (
                      <p className="text-sm text-gray-500">Queue: {service.queue_size}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-4">
              <h4 className="font-semibold mb-2">Requests (24h)</h4>
              <p className="text-3xl font-bold">{metrics?.requests?.total_24h || 0}</p>
              <p className="text-sm text-gray-500">
                Avg response: {metrics?.requests?.avg_response_time_ms || 0}ms
              </p>
              <p className="text-sm text-gray-500">
                Error rate: {metrics?.requests?.error_rate_percent || 0}%
              </p>
            </Card>
            <Card className="p-4">
              <h4 className="font-semibold mb-2">Database</h4>
              <p className="text-3xl font-bold">
                {metrics?.database?.connections_active || 0}/{metrics?.database?.connections_max || 0}
              </p>
              <p className="text-sm text-gray-500">active connections</p>
              <p className="text-sm text-gray-500">
                Avg query: {metrics?.database?.avg_query_time_ms || 0}ms
              </p>
            </Card>
            <Card className="p-4">
              <h4 className="font-semibold mb-2">Errors (24h)</h4>
              <p className="text-3xl font-bold text-red-600">{errors.length}</p>
              <p className="text-sm text-gray-500">total errors logged</p>
            </Card>
          </div>

          {/* Slowest Endpoints */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Slowest Endpoints</h3>
            <div className="space-y-2">
              {metrics?.api_endpoints?.slowest?.map((ep: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <code className="text-sm">{ep.endpoint}</code>
                  <Badge variant="secondary">{ep.avg_ms}ms</Badge>
                </div>
              ))}
            </div>
          </Card>

          {/* Most Used Endpoints */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Most Used Endpoints (24h)</h3>
            <div className="space-y-2">
              {metrics?.api_endpoints?.most_used?.map((ep: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <code className="text-sm">{ep.endpoint}</code>
                  <Badge>{ep.calls_24h.toLocaleString()} calls</Badge>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Errors Tab */}
        <TabsContent value="errors">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Errors (Last 24 Hours)</h3>
            <div className="space-y-3">
              {errors.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No errors in the last 24 hours</p>
              ) : (
                errors.slice(0, 20).map((error: any) => (
                  <div key={error.id} className="p-4 bg-red-50 rounded border border-red-100">
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant="destructive">{error.error_type}</Badge>
                        <p className="font-medium mt-1">{error.message}</p>
                        <p className="text-sm text-gray-500">
                          {error.request_method} {error.request_path}
                        </p>
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(error.created_at).toLocaleString()}
                      </span>
                    </div>
                    {error.stack_trace && (
                      <details className="mt-2">
                        <summary className="text-sm text-gray-500 cursor-pointer">Stack trace</summary>
                        <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                          {error.stack_trace}
                        </pre>
                      </details>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
