import React, { useState, useEffect, useCallback } from 'react';
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  PiggyBank
} from 'lucide-react';
import {
  LineChart,
  Line,
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
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { apiService } from '../services/api';
import { useFinOps } from '../context/FinOpsContext';

const Dashboard = () => {
  const { selectedAccount, selectedRegion } = useFinOps();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        accountId: selectedAccount,
        region: selectedRegion,
        timeRange
      };

      const [dashboardResponse, metricsResponse, chartsResponse] = await Promise.all([
        apiService.getDashboardData(params),
        apiService.getDashboardMetrics(params),
        apiService.getDashboardCharts(params)
      ]);

      setDashboardData({
        ...dashboardResponse.data.data,
        metrics: metricsResponse.data.data,
        charts: chartsResponse.data.data
      });
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
      // Set mock data for demo purposes
      setDashboardData(getMockDashboardData());
    } finally {
      setLoading(false);
    }
  }, [timeRange, selectedAccount, selectedRegion]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const getMockDashboardData = () => ({
    totalCost: 45678.90,
    monthlySavings: 8234.56,
    optimizationOpportunities: 23,
    activeAnomalies: 3,
    resourceCount: 1247,
    budgetUtilization: 78.5,
    metrics: {
      costTrend: '+12.3%',
      savingsRate: '+15.7%',
      efficiencyScore: 87.2
    },
    charts: {
      costTrend: [
        { date: '2024-01-01', cost: 42000, savings: 7500 },
        { date: '2024-01-02', cost: 43200, savings: 7800 },
        { date: '2024-01-03', cost: 44100, savings: 8100 },
        { date: '2024-01-04', cost: 45600, savings: 8200 },
        { date: '2024-01-05', cost: 45678, savings: 8234 }
      ],
      serviceBreakdown: [
        { name: 'EC2', value: 18500, color: '#3b82f6' },
        { name: 'RDS', value: 12300, color: '#10b981' },
        { name: 'S3', value: 8900, color: '#f59e0b' },
        { name: 'Lambda', value: 3200, color: '#ef4444' },
        { name: 'EBS', value: 2778, color: '#8b5cf6' }
      ],
      regionCosts: [
        { region: 'us-east-1', cost: 18500 },
        { region: 'us-west-2', cost: 15200 },
        { region: 'eu-west-1', cost: 8900 },
        { region: 'ap-southeast-1', cost: 3078 }
      ]
    },
    recentOptimizations: [
      {
        id: 1,
        type: 'Right-sizing',
        resource: 'i-1234567890abcdef0',
        savings: 245.67,
        status: 'executed',
        timestamp: '2024-01-05T10:30:00Z'
      },
      {
        id: 2,
        type: 'Reserved Instance',
        resource: 'Multiple EC2 instances',
        savings: 1200.00,
        status: 'pending',
        timestamp: '2024-01-05T09:15:00Z'
      }
    ],
    activeAnomaliesList: [
      {
        id: 1,
        service: 'EC2',
        severity: 'HIGH',
        description: 'Unusual spike in us-east-1',
        cost: 2500,
        timestamp: '2024-01-05T08:45:00Z'
      },
      {
        id: 2,
        service: 'RDS',
        severity: 'MEDIUM',
        description: 'Increased storage costs',
        cost: 890,
        timestamp: '2024-01-05T07:20:00Z'
      }
    ]
  });

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
        <AlertTriangle className="mx-auto h-12 w-12 text-danger-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading dashboard</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-4 btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Cost Optimization Dashboard</h1>
        <div className="flex space-x-2">
          {['24h', '7d', '30d', '90d'].map((range) => (
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
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Monthly Cost"
          value={`$${dashboardData.totalCost?.toLocaleString() || '0'}`}
          change={dashboardData.metrics?.costTrend}
          changeType="negative"
          icon={DollarSign}
        />
        <MetricCard
          title="Monthly Savings"
          value={`$${dashboardData.monthlySavings?.toLocaleString() || '0'}`}
          change={dashboardData.metrics?.savingsRate}
          changeType="positive"
          icon={PiggyBank}
        />
        <MetricCard
          title="Optimization Opportunities"
          value={dashboardData.optimizationOpportunities || 0}
          icon={TrendingUp}
        />
        <MetricCard
          title="Active Anomalies"
          value={dashboardData.activeAnomalies || 0}
          icon={AlertTriangle}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Trend Chart */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Cost Trend & Savings</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dashboardData.charts?.costTrend || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
              <Legend />
              <Line
                type="monotone"
                dataKey="cost"
                stroke="#ef4444"
                strokeWidth={2}
                name="Cost"
              />
              <Line
                type="monotone"
                dataKey="savings"
                stroke="#10b981"
                strokeWidth={2}
                name="Savings"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Service Breakdown */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Cost by Service</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={dashboardData.charts?.serviceBreakdown || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {(dashboardData.charts?.serviceBreakdown || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Cost']} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Regional Costs */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Cost by Region</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dashboardData.charts?.regionCosts || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="region" />
            <YAxis />
            <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Cost']} />
            <Bar dataKey="cost" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Optimizations */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Optimizations</h3>
          <div className="space-y-3">
            {(dashboardData.recentOptimizations || []).map((opt) => (
              <div key={opt.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{opt.type}</p>
                  <p className="text-xs text-gray-500">{opt.resource}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-success-600">
                    ${opt.savings.toLocaleString()}
                  </p>
                  <StatusBadge status={opt.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Active Anomalies */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Active Anomalies</h3>
          <div className="space-y-3">
            {(dashboardData.activeAnomaliesList || []).map((anomaly) => (
              <div key={anomaly.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{anomaly.service}</p>
                  <p className="text-xs text-gray-500">{anomaly.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-danger-600">
                    +${anomaly.cost.toLocaleString()}
                  </p>
                  <StatusBadge status={anomaly.severity} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;