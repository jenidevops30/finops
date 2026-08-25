import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  CheckCircle,
  Clock,
  AlertCircle,
  DollarSign,
  Zap,
  RefreshCw
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { apiService } from '../services/api';
import { useFinOps } from '../context/FinOpsContext';

const Optimizations = () => {
  const { selectedAccount, selectedRegion } = useFinOps();
  const [optimizations, setOptimizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOptimization, setSelectedOptimization] = useState(null);
  const [approving, setApproving] = useState(null);
  const [, setError] = useState(null);

  const fetchOptimizations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getOptimizations({
        accountId: selectedAccount,
        region: selectedRegion
      });
      setOptimizations(response.data.data || []);
    } catch (err) {
      console.error('Error fetching optimizations:', err);
      setError('Failed to load optimizations');
      // Set mock data for demo
      setOptimizations(getMockOptimizations());
    } finally {
      setLoading(false);
    }
  }, [selectedAccount, selectedRegion]);

  useEffect(() => {
    fetchOptimizations();
  }, [fetchOptimizations]);

  const getMockOptimizations = () => [
    {
      optimizationId: 'opt-001',
      resourceId: 'i-1234567890abcdef0',
      resourceName: 'Web Server 1',
      optimizationType: 'rightsizing',
      currentCost: 145.67,
      projectedCost: 89.45,
      estimatedSavings: 56.22,
      confidenceScore: 0.92,
      riskLevel: 'LOW',
      status: 'pending',
      approvalRequired: false,
      description: 'Right-size from t3.large to t3.medium based on low CPU utilization',
      details: {
        currentConfig: 't3.large (2 vCPU, 8 GB RAM)',
        recommendedConfig: 't3.medium (2 vCPU, 4 GB RAM)',
        utilizationData: { cpu: 15.2, memory: 35.8 },
        implementationTime: '5 minutes',
        rollbackTime: '2 minutes'
      },
      timestamp: '2024-01-05T10:30:00Z'
    },
    {
      optimizationId: 'opt-002',
      resourceId: 'db-xyz789',
      resourceName: 'Production DB',
      optimizationType: 'pricing',
      currentCost: 734.56,
      projectedCost: 489.12,
      estimatedSavings: 245.44,
      confidenceScore: 0.87,
      riskLevel: 'MEDIUM',
      status: 'pending',
      approvalRequired: true,
      description: 'Purchase Reserved Instance for 1-year term',
      details: {
        currentConfig: 'On-Demand db.r5.xlarge',
        recommendedConfig: '1-year Reserved Instance',
        paymentOption: 'Partial Upfront',
        upfrontCost: 1200.00,
        implementationTime: 'Immediate',
        rollbackTime: 'Not applicable'
      },
      timestamp: '2024-01-05T10:25:00Z'
    },
    {
      optimizationId: 'opt-003',
      resourceId: 'lambda-abc123',
      resourceName: 'Data Processor',
      optimizationType: 'rightsizing',
      currentCost: 45.34,
      projectedCost: 32.12,
      estimatedSavings: 13.22,
      confidenceScore: 0.78,
      riskLevel: 'LOW',
      status: 'executed',
      approvalRequired: false,
      description: 'Optimize memory allocation from 1024MB to 768MB',
      details: {
        currentConfig: '1024 MB memory',
        recommendedConfig: '768 MB memory',
        avgDuration: '2.1s',
        maxMemoryUsed: '512 MB',
        implementationTime: 'Immediate',
        rollbackTime: 'Immediate'
      },
      timestamp: '2024-01-05T09:15:00Z'
    },
    {
      optimizationId: 'opt-004',
      resourceId: 'bucket-files2024',
      resourceName: 'Application Files',
      optimizationType: 'cleanup',
      currentCost: 189.12,
      projectedCost: 134.67,
      estimatedSavings: 54.45,
      confidenceScore: 0.95,
      riskLevel: 'HIGH',
      status: 'pending',
      approvalRequired: true,
      description: 'Implement lifecycle policy and transition to IA storage class',
      details: {
        currentConfig: 'Standard storage, no lifecycle',
        recommendedConfig: 'Lifecycle: IA after 30 days, Glacier after 90 days',
        affectedObjects: '~2.5TB',
        accessPattern: 'Infrequent after 30 days',
        implementationTime: '24 hours',
        rollbackTime: '48 hours'
      },
      timestamp: '2024-01-05T08:45:00Z'
    }
  ];

  const handleApprove = async (optimizationId) => {
    try {
      setApproving(optimizationId);
      await apiService.approveOptimization(optimizationId, { approved: true });

      // Update local state
      setOptimizations(prev =>
        prev.map(opt =>
          opt.optimizationId === optimizationId
            ? { ...opt, status: 'approved' }
            : opt
        )
      );
    } catch (err) {
      console.error('Error approving optimization:', err);
      alert('Failed to approve optimization');
    } finally {
      setApproving(null);
    }
  };

  const getOptimizationIcon = (type) => {
    switch (type) {
      case 'rightsizing': return TrendingUp;
      case 'pricing': return DollarSign;
      case 'cleanup': return Zap;
      default: return TrendingUp;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return Clock;
      case 'approved': return CheckCircle;
      case 'executed': return CheckCircle;
      case 'rolled_back': return AlertCircle;
      default: return Clock;
    }
  };

  const totalSavings = optimizations.reduce((sum, opt) => sum + opt.estimatedSavings, 0);
  const pendingOptimizations = optimizations.filter(opt => opt.status === 'pending');
  const executedOptimizations = optimizations.filter(opt => opt.status === 'executed');

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
        <h1 className="text-2xl font-bold text-gray-900">Cost Optimizations</h1>
        <button
          onClick={fetchOptimizations}
          className="btn-primary flex items-center"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-blue-900">{optimizations.length}</div>
              <div className="text-sm text-blue-700">Total Opportunities</div>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-green-900">${totalSavings.toFixed(2)}</div>
              <div className="text-sm text-green-700">Potential Savings</div>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-yellow-900">{pendingOptimizations.length}</div>
              <div className="text-sm text-yellow-700">Pending Approval</div>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 p-6 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-purple-900">{executedOptimizations.length}</div>
              <div className="text-sm text-purple-700">Executed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Optimizations List */}
      <div className="card">
        <div className="space-y-4">
          {optimizations.map((optimization) => {
            const OptIcon = getOptimizationIcon(optimization.optimizationType);
            const StatusIcon = getStatusIcon(optimization.status);

            return (
              <div
                key={optimization.optimizationId}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedOptimization(optimization)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <OptIcon className="h-8 w-8 text-primary-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium text-gray-900">
                          {optimization.resourceName}
                        </h3>
                        <StatusBadge status={optimization.status} />
                        <StatusBadge status={optimization.riskLevel} />
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {optimization.description}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <span>Type: {optimization.optimizationType}</span>
                        <span>Confidence: {(optimization.confidenceScore * 100).toFixed(0)}%</span>
                        <span>Resource: {optimization.resourceId}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-lg font-semibold text-green-600">
                        ${optimization.estimatedSavings.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-500">monthly savings</div>
                    </div>

                    {optimization.status === 'pending' && optimization.approvalRequired && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApprove(optimization.optimizationId);
                        }}
                        disabled={approving === optimization.optimizationId}
                        className="btn-success flex items-center"
                      >
                        {approving === optimization.optimizationId ? (
                          <LoadingSpinner size="sm" className="mr-2" />
                        ) : (
                          <CheckCircle className="h-4 w-4 mr-2" />
                        )}
                        Approve
                      </button>
                    )}

                    {optimization.status === 'pending' && !optimization.approvalRequired && (
                      <div className="flex items-center text-sm text-blue-600">
                        <Zap className="h-4 w-4 mr-1" />
                        Auto-execute
                      </div>
                    )}

                    <StatusIcon className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {optimizations.length === 0 && (
          <div className="text-center py-12">
            <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No optimizations found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Run a scan to discover optimization opportunities.
            </p>
          </div>
        )}
      </div>

      {/* Optimization Details Modal */}
      {selectedOptimization && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Optimization Details
                </h3>
                <button
                  onClick={() => setSelectedOptimization(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">Resource Information</h4>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Resource:</span>
                      <span className="ml-2">{selectedOptimization.resourceName}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">ID:</span>
                      <span className="ml-2">{selectedOptimization.resourceId}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Type:</span>
                      <span className="ml-2">{selectedOptimization.optimizationType}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Risk Level:</span>
                      <span className="ml-2">
                        <StatusBadge status={selectedOptimization.riskLevel} />
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900">Cost Impact</h4>
                  <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Current Cost:</span>
                      <div className="text-lg font-semibold">${selectedOptimization.currentCost.toFixed(2)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Projected Cost:</span>
                      <div className="text-lg font-semibold">${selectedOptimization.projectedCost.toFixed(2)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Monthly Savings:</span>
                      <div className="text-lg font-semibold text-green-600">
                        ${selectedOptimization.estimatedSavings.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900">Configuration Changes</h4>
                  <div className="mt-2 space-y-2 text-sm">
                    <div>
                      <span className="text-gray-500">Current:</span>
                      <span className="ml-2">{selectedOptimization.details.currentConfig}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Recommended:</span>
                      <span className="ml-2">{selectedOptimization.details.recommendedConfig}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900">Implementation</h4>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Implementation Time:</span>
                      <span className="ml-2">{selectedOptimization.details.implementationTime}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Rollback Time:</span>
                      <span className="ml-2">{selectedOptimization.details.rollbackTime}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedOptimization(null)}
                  className="btn-secondary"
                >
                  Close
                </button>
                {selectedOptimization.status === 'pending' && selectedOptimization.approvalRequired && (
                  <button
                    onClick={() => {
                      handleApprove(selectedOptimization.optimizationId);
                      setSelectedOptimization(null);
                    }}
                    className="btn-success"
                  >
                    Approve Optimization
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

export default Optimizations;