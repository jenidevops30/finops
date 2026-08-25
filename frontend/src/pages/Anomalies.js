import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  RefreshCw,
  Filter,
  Search
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { apiService } from '../services/api';
import { useFinOps } from '../context/FinOpsContext';

const Anomalies = () => {
  const { selectedAccount, selectedRegion } = useFinOps();
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedService, setSelectedService] = useState('all');
  const [, setError] = useState(null);

  const fetchAnomalies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getAnomalies({
        accountId: selectedAccount,
        region: selectedRegion
      });
      setAnomalies(response.data.data || []);
    } catch (err) {
      console.error('Error fetching anomalies:', err);
      setError('Failed to load anomalies');
      // Set mock data for demo
      setAnomalies(getMockAnomalies());
    } finally {
      setLoading(false);
    }
  }, [selectedAccount, selectedRegion]);

  useEffect(() => {
    fetchAnomalies();
  }, [fetchAnomalies]);

  const getMockAnomalies = () => [
    {
      anomalyId: 'anom-001',
      detectedAt: '2024-01-05T08:45:00Z',
      serviceType: 'EC2',
      region: 'us-east-1',
      anomalyType: 'spike',
      severity: 'HIGH',
      baselineCost: 1200.00,
      actualCost: 2500.00,
      deviationPercentage: 108.3,
      rootCause: 'Unusual instance scaling in Auto Scaling Group',
      affectedResources: ['i-1234567890abcdef0', 'i-0987654321fedcba0'],
      resolved: false,
      description: 'Significant cost spike detected in EC2 instances',
      timeline: [
        { time: '08:00', baseline: 1200, actual: 1180 },
        { time: '08:15', baseline: 1200, actual: 1350 },
        { time: '08:30', baseline: 1200, actual: 1890 },
        { time: '08:45', baseline: 1200, actual: 2500 },
        { time: '09:00', baseline: 1200, actual: 2450 }
      ]
    },
    {
      anomalyId: 'anom-002',
      detectedAt: '2024-01-05T07:20:00Z',
      serviceType: 'RDS',
      region: 'us-west-2',
      anomalyType: 'trend',
      severity: 'MEDIUM',
      baselineCost: 450.00,
      actualCost: 890.00,
      deviationPercentage: 97.8,
      rootCause: 'Increased storage usage and backup frequency',
      affectedResources: ['db-prod-mysql-001'],
      resolved: false,
      description: 'Gradual cost increase in RDS storage',
      timeline: [
        { time: '06:00', baseline: 450, actual: 445 },
        { time: '06:30', baseline: 450, actual: 520 },
        { time: '07:00', baseline: 450, actual: 680 },
        { time: '07:20', baseline: 450, actual: 890 },
        { time: '07:40', baseline: 450, actual: 920 }
      ]
    },
    {
      anomalyId: 'anom-003',
      detectedAt: '2024-01-04T15:30:00Z',
      serviceType: 'Lambda',
      region: 'us-east-1',
      anomalyType: 'pattern',
      severity: 'LOW',
      baselineCost: 25.00,
      actualCost: 67.00,
      deviationPercentage: 168.0,
      rootCause: 'Increased function invocations during data processing',
      affectedResources: ['lambda-data-processor', 'lambda-image-resize'],
      resolved: true,
      description: 'Unusual invocation pattern detected',
      timeline: [
        { time: '15:00', baseline: 25, actual: 23 },
        { time: '15:15', baseline: 25, actual: 45 },
        { time: '15:30', baseline: 25, actual: 67 },
        { time: '15:45', baseline: 25, actual: 52 },
        { time: '16:00', baseline: 25, actual: 28 }
      ]
    },
    {
      anomalyId: 'anom-004',
      detectedAt: '2024-01-04T12:15:00Z',
      serviceType: 'S3',
      region: 'eu-west-1',
      anomalyType: 'spike',
      severity: 'CRITICAL',
      baselineCost: 180.00,
      actualCost: 1250.00,
      deviationPercentage: 594.4,
      rootCause: 'Large data transfer and increased request volume',
      affectedResources: ['bucket-data-lake', 'bucket-backups'],
      resolved: true,
      description: 'Critical cost spike in S3 data transfer',
      timeline: [
        { time: '12:00', baseline: 180, actual: 175 },
        { time: '12:05', baseline: 180, actual: 890 },
        { time: '12:10', baseline: 180, actual: 1150 },
        { time: '12:15', baseline: 180, actual: 1250 },
        { time: '12:20', baseline: 180, actual: 980 }
      ]
    }
  ];

  const handleAcknowledge = async (anomalyId) => {
    try {
      await apiService.acknowledgeAnomaly(anomalyId);
      setAnomalies(prev =>
        prev.map(anomaly =>
          anomaly.anomalyId === anomalyId
            ? { ...anomaly, resolved: true }
            : anomaly
        )
      );
    } catch (err) {
      console.error('Error acknowledging anomaly:', err);
      alert('Failed to acknowledge anomaly');
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'CRITICAL': return AlertTriangle;
      case 'HIGH': return AlertTriangle;
      case 'MEDIUM': return Clock;
      case 'LOW': return TrendingUp;
      default: return AlertTriangle;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-600';
      case 'HIGH': return 'text-orange-600';
      case 'MEDIUM': return 'text-yellow-600';
      case 'LOW': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const filteredAnomalies = anomalies.filter(anomaly => {
    const matchesSearch = anomaly.serviceType.toLowerCase().includes(searchTerm.toLowerCase()) ||
      anomaly.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      anomaly.rootCause.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = selectedSeverity === 'all' || anomaly.severity === selectedSeverity;
    const matchesService = selectedService === 'all' || anomaly.serviceType === selectedService;

    return matchesSearch && matchesSeverity && matchesService;
  });

  const severities = [...new Set(anomalies.map(a => a.severity))];
  const services = [...new Set(anomalies.map(a => a.serviceType))];
  const activeAnomalies = anomalies.filter(a => !a.resolved);
  const resolvedAnomalies = anomalies.filter(a => a.resolved);
  const totalImpact = anomalies.reduce((sum, a) => sum + (a.actualCost - a.baselineCost), 0);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Cost Anomalies</h1>
        <button
          onClick={fetchAnomalies}
          className="btn-primary flex items-center"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-red-50 p-6 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-red-900">{activeAnomalies.length}</div>
              <div className="text-sm text-red-700">Active Anomalies</div>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-green-900">{resolvedAnomalies.length}</div>
              <div className="text-sm text-green-700">Resolved</div>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-yellow-900">${totalImpact.toFixed(2)}</div>
              <div className="text-sm text-yellow-700">Total Impact</div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-blue-900">
                {anomalies.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH').length}
              </div>
              <div className="text-sm text-blue-700">High Priority</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search anomalies..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">All Severities</option>
              {severities.map(severity => (
                <option key={severity} value={severity}>{severity}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service</label>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">All Services</option>
              {services.map(service => (
                <option key={service} value={service}>{service}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button className="btn-secondary w-full flex items-center justify-center">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </button>
          </div>
        </div>
      </div>

      {/* Anomalies List */}
      <div className="card">
        <div className="space-y-4">
          {filteredAnomalies.map((anomaly) => {
            const SeverityIcon = getSeverityIcon(anomaly.severity);
            const impact = anomaly.actualCost - anomaly.baselineCost;

            return (
              <div
                key={anomaly.anomalyId}
                className={`border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer ${anomaly.resolved ? 'border-gray-200 bg-gray-50' : 'border-red-200 bg-red-50'
                  }`}
                onClick={() => setSelectedAnomaly(anomaly)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <SeverityIcon className={`h-8 w-8 ${getSeverityColor(anomaly.severity)}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium text-gray-900">
                          {anomaly.serviceType} Anomaly
                        </h3>
                        <StatusBadge status={anomaly.severity} />
                        <StatusBadge status={anomaly.anomalyType} />
                        {anomaly.resolved && <StatusBadge status="resolved" />}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {anomaly.description}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <span>Region: {anomaly.region}</span>
                        <span>Detected: {new Date(anomaly.detectedAt).toLocaleString()}</span>
                        <span>Deviation: +{anomaly.deviationPercentage.toFixed(1)}%</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        <strong>Root Cause:</strong> {anomaly.rootCause}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-lg font-semibold text-red-600">
                        +${impact.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-500">cost impact</div>
                      <div className="text-xs text-gray-400">
                        ${anomaly.baselineCost} → ${anomaly.actualCost}
                      </div>
                    </div>

                    {!anomaly.resolved && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAcknowledge(anomaly.anomalyId);
                        }}
                        className="btn-success flex items-center"
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Acknowledge
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {filteredAnomalies.length === 0 && (
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No anomalies found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No cost anomalies match your current filters.
            </p>
          </div>
        )}
      </div>

      {/* Anomaly Details Modal */}
      {selectedAnomaly && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Anomaly Details - {selectedAnomaly.serviceType}
                </h3>
                <button
                  onClick={() => setSelectedAnomaly(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Anomaly Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Service:</span>
                        <span>{selectedAnomaly.serviceType}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Region:</span>
                        <span>{selectedAnomaly.region}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Type:</span>
                        <StatusBadge status={selectedAnomaly.anomalyType} />
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Severity:</span>
                        <StatusBadge status={selectedAnomaly.severity} />
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Status:</span>
                        <StatusBadge status={selectedAnomaly.resolved ? 'resolved' : 'active'} />
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Detected:</span>
                        <span>{new Date(selectedAnomaly.detectedAt).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Cost Impact</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Baseline Cost:</span>
                        <span>${selectedAnomaly.baselineCost.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Actual Cost:</span>
                        <span>${selectedAnomaly.actualCost.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Impact:</span>
                        <span className="text-red-600 font-medium">
                          +${(selectedAnomaly.actualCost - selectedAnomaly.baselineCost).toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Deviation:</span>
                        <span className="text-red-600 font-medium">
                          +{selectedAnomaly.deviationPercentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Root Cause Analysis</h4>
                    <p className="text-sm text-gray-700">{selectedAnomaly.rootCause}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Affected Resources</h4>
                    <div className="space-y-1">
                      {selectedAnomaly.affectedResources.map((resource, index) => (
                        <div key={index} className="text-sm text-gray-600 font-mono">
                          {resource}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Cost Timeline</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={selectedAnomaly.timeline}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$${value}`, '']} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="baseline"
                        stroke="#94a3b8"
                        strokeDasharray="5 5"
                        name="Baseline"
                      />
                      <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="#ef4444"
                        strokeWidth={2}
                        name="Actual Cost"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedAnomaly(null)}
                  className="btn-secondary"
                >
                  Close
                </button>
                {!selectedAnomaly.resolved && (
                  <button
                    onClick={() => {
                      handleAcknowledge(selectedAnomaly.anomalyId);
                      setSelectedAnomaly(null);
                    }}
                    className="btn-success"
                  >
                    Acknowledge Anomaly
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Anomalies;