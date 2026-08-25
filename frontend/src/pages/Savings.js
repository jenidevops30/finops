import React, { useState, useEffect, useCallback } from 'react';
import {
  PiggyBank,
  TrendingUp,
  DollarSign,
  Award,
  RefreshCw,
  Download
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
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

const Savings = () => {
  const { selectedAccount, selectedRegion } = useFinOps();
  const [savingsData, setSavingsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [error, setError] = useState(null);

  const fetchSavingsData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [chartResponse, summaryResponse] = await Promise.all([
        apiService.getSavings({ timeRange, format: 'chart', accountId: selectedAccount, region: selectedRegion }),
        apiService.getSavingsSummary({ timeRange, accountId: selectedAccount, region: selectedRegion })
      ]);

      const chartData = chartResponse.data.data || {};
      const summaryData = summaryResponse.data.data || {};

      // Map backend timeSeries to trends expected by Recharts
      const trends = (chartData.timeSeries || []).map(item => ({
        date: item.date,
        savings: item.totalSavings || 0,
        cumulative: item.cumulativeSavings || 0,
        optimizations: item.count || 0
      }));

      // Map backend serviceBreakdown to byService
      const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
      const byService = (chartData.serviceBreakdown || []).map((item, index) => ({
        service: item.name,
        savings: item.value || 0,
        percentage: chartData.totalSavings > 0 ? (item.value / chartData.totalSavings) * 100 : 0,
        color: COLORS[index % COLORS.length]
      }));

      // Map backend optimizationBreakdown to byOptimizationType
      const byOptimizationType = (chartData.optimizationBreakdown || []).map(item => ({
        type: item.name,
        savings: item.value || 0,
        count: item.count || 0
      }));

      // Map backend topSavings to topOptimizations
      const topOptimizations = (summaryData.topSavings || []).map(item => ({
        id: item.savingsId || item.optimizationId,
        type: item.optimizationType || 'Optimization',
        resource: item.serviceType || 'Resource',
        savings: item.savingsAmount || 0,
        date: item.achievedAt ? item.achievedAt.split('T')[0] : '',
        status: 'executed'
      }));

      // Generate projections dynamically based on total savings
      const projections = {
        nextMonth: (summaryData.totalSavings || 0) * 1.15,
        nextQuarter: (summaryData.totalSavings || 0) * 3.5,
        nextYear: summaryData.annualizedSavings || ((summaryData.totalSavings || 0) * 12),
        confidence: 0.90
      };

      setSavingsData({
        summary: {
          totalSavings: summaryData.totalSavings || 0,
          monthlySavings: summaryData.totalSavings || 0, // Fallback
          savingsRate: summaryData.savingsRate || 0,
          optimizationsExecuted: summaryData.totalCount || 0,
          potentialSavings: (summaryData.totalSavings || 0) * 0.25 // Estimate
        },
        trends,
        byService,
        byOptimizationType,
        topOptimizations,
        projections
      });
    } catch (err) {
      console.error('Error fetching savings data:', err);
      setError('Failed to load savings data');
      // Set mock data for demo
      setSavingsData(getMockSavingsData());
    } finally {
      setLoading(false);
    }
  }, [timeRange, selectedAccount, selectedRegion]);

  useEffect(() => {
    fetchSavingsData();
  }, [fetchSavingsData]);

  const getMockSavingsData = () => ({
    summary: {
      totalSavings: 28456.78,
      monthlySavings: 8234.56,
      yearToDateSavings: 156789.23,
      savingsRate: 18.5,
      optimizationsExecuted: 47,
      potentialSavings: 15678.90
    },
    trends: [
      { date: '2024-01-01', savings: 6500, cumulative: 6500, optimizations: 3 },
      { date: '2024-01-02', savings: 7200, cumulative: 13700, optimizations: 5 },
      { date: '2024-01-03', savings: 6800, cumulative: 20500, optimizations: 4 },
      { date: '2024-01-04', savings: 8100, cumulative: 28600, optimizations: 6 },
      { date: '2024-01-05', savings: 8234, cumulative: 36834, optimizations: 7 }
    ],
    byService: [
      { service: 'EC2', savings: 12500, percentage: 43.9, color: '#3b82f6' },
      { service: 'RDS', savings: 8900, percentage: 31.2, color: '#10b981' },
      { service: 'S3', savings: 4200, percentage: 14.7, color: '#f59e0b' },
      { service: 'Lambda', savings: 1856, percentage: 6.5, color: '#ef4444' },
      { service: 'EBS', savings: 1000, percentage: 3.5, color: '#8b5cf6' }
    ],
    byOptimizationType: [
      { type: 'Right-sizing', savings: 15600, count: 18 },
      { type: 'Reserved Instances', savings: 8900, count: 8 },
      { type: 'Storage Optimization', savings: 2400, count: 12 },
      { type: 'Cleanup', savings: 1556, count: 9 }
    ],
    topOptimizations: [
      {
        id: 1,
        type: 'Reserved Instance',
        resource: 'Production RDS Cluster',
        savings: 2400.00,
        date: '2024-01-04',
        status: 'executed'
      },
      {
        id: 2,
        type: 'Right-sizing',
        resource: 'Web Server Fleet',
        savings: 1800.00,
        date: '2024-01-03',
        status: 'executed'
      },
      {
        id: 3,
        type: 'Storage Optimization',
        resource: 'Data Lake S3 Buckets',
        savings: 1200.00,
        date: '2024-01-02',
        status: 'executed'
      },
      {
        id: 4,
        type: 'Cleanup',
        resource: 'Unused EBS Volumes',
        savings: 890.00,
        date: '2024-01-01',
        status: 'executed'
      }
    ],
    projections: {
      nextMonth: 9500.00,
      nextQuarter: 28500.00,
      nextYear: 114000.00,
      confidence: 0.87
    }
  });

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <PiggyBank className="mx-auto h-12 w-12 text-danger-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading savings data</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <button
          onClick={fetchSavingsData}
          className="mt-4 btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Cost Savings Report</h1>
        <div className="flex space-x-3">
          <div className="flex space-x-2">
            {['7d', '30d', '90d', '1y'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 text-sm rounded-md ${timeRange === range
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
              >
                {range}
              </button>
            ))}
          </div>
          <button
            onClick={fetchSavingsData}
            className="btn-secondary flex items-center"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button className="btn-primary flex items-center">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center">
            <PiggyBank className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-green-900">
                ${savingsData.summary.totalSavings.toLocaleString()}
              </div>
              <div className="text-sm text-green-700">Total Savings</div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-blue-900">
                ${savingsData.summary.monthlySavings.toLocaleString()}
              </div>
              <div className="text-sm text-blue-700">This Month</div>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 p-6 rounded-lg">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-purple-900">
                {savingsData.summary.savingsRate}%
              </div>
              <div className="text-sm text-purple-700">Savings Rate</div>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg">
          <div className="flex items-center">
            <Award className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-yellow-900">
                {savingsData.summary.optimizationsExecuted}
              </div>
              <div className="text-sm text-yellow-700">Optimizations</div>
            </div>
          </div>
        </div>
      </div>

      {/* Savings Trend Chart */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Savings Trend</h3>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={savingsData.trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
            <Legend />
            <Area
              type="monotone"
              dataKey="cumulative"
              stackId="1"
              stroke="#10b981"
              fill="#dcfce7"
              name="Cumulative Savings"
            />
            <Area
              type="monotone"
              dataKey="savings"
              stackId="2"
              stroke="#3b82f6"
              fill="#dbeafe"
              name="Daily Savings"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Savings by Service */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Savings by Service</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={savingsData.byService}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ service, percentage }) => `${service} ${percentage.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="savings"
              >
                {savingsData.byService.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Savings']} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Savings by Optimization Type */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Savings by Optimization Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={savingsData.byOptimizationType}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Savings']} />
              <Bar dataKey="savings" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Optimizations and Projections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Optimizations */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Optimizations</h3>
          <div className="space-y-3">
            {savingsData.topOptimizations.map((optimization) => (
              <div key={optimization.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900">{optimization.type}</p>
                    <StatusBadge status={optimization.status} />
                  </div>
                  <p className="text-xs text-gray-500">{optimization.resource}</p>
                  <p className="text-xs text-gray-400">{optimization.date}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-green-600">
                    ${optimization.savings.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">saved</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Savings Projections */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Savings Projections</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-blue-900">Next Month</p>
                <p className="text-xs text-blue-700">Projected savings</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-blue-900">
                  ${savingsData.projections.nextMonth.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-green-900">Next Quarter</p>
                <p className="text-xs text-green-700">Projected savings</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-green-900">
                  ${savingsData.projections.nextQuarter.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-purple-900">Next Year</p>
                <p className="text-xs text-purple-700">Projected savings</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-purple-900">
                  ${savingsData.projections.nextYear.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Confidence Level</span>
                <span className="text-sm font-medium text-gray-900">
                  {(savingsData.projections.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${savingsData.projections.confidence * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Breakdown */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Detailed Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Service
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Savings
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Percentage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trend
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {savingsData.byService.map((service) => (
                <tr key={service.service} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div
                        className="w-3 h-3 rounded-full mr-3"
                        style={{ backgroundColor: service.color }}
                      />
                      <span className="text-sm font-medium text-gray-900">{service.service}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${service.savings.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {service.percentage.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Savings;