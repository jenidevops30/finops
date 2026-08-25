import React, { useState, useEffect, useCallback } from 'react';
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Plus,
  RefreshCw,
  Calendar
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
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

const Budgets = () => {
  const { selectedAccount, selectedRegion } = useFinOps();
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBudget, setSelectedBudget] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [, setError] = useState(null);

  const fetchBudgets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getBudgets({
        accountId: selectedAccount,
        region: selectedRegion
      });
      setBudgets(response.data.data.budgets || []);
    } catch (err) {
      console.error('Error fetching budgets:', err);
      setError('Failed to load budgets');
      // Set mock data for demo
      setBudgets(getMockBudgets());
    } finally {
      setLoading(false);
    }
  }, [selectedAccount, selectedRegion]);

  useEffect(() => {
    fetchBudgets();
  }, [fetchBudgets]);

  const getMockBudgets = () => [
    {
      forecastId: 'budget-001',
      budgetCategory: 'organization',
      budgetName: 'Total AWS Spend',
      currentSpend: 45678.90,
      forecastedSpend: 52000.00,
      budgetLimit: 50000.00,
      utilizationPercentage: 91.4,
      status: 'warning',
      confidenceInterval: { lower: 48000, upper: 56000 },
      projectionPeriod: 'monthly',
      lastUpdated: '2024-01-05T10:30:00Z',
      trend: [
        { date: '2024-01-01', actual: 42000, forecast: 45000, budget: 50000 },
        { date: '2024-01-02', actual: 43200, forecast: 46500, budget: 50000 },
        { date: '2024-01-03', actual: 44100, forecast: 48000, budget: 50000 },
        { date: '2024-01-04', actual: 45600, forecast: 50500, budget: 50000 },
        { date: '2024-01-05', actual: 45678, forecast: 52000, budget: 50000 }
      ]
    },
    {
      forecastId: 'budget-002',
      budgetCategory: 'team',
      budgetName: 'Engineering Team',
      currentSpend: 18500.00,
      forecastedSpend: 21000.00,
      budgetLimit: 25000.00,
      utilizationPercentage: 74.0,
      status: 'healthy',
      confidenceInterval: { lower: 19500, upper: 22500 },
      projectionPeriod: 'monthly',
      lastUpdated: '2024-01-05T10:25:00Z',
      trend: [
        { date: '2024-01-01', actual: 16000, forecast: 18000, budget: 25000 },
        { date: '2024-01-02', actual: 16800, forecast: 19000, budget: 25000 },
        { date: '2024-01-03', actual: 17500, forecast: 20000, budget: 25000 },
        { date: '2024-01-04', actual: 18200, forecast: 20500, budget: 25000 },
        { date: '2024-01-05', actual: 18500, forecast: 21000, budget: 25000 }
      ]
    },
    {
      forecastId: 'budget-003',
      budgetCategory: 'project',
      budgetName: 'ML Training Pipeline',
      currentSpend: 8900.00,
      forecastedSpend: 12500.00,
      budgetLimit: 10000.00,
      utilizationPercentage: 89.0,
      status: 'critical',
      confidenceInterval: { lower: 11000, upper: 14000 },
      projectionPeriod: 'monthly',
      lastUpdated: '2024-01-05T10:20:00Z',
      trend: [
        { date: '2024-01-01', actual: 7000, forecast: 8000, budget: 10000 },
        { date: '2024-01-02', actual: 7500, forecast: 9000, budget: 10000 },
        { date: '2024-01-03', actual: 8200, forecast: 10500, budget: 10000 },
        { date: '2024-01-04', actual: 8700, forecast: 11800, budget: 10000 },
        { date: '2024-01-05', actual: 8900, forecast: 12500, budget: 10000 }
      ]
    }
  ];

  const getBudgetStatus = (budget) => {
    const utilization = (budget.currentSpend / budget.budgetLimit) * 100;
    if (utilization >= 90) return 'critical';
    if (utilization >= 75) return 'warning';
    return 'healthy';
  };

  const getBudgetStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const totalBudget = budgets.reduce((sum, b) => sum + b.budgetLimit, 0);
  const totalSpend = budgets.reduce((sum, b) => sum + b.currentSpend, 0);
  const totalForecast = budgets.reduce((sum, b) => sum + b.forecastedSpend, 0);

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
        <h1 className="text-2xl font-bold text-gray-900">Budget Management</h1>
        <div className="flex space-x-3">
          <button
            onClick={fetchBudgets}
            className="btn-secondary flex items-center"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Budget
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-blue-900">${totalBudget.toLocaleString()}</div>
              <div className="text-sm text-blue-700">Total Budget</div>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-green-900">${totalSpend.toLocaleString()}</div>
              <div className="text-sm text-green-700">Current Spend</div>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-yellow-900">${totalForecast.toLocaleString()}</div>
              <div className="text-sm text-yellow-700">Forecasted Spend</div>
            </div>
          </div>
        </div>

        <div className="bg-red-50 p-6 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <div className="text-2xl font-bold text-red-900">
                {budgets.filter(b => getBudgetStatus(b) === 'critical').length}
              </div>
              <div className="text-sm text-red-700">Over Budget</div>
            </div>
          </div>
        </div>
      </div>

      {/* Budget Overview Chart */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Budget Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={budgets[0]?.trend || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
            <Legend />
            <Area
              type="monotone"
              dataKey="budget"
              stackId="1"
              stroke="#94a3b8"
              fill="#f1f5f9"
              name="Budget Limit"
            />
            <Area
              type="monotone"
              dataKey="forecast"
              stackId="2"
              stroke="#f59e0b"
              fill="#fef3c7"
              name="Forecast"
            />
            <Area
              type="monotone"
              dataKey="actual"
              stackId="3"
              stroke="#3b82f6"
              fill="#dbeafe"
              name="Actual Spend"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Budget List */}
      <div className="card">
        <div className="space-y-4">
          {budgets.map((budget) => {
            const status = getBudgetStatus(budget);
            const utilization = (budget.currentSpend / budget.budgetLimit) * 100;

            return (
              <div
                key={budget.forecastId}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedBudget(budget)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">
                        {budget.budgetName}
                      </h3>
                      <StatusBadge status={budget.budgetCategory} />
                      <StatusBadge status={status} />
                    </div>

                    <div className="mt-2">
                      <div className="flex items-center space-x-6 text-sm text-gray-600">
                        <span>Current: ${budget.currentSpend.toLocaleString()}</span>
                        <span>Forecast: ${budget.forecastedSpend.toLocaleString()}</span>
                        <span>Budget: ${budget.budgetLimit.toLocaleString()}</span>
                      </div>

                      {/* Progress Bar */}
                      <div className="mt-3">
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>Budget Utilization</span>
                          <span>{utilization.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${status === 'critical' ? 'bg-red-600' :
                                status === 'warning' ? 'bg-yellow-600' : 'bg-green-600'
                              }`}
                            style={{ width: `${Math.min(utilization, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-right ml-6">
                    <div className={`text-2xl font-bold ${getBudgetStatusColor(status)}`}>
                      ${(budget.forecastedSpend - budget.budgetLimit).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      {budget.forecastedSpend > budget.budgetLimit ? 'Over Budget' : 'Under Budget'}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {budgets.length === 0 && (
          <div className="text-center py-12">
            <DollarSign className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No budgets found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Create your first budget to start tracking costs.
            </p>
          </div>
        )}
      </div>

      {/* Budget Details Modal */}
      {selectedBudget && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedBudget.budgetName} - Budget Details
                </h3>
                <button
                  onClick={() => setSelectedBudget(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Budget Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Category:</span>
                        <StatusBadge status={selectedBudget.budgetCategory} />
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Period:</span>
                        <span>{selectedBudget.projectionPeriod}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Last Updated:</span>
                        <span>{new Date(selectedBudget.lastUpdated).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Financial Summary</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Budget Limit:</span>
                        <span className="font-medium">${selectedBudget.budgetLimit.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Current Spend:</span>
                        <span className="font-medium">${selectedBudget.currentSpend.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Forecasted Spend:</span>
                        <span className="font-medium">${selectedBudget.forecastedSpend.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Variance:</span>
                        <span className={`font-medium ${selectedBudget.forecastedSpend > selectedBudget.budgetLimit
                            ? 'text-red-600' : 'text-green-600'
                          }`}>
                          ${(selectedBudget.forecastedSpend - selectedBudget.budgetLimit).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Confidence Interval</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Lower Bound:</span>
                        <span>${selectedBudget.confidenceInterval.lower.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Upper Bound:</span>
                        <span>${selectedBudget.confidenceInterval.upper.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Spending Trend</h4>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={selectedBudget.trend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="budget"
                        stroke="#94a3b8"
                        strokeDasharray="5 5"
                        name="Budget"
                      />
                      <Line
                        type="monotone"
                        dataKey="forecast"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        name="Forecast"
                      />
                      <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="Actual"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedBudget(null)}
                  className="btn-secondary"
                >
                  Close
                </button>
                <button className="btn-primary">
                  Edit Budget
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Budget Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Create New Budget</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Budget Name</label>
                  <input
                    type="text"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    placeholder="Enter budget name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Category</label>
                  <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    <option value="organization">Organization</option>
                    <option value="team">Team</option>
                    <option value="project">Project</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Budget Amount</label>
                  <input
                    type="number"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Period</label>
                  <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </form>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button className="btn-primary">
                  Create Budget
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Budgets;