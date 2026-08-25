import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  Database,
  Server,
  HardDrive,
  Zap,
  Archive,
  Activity
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { apiService } from '../services/api';
import { useFinOps } from '../context/FinOpsContext';

const Resources = () => {
  const { selectedAccount, selectedRegion, setSelectedRegion } = useFinOps();
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedService, setSelectedService] = useState('all');
  const [, setError] = useState(null);

  const fetchResources = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getResources({
        accountId: selectedAccount,
        region: selectedRegion
      });
      setResources(response.data.data || []);
    } catch (err) {
      console.error('Error fetching resources:', err);
      setError('Failed to load resources');
      // Set mock data for demo
      setResources(getMockResources());
    } finally {
      setLoading(false);
    }
  }, [selectedAccount, selectedRegion]);

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  const getMockResources = () => [
    {
      resourceId: 'i-1234567890abcdef0',
      resourceType: 'ec2',
      region: 'us-east-1',
      name: 'Web Server 1',
      instanceType: 't3.medium',
      state: 'running',
      currentCost: 45.67,
      utilizationMetrics: { cpu: 15.2, memory: 45.8 },
      optimizationOpportunities: ['rightsizing'],
      riskLevel: 'LOW',
      timestamp: '2024-01-05T10:30:00Z'
    },
    {
      resourceId: 'db-xyz789',
      resourceType: 'rds',
      region: 'us-west-2',
      name: 'Production DB',
      instanceType: 'db.t3.large',
      state: 'available',
      currentCost: 234.56,
      utilizationMetrics: { cpu: 78.5, connections: 45 },
      optimizationOpportunities: ['reserved_instance'],
      riskLevel: 'MEDIUM',
      timestamp: '2024-01-05T10:25:00Z'
    },
    {
      resourceId: 'lambda-abc123',
      resourceType: 'lambda',
      region: 'us-east-1',
      name: 'Data Processor',
      memory: 512,
      state: 'active',
      currentCost: 12.34,
      utilizationMetrics: { invocations: 1250, duration: 2.5 },
      optimizationOpportunities: ['memory_optimization'],
      riskLevel: 'LOW',
      timestamp: '2024-01-05T10:20:00Z'
    },
    {
      resourceId: 'bucket-files2024',
      resourceType: 's3',
      region: 'us-east-1',
      name: 'Application Files',
      storageClass: 'STANDARD',
      state: 'active',
      currentCost: 89.12,
      utilizationMetrics: { size: '2.5TB', requests: 15000 },
      optimizationOpportunities: ['lifecycle_policy', 'storage_class'],
      riskLevel: 'MEDIUM',
      timestamp: '2024-01-05T10:15:00Z'
    },
    {
      resourceId: 'vol-0987654321fedcba',
      resourceType: 'ebs',
      region: 'us-east-1',
      name: 'Data Volume',
      volumeType: 'gp3',
      state: 'available',
      currentCost: 67.89,
      utilizationMetrics: { iops: 3000, throughput: 125 },
      optimizationOpportunities: ['volume_type'],
      riskLevel: 'LOW',
      timestamp: '2024-01-05T10:10:00Z'
    }
  ];

  const getServiceIcon = (type) => {
    switch (type) {
      case 'ec2': return Server;
      case 'rds': return Database;
      case 'lambda': return Zap;
      case 's3': return Archive;
      case 'ebs': return HardDrive;
      default: return Activity;
    }
  };

  const getServiceColor = (type) => {
    switch (type) {
      case 'ec2': return 'text-blue-600';
      case 'rds': return 'text-green-600';
      case 'lambda': return 'text-yellow-600';
      case 's3': return 'text-orange-600';
      case 'ebs': return 'text-purple-600';
      default: return 'text-gray-600';
    }
  };

  const filteredResources = resources.filter(resource => {
    const matchesSearch = resource.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.resourceId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesService = selectedService === 'all' || resource.resourceType === selectedService;
    const matchesRegion = selectedRegion === 'all' || resource.region === selectedRegion;

    return matchesSearch && matchesService && matchesRegion;
  });

  const services = [...new Set(resources.map(r => r.resourceType))];
  const regions = [...new Set(resources.map(r => r.region))];

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
        <h1 className="text-2xl font-bold text-gray-900">Resource Inventory</h1>
        <button
          onClick={fetchResources}
          className="btn-primary flex items-center"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search resources..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Service</label>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">All Services</option>
              {services.map(service => (
                <option key={service} value={service}>{service.toUpperCase()}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Region</label>
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">All Regions</option>
              {regions.map(region => (
                <option key={region} value={region}>{region}</option>
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-900">{filteredResources.length}</div>
          <div className="text-sm text-blue-700">Total Resources</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-900">
            ${filteredResources.reduce((sum, r) => sum + (r.currentCost || 0), 0).toFixed(2)}
          </div>
          <div className="text-sm text-green-700">Monthly Cost</div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-yellow-900">
            {filteredResources.reduce((sum, r) => sum + (r.optimizationOpportunities?.length || 0), 0)}
          </div>
          <div className="text-sm text-yellow-700">Optimization Opportunities</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-red-900">
            {filteredResources.filter(r => r.riskLevel === 'HIGH' || r.riskLevel === 'CRITICAL').length}
          </div>
          <div className="text-sm text-red-700">High Risk Resources</div>
        </div>
      </div>

      {/* Resources Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Region
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Utilization
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Opportunities
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredResources.map((resource) => {
                const ServiceIcon = getServiceIcon(resource.resourceType);
                return (
                  <tr key={resource.resourceId} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <ServiceIcon className={`h-5 w-5 mr-3 ${getServiceColor(resource.resourceType)}`} />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {resource.name || resource.resourceId}
                          </div>
                          <div className="text-sm text-gray-500">{resource.resourceId}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">{resource.resourceType.toUpperCase()}</span>
                      {resource.instanceType && (
                        <div className="text-xs text-gray-500">{resource.instanceType}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {resource.region}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${resource.currentCost?.toFixed(2) || '0.00'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {resource.utilizationMetrics?.cpu && (
                        <div>CPU: {resource.utilizationMetrics.cpu}%</div>
                      )}
                      {resource.utilizationMetrics?.memory && (
                        <div>Memory: {resource.utilizationMetrics.memory}%</div>
                      )}
                      {resource.utilizationMetrics?.invocations && (
                        <div>Invocations: {resource.utilizationMetrics.invocations}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={resource.riskLevel} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-wrap gap-1">
                        {(() => {
                          const opps = resource.optimizationOpportunities;
                          if (!opps) return null;
                          const oppsArray = Array.isArray(opps) ? opps : [opps];
                          return oppsArray.map((opp, index) => {
                            let displayText = '';
                            if (opp && typeof opp === 'object') {
                              displayText = opp.type || opp.title || opp.name || JSON.stringify(opp);
                            } else {
                              displayText = String(opp || '');
                            }
                            return (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                              >
                                {displayText.replace(/_/g, ' ')}
                              </span>
                            );
                          });
                        })()}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filteredResources.length === 0 && (
          <div className="text-center py-12">
            <Database className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No resources found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search criteria or refresh the data.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Resources;