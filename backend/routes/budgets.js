/**
 * Budget Routes
 * 
 * API endpoints for managing hierarchical budgets, forecasts, and alerts.
 * Handles budget data from the Python budget manager engine.
 * 
 * Requirements: 5.1, 5.2, 5.3, 6.1, 6.3, 9.1
 */

const express = require('express');
const router = express.Router();
const BudgetForecast = require('../models/BudgetForecast');

// In-memory storage (will be replaced with database in production)
let budgets = [];
let forecasts = [];
let alerts = [];
let approvalWorkflows = [];

/**
 * GET /api/budgets
 * Retrieve all budgets with optional filtering
 */
router.get('/', (req, res) => {
  try {
    const { 
      budgetType, 
      status, 
      parentBudgetId,
      limit = 100, 
      offset = 0,
      accountId
    } = req.query;
    
    let filteredBudgets = [...budgets];
    
    // Apply filters
    if (budgetType) {
      filteredBudgets = filteredBudgets.filter(b => b.budgetType === budgetType);
    }
    
    if (status) {
      filteredBudgets = filteredBudgets.filter(b => b.status === status);
    }
    
    if (parentBudgetId) {
      filteredBudgets = filteredBudgets.filter(b => b.parentBudgetId === parentBudgetId);
    }
    
    if (accountId && accountId !== 'all') {
      filteredBudgets = filteredBudgets.filter(b => b.accountId === accountId || b.budgetId.includes(accountId));
    }
    
    // Apply pagination
    const startIndex = parseInt(offset);
    const endIndex = startIndex + parseInt(limit);
    const paginatedBudgets = filteredBudgets.slice(startIndex, endIndex);
    
    res.json({
      success: true,
      data: {
        budgets: paginatedBudgets,
        total: filteredBudgets.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: endIndex < filteredBudgets.length
      },
      message: `Retrieved ${paginatedBudgets.length} budgets`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving budgets:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve budgets',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/budgets/:budgetId
 * Get specific budget by ID
 */
router.get('/:budgetId', (req, res) => {
  try {
    const { budgetId } = req.params;
    const budget = budgets.find(b => b.budgetId === budgetId);
    
    if (!budget) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Budget ${budgetId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    res.json({
      success: true,
      data: budget,
      message: `Retrieved budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving budget:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve budget',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/budgets
 * Create new budget
 */
router.post('/', (req, res) => {
  try {
    const budgetData = req.body;
    
    // Validate required fields
    const requiredFields = ['budgetId', 'budgetType', 'budgetAmount'];
    const missingFields = requiredFields.filter(field => !budgetData[field]);
    
    if (missingFields.length > 0) {
      return res.status(400).json({
        success: false,
        data: null,
        message: `Missing required fields: ${missingFields.join(', ')}`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Check if budget already exists
    const existingBudget = budgets.find(b => b.budgetId === budgetData.budgetId);
    if (existingBudget) {
      return res.status(409).json({
        success: false,
        data: null,
        message: `Budget ${budgetData.budgetId} already exists`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Create budget with defaults
    const newBudget = {
      budgetId: budgetData.budgetId,
      budgetType: budgetData.budgetType,
      parentBudgetId: budgetData.parentBudgetId || null,
      budgetAmount: parseFloat(budgetData.budgetAmount),
      monthlyAmount: parseFloat(budgetData.budgetAmount) / (budgetData.periodMonths || 12),
      periodMonths: budgetData.periodMonths || 12,
      currency: budgetData.currency || 'USD',
      tags: budgetData.tags || {},
      allocationRules: budgetData.allocationRules || {},
      createdAt: new Date().toISOString(),
      status: 'healthy',
      currentSpend: 0.0,
      forecastedSpend: 0.0,
      variance: 0.0,
      alertThresholds: {
        warning50: budgetData.budgetAmount * 0.5,
        warning75: budgetData.budgetAmount * 0.75,
        critical90: budgetData.budgetAmount * 0.9,
        exceeded100: budgetData.budgetAmount * 1.0
      },
      childBudgets: [],
      approvalWorkflows: []
    };
    
    budgets.push(newBudget);
    
    res.status(201).json({
      success: true,
      data: newBudget,
      message: `Budget ${budgetData.budgetId} created successfully`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error creating budget:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create budget',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * PUT /api/budgets/:budgetId
 * Update existing budget
 */
router.put('/:budgetId', (req, res) => {
  try {
    const { budgetId } = req.params;
    const updateData = req.body;
    
    const budgetIndex = budgets.findIndex(b => b.budgetId === budgetId);
    if (budgetIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Budget ${budgetId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Update budget with new data
    budgets[budgetIndex] = {
      ...budgets[budgetIndex],
      ...updateData,
      lastUpdated: new Date().toISOString()
    };
    
    res.json({
      success: true,
      data: budgets[budgetIndex],
      message: `Budget ${budgetId} updated successfully`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error updating budget:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to update budget',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/budgets/:budgetId/forecasts
 * Get cost forecasts for a specific budget
 */
router.get('/:budgetId/forecasts', (req, res) => {
  try {
    const { budgetId } = req.params;
    const budgetForecasts = forecasts.filter(f => f.budgetId === budgetId);
    
    res.json({
      success: true,
      data: {
        budgetId: budgetId,
        forecasts: budgetForecasts,
        total: budgetForecasts.length
      },
      message: `Retrieved ${budgetForecasts.length} forecasts for budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving forecasts:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve forecasts',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/budgets/:budgetId/forecasts
 * Create new forecast for a budget
 */
router.post('/:budgetId/forecasts', (req, res) => {
  try {
    const { budgetId } = req.params;
    const forecastData = req.body;
    
    // Validate budget exists
    const budget = budgets.find(b => b.budgetId === budgetId);
    if (!budget) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Budget ${budgetId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    const newForecast = {
      forecastId: `forecast_${budgetId}_${Date.now()}`,
      budgetId: budgetId,
      ...forecastData,
      createdAt: new Date().toISOString()
    };
    
    forecasts.push(newForecast);
    
    res.status(201).json({
      success: true,
      data: newForecast,
      message: `Forecast created for budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error creating forecast:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create forecast',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/budgets/:budgetId/alerts
 * Get alerts for a specific budget
 */
router.get('/:budgetId/alerts', (req, res) => {
  try {
    const { budgetId } = req.params;
    const { acknowledged } = req.query;
    
    let budgetAlerts = alerts.filter(a => a.budgetId === budgetId);
    
    // Filter by acknowledged status if specified
    if (acknowledged !== undefined) {
      const isAcknowledged = acknowledged === 'true';
      budgetAlerts = budgetAlerts.filter(a => a.acknowledged === isAcknowledged);
    }
    
    res.json({
      success: true,
      data: {
        budgetId: budgetId,
        alerts: budgetAlerts,
        total: budgetAlerts.length
      },
      message: `Retrieved ${budgetAlerts.length} alerts for budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving alerts:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve alerts',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/budgets/:budgetId/alerts
 * Create new alert for a budget
 */
router.post('/:budgetId/alerts', (req, res) => {
  try {
    const { budgetId } = req.params;
    const alertData = req.body;
    
    const newAlert = {
      alertId: `alert_${budgetId}_${Date.now()}`,
      budgetId: budgetId,
      ...alertData,
      acknowledged: false,
      createdAt: new Date().toISOString()
    };
    
    alerts.push(newAlert);
    
    res.status(201).json({
      success: true,
      data: newAlert,
      message: `Alert created for budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error creating alert:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create alert',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * PUT /api/budgets/:budgetId/alerts/:alertId/acknowledge
 * Acknowledge a budget alert
 */
router.put('/:budgetId/alerts/:alertId/acknowledge', (req, res) => {
  try {
    const { budgetId, alertId } = req.params;
    
    const alertIndex = alerts.findIndex(a => a.alertId === alertId && a.budgetId === budgetId);
    if (alertIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Alert ${alertId} not found for budget ${budgetId}`,
        timestamp: new Date().toISOString()
      });
    }
    
    alerts[alertIndex].acknowledged = true;
    alerts[alertIndex].acknowledgedAt = new Date().toISOString();
    alerts[alertIndex].acknowledgedBy = req.body.acknowledgedBy || 'system';
    
    res.json({
      success: true,
      data: alerts[alertIndex],
      message: `Alert ${alertId} acknowledged`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error acknowledging alert:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to acknowledge alert',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/budgets/:budgetId/approvals
 * Get approval workflows for a specific budget
 */
router.get('/:budgetId/approvals', (req, res) => {
  try {
    const { budgetId } = req.params;
    const { status } = req.query;
    
    let budgetApprovals = approvalWorkflows.filter(w => w.budgetId === budgetId);
    
    // Filter by status if specified
    if (status) {
      budgetApprovals = budgetApprovals.filter(w => w.status === status);
    }
    
    res.json({
      success: true,
      data: {
        budgetId: budgetId,
        approvals: budgetApprovals,
        total: budgetApprovals.length
      },
      message: `Retrieved ${budgetApprovals.length} approval workflows for budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving approvals:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve approvals',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/budgets/:budgetId/approvals
 * Create new approval workflow for a budget
 */
router.post('/:budgetId/approvals', (req, res) => {
  try {
    const { budgetId } = req.params;
    const approvalData = req.body;
    
    // Validate budget exists
    const budget = budgets.find(b => b.budgetId === budgetId);
    if (!budget) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Budget ${budgetId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    const newApproval = {
      workflowId: `approval_${budgetId}_${Date.now()}`,
      budgetId: budgetId,
      status: 'pending',
      ...approvalData,
      createdAt: new Date().toISOString()
    };
    
    approvalWorkflows.push(newApproval);
    
    res.status(201).json({
      success: true,
      data: newApproval,
      message: `Approval workflow created for budget ${budgetId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error creating approval workflow:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create approval workflow',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * PUT /api/budgets/:budgetId/approvals/:workflowId
 * Update approval workflow status
 */
router.put('/:budgetId/approvals/:workflowId', (req, res) => {
  try {
    const { budgetId, workflowId } = req.params;
    const updateData = req.body;
    
    const workflowIndex = approvalWorkflows.findIndex(
      w => w.workflowId === workflowId && w.budgetId === budgetId
    );
    
    if (workflowIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Approval workflow ${workflowId} not found for budget ${budgetId}`,
        timestamp: new Date().toISOString()
      });
    }
    
    approvalWorkflows[workflowIndex] = {
      ...approvalWorkflows[workflowIndex],
      ...updateData,
      lastUpdated: new Date().toISOString()
    };
    
    res.json({
      success: true,
      data: approvalWorkflows[workflowIndex],
      message: `Approval workflow ${workflowId} updated`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error updating approval workflow:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to update approval workflow',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/budgets/stats/summary
 * Get budget statistics summary
 */
router.get('/stats/summary', (req, res) => {
  try {
    const totalBudgets = budgets.length;
    const totalBudgetAmount = budgets.reduce((sum, b) => sum + b.budgetAmount, 0);
    const totalCurrentSpend = budgets.reduce((sum, b) => sum + (b.currentSpend || 0), 0);
    const overallUtilization = totalBudgetAmount > 0 ? (totalCurrentSpend / totalBudgetAmount) * 100 : 0;
    
    // Status distribution
    const statusDistribution = budgets.reduce((acc, budget) => {
      acc[budget.status] = (acc[budget.status] || 0) + 1;
      return acc;
    }, {});
    
    // Type distribution
    const typeDistribution = budgets.reduce((acc, budget) => {
      acc[budget.budgetType] = (acc[budget.budgetType] || 0) + 1;
      return acc;
    }, {});
    
    const activeAlerts = alerts.filter(a => !a.acknowledged).length;
    const pendingApprovals = approvalWorkflows.filter(w => w.status === 'pending').length;
    
    res.json({
      success: true,
      data: {
        totalBudgets,
        totalBudgetAmount,
        totalCurrentSpend,
        overallUtilization,
        statusDistribution,
        typeDistribution,
        activeAlerts,
        pendingApprovals,
        averageBudgetAmount: totalBudgets > 0 ? totalBudgetAmount / totalBudgets : 0,
        budgetsOverThreshold: budgets.filter(b => (b.currentSpend || 0) / b.budgetAmount > 0.8).length
      },
      message: 'Budget statistics retrieved successfully',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving budget statistics:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve budget statistics',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

router.budgets = budgets;
module.exports = router;