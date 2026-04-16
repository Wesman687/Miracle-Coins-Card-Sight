import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  CogIcon,
  PlusIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  StopIcon
} from '@heroicons/react/24/outline';

interface AlertRule {
  id: number;
  name: string;
  description?: string;
  alert_type: string;
  conditions: any;
  product_specific: boolean;
  product_id?: number;
  notification_channels: string[];
  notification_frequency: string;
  enabled: boolean;
  last_triggered?: string;
  trigger_count: number;
  created_at: string;
  created_by: string;
  updated_at: string;
}

interface Alert {
  id: number;
  rule_id: number;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  context_data?: any;
  affected_entity_id?: number;
  affected_entity_type?: string;
  status: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_notes?: string;
  triggered_at: string;
  created_at: string;
  updated_at: string;
}

interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  resolved_alerts: number;
  alerts_by_type: Record<string, number>;
  alerts_by_severity: Record<string, number>;
  recent_trends: Array<{ date: string; count: number }>;
}

const AlertManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'rules' | 'alerts' | 'templates'>('dashboard');
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertStats, setAlertStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateRule, setShowCreateRule] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [rulesResponse, alertsResponse, statsResponse] = await Promise.all([
        fetch('/api/v1/alert-rules'),
        fetch('/api/v1/alerts/active'),
        fetch('/api/v1/alerts/statistics')
      ]);

      if (rulesResponse.ok) {
        const rules = await rulesResponse.json();
        setAlertRules(rules);
      }

      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData);
      }

      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setAlertStats(stats);
      }
    } catch (err) {
      setError('Failed to load alert data');
      console.error('Error loading alert data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runAlertChecks = async () => {
    try {
      const response = await fetch('/api/v1/alerts/check', {
        method: 'POST'
      });
      
      if (response.ok) {
        // Reload data after running checks
        await loadData();
      }
    } catch (err) {
      console.error('Error running alert checks:', err);
    }
  };

  const updateAlertStatus = async (alertId: number, status: string, resolutionNotes?: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status,
          resolution_notes: resolutionNotes
        })
      });

      if (response.ok) {
        await loadData();
        setSelectedAlert(null);
      }
    } catch (err) {
      console.error('Error updating alert:', err);
    }
  };

  const toggleRuleStatus = async (ruleId: number, enabled: boolean) => {
    try {
      const response = await fetch(`/api/v1/alert-rules/${ruleId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled })
      });

      if (response.ok) {
        await loadData();
      }
    } catch (err) {
      console.error('Error updating rule:', err);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-red-600 bg-red-100';
      case 'acknowledged': return 'text-yellow-600 bg-yellow-100';
      case 'resolved': return 'text-green-600 bg-green-100';
      case 'dismissed': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Alert Management</h1>
          <p className="text-gray-400 mt-2">Monitor and manage system alerts and notifications</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={runAlertChecks}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <PlayIcon className="h-5 w-5" />
            <span>Run Checks</span>
          </button>
          <button
            onClick={() => setShowCreateRule(true)}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
            <span>New Rule</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: BellIcon },
            { id: 'rules', label: 'Alert Rules', icon: CogIcon },
            { id: 'alerts', label: 'Active Alerts', icon: ExclamationTriangleIcon },
            { id: 'templates', label: 'Templates', icon: PencilIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-yellow-500 text-yellow-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-red-100 rounded-lg">
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Active Alerts</p>
                  <p className="text-2xl font-bold text-white">{alertStats?.active_alerts || 0}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Resolved</p>
                  <p className="text-2xl font-bold text-white">{alertStats?.resolved_alerts || 0}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BellIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Total Alerts</p>
                  <p className="text-2xl font-bold text-white">{alertStats?.total_alerts || 0}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <CogIcon className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Alert Rules</p>
                  <p className="text-2xl font-bold text-white">{alertRules.length}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Alerts</h3>
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                      {alert.severity}
                    </span>
                    <div>
                      <p className="text-white font-medium">{alert.title}</p>
                      <p className="text-gray-400 text-sm">{alert.message}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400 text-sm">{formatDate(alert.triggered_at)}</span>
                    <button
                      onClick={() => setSelectedAlert(alert)}
                      className="text-blue-400 hover:text-blue-300"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Alert Rules Tab */}
      {activeTab === 'rules' && (
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Alert Rules</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Triggers</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Last Triggered</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {alertRules.map((rule) => (
                  <tr key={rule.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">{rule.name}</div>
                        {rule.description && (
                          <div className="text-sm text-gray-400">{rule.description}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {rule.alert_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        rule.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {rule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {rule.trigger_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {rule.last_triggered ? formatDate(rule.last_triggered) : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => toggleRuleStatus(rule.id, !rule.enabled)}
                          className={`${
                            rule.enabled 
                              ? 'text-red-400 hover:text-red-300' 
                              : 'text-green-400 hover:text-green-300'
                          }`}
                        >
                          {rule.enabled ? <StopIcon className="h-5 w-5" /> : <PlayIcon className="h-5 w-5" />}
                        </button>
                        <button className="text-blue-400 hover:text-blue-300">
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        <button className="text-red-400 hover:text-red-300">
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Active Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Active Alerts</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Alert</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Severity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Triggered</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">{alert.title}</div>
                        <div className="text-sm text-gray-400">{alert.message}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatDate(alert.triggered_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedAlert(alert)}
                          className="text-blue-400 hover:text-blue-300"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        {alert.status === 'active' && (
                          <>
                            <button
                              onClick={() => updateAlertStatus(alert.id, 'acknowledged')}
                              className="text-yellow-400 hover:text-yellow-300"
                            >
                              <CheckCircleIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => updateAlertStatus(alert.id, 'resolved')}
                              className="text-green-400 hover:text-green-300"
                            >
                              <XCircleIcon className="h-5 w-5" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Alert Details</h3>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-gray-400 hover:text-gray-300"
              >
                <XCircleIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300">Title</label>
                <p className="text-white">{selectedAlert.title}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300">Message</label>
                <p className="text-white">{selectedAlert.message}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300">Severity</label>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(selectedAlert.severity)}`}>
                    {selectedAlert.severity}
                  </span>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300">Status</label>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedAlert.status)}`}>
                    {selectedAlert.status}
                  </span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300">Triggered At</label>
                <p className="text-white">{formatDate(selectedAlert.triggered_at)}</p>
              </div>
              
              {selectedAlert.context_data && (
                <div>
                  <label className="block text-sm font-medium text-gray-300">Context Data</label>
                  <pre className="bg-gray-700 p-3 rounded text-sm text-white overflow-auto">
                    {JSON.stringify(selectedAlert.context_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              {selectedAlert.status === 'active' && (
                <>
                  <button
                    onClick={() => updateAlertStatus(selectedAlert.id, 'acknowledged')}
                    className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg transition-colors"
                  >
                    Acknowledge
                  </button>
                  <button
                    onClick={() => updateAlertStatus(selectedAlert.id, 'resolved')}
                    className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Resolve
                  </button>
                </>
              )}
              <button
                onClick={() => setSelectedAlert(null)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );
};

export default AlertManager;


