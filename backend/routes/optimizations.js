/**
 * Optimization Routes
 * 
 * API endpoints for managing cost optimization recommendations and approval workflows.
 * Handles optimization data from the Python automation engine and approval processes.
 * 
 * Requirements: 8.1, 8.3, 9.1
 */

const express = require('express');
const router = express.Router();
const CostOptimization = require('../models/CostOptimization');

// In-memory storage (will be replaced with database in production)
let optimizations = [];

/**
 * GET /api/optimizations
 * Retrieve optimization recommendations with optional filtering
 */
router.get('/', (req, res) => {
  try {
    const { 
      status, 
      riskLevel, 
      optimizationType,
      resourceId,
      region,
      minSavings,
      maxSavings,
      limit = 100, 
      offset = 0,
      sortBy = 'estimatedSavings',
      sortOrder = 'desc',
      accountId
    } = req.query;
    
    let filteredOptimizations = [...optimizations];
    
    // Apply filters
    if (status) {
      filteredOptimizations = filteredOptimizations.filter(o => o.status === status);
    }
    
    if (riskLevel) {
      filteredOptimizations = filteredOptimizations.filter(o => o.riskLevel === riskLevel);
    }
    
    if (optimizationType) {
      filteredOptimizations = filteredOptimizations.filter(o => o.optimizationType === optimizationType);
    }
    
    if (resourceId) {
      filteredOptimizations = filteredOptimizations.filter(o => o.resourceId === resourceId);
    }
    
    if (accountId && accountId !== 'all') {
      filteredOptimizations = filteredOptimizations.filter(o => o.accountId === accountId);
    }
    
    if (region && region !== 'all') {
      filteredOptimizations = filteredOptimizations.filter(o => o.region === region);
    }
    
    if (minSavings) {
      filteredOptimizations = filteredOptimizations.filter(o => o.estimatedSavings >= parseFloat(minSavings));
    }
    
    if (maxSavings) {
      filteredOptimizations = filteredOptimizations.filter(o => o.estimatedSavings <= parseFloat(maxSavings));
    }
    
    // Apply sorting
    filteredOptimizations.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      // Handle numeric sorting
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'desc' ? bValue - aValue : aValue - bValue;
      }
      
      // Handle string sorting
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'desc' ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
      }
      
      return 0;
    });
    
    // Apply pagination
    const startIndex = parseInt(offset);
    const endIndex = startIndex + parseInt(limit);
    const paginatedOptimizations = filteredOptimizations.slice(startIndex, endIndex);
    
    console.log(`🎯 SENDING OPTIMIZATIONS: ${paginatedOptimizations.length} of ${filteredOptimizations.length} total`);
    
    res.json({
      success: true,
      data: paginatedOptimizations,
      message: `Retrieved ${paginatedOptimizations.length} optimization recommendations`,
      metadata: {
        total: filteredOptimizations.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: endIndex < filteredOptimizations.length,
        totalSavings: filteredOptimizations.reduce((sum, opt) => sum + opt.estimatedSavings, 0)
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving optimizations:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve optimizations: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/optimizations
 * Create new optimization recommendation
 */
router.post('/', (req, res) => {
  try {
    console.log('💡 RECEIVED OPTIMIZATION:', req.body);
    
    // Create CostOptimization instance for validation
    const optimization = new CostOptimization(req.body);
    
    // Validate the optimization data
    const validation = optimization.validate();
    if (!validation.isValid) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'Invalid optimization data: ' + validation.errors.join(', '),
        errors: validation.errors,
        timestamp: new Date().toISOString()
      });
    }
    
    // Set approval requirement based on risk and savings
    optimization.approvalRequired = optimization.requiresApproval();
    
    // Check if optimization already exists (update vs create)
    const existingIndex = optimizations.findIndex(
      o => o.resourceId === optimization.resourceId && 
           o.optimizationType === optimization.optimizationType &&
           o.status === 'pending'
    );
    
    if (existingIndex >= 0) {
      // Update existing optimization
      optimizations[existingIndex] = optimization.toJSON();
      console.log('🔄 UPDATED EXISTING OPTIMIZATION:', optimization.optimizationId);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('optimization_updated', {
          optimization: optimization.toJSON(),
          totalOptimizations: optimizations.length,
          totalPotentialSavings: optimizations.reduce((sum, o) => sum + o.estimatedSavings, 0)
        });
      }
    } else {
      // Add new optimization
      optimizations.push(optimization.toJSON());
      console.log('➕ ADDED NEW OPTIMIZATION:', optimization.optimizationId);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('optimization_added', {
          optimization: optimization.toJSON(),
          totalOptimizations: optimizations.length,
          totalPotentialSavings: optimizations.reduce((sum, o) => sum + o.estimatedSavings, 0)
        });
      }
    }
    
    res.json({
      success: true,
      data: optimization.toJSON(),
      message: existingIndex >= 0 ? 'Optimization updated successfully' : 'Optimization created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error saving optimization:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to save optimization: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/optimizations/approve
 * Approve optimization actions
 */
router.post('/approve', (req, res) => {
  try {
    const { optimizationIds, approvedBy, comments } = req.body;
    
    console.log('✅ APPROVAL REQUEST:', { optimizationIds, approvedBy, comments });
    
    if (!optimizationIds || !Array.isArray(optimizationIds) || optimizationIds.length === 0) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'optimizationIds array is required',
        timestamp: new Date().toISOString()
      });
    }
    
    if (!approvedBy) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'approvedBy is required',
        timestamp: new Date().toISOString()
      });
    }
    
    const approvedOptimizations = [];
    const failedApprovals = [];
    
    optimizationIds.forEach(optimizationId => {
      const optimizationIndex = optimizations.findIndex(o => o.optimizationId === optimizationId);
      
      if (optimizationIndex === -1) {
        failedApprovals.push({
          optimizationId,
          reason: 'Optimization not found'
        });
        return;
      }
      
      const optimization = new CostOptimization(optimizations[optimizationIndex]);
      
      if (optimization.approve(approvedBy)) {
        // Add comments if provided
        if (comments) {
          optimization.approvalComments = comments;
        }
        
        optimizations[optimizationIndex] = optimization.toJSON();
        approvedOptimizations.push(optimization.toJSON());
        console.log('✅ APPROVED OPTIMIZATION:', optimizationId);
      } else {
        failedApprovals.push({
          optimizationId,
          reason: `Cannot approve optimization in status: ${optimization.status}`
        });
      }
    });
    
    const response = {
      success: true,
      data: {
        approved: approvedOptimizations,
        failed: failedApprovals
      },
      message: `Approved ${approvedOptimizations.length} of ${optimizationIds.length} optimizations`,
      timestamp: new Date().toISOString()
    };
    
    // If some approvals failed, include warning in response
    if (failedApprovals.length > 0) {
      response.warning = `${failedApprovals.length} approvals failed`;
    }
    
    res.json(response);
  } catch (error) {
    console.error('❌ Error approving optimizations:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to approve optimizations: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/optimizations/:optimizationId
 * Get specific optimization by ID
 */
router.get('/:optimizationId', (req, res) => {
  try {
    const { optimizationId } = req.params;
    
    const optimization = optimizations.find(o => o.optimizationId === optimizationId);
    
    if (!optimization) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Optimization not found: ${optimizationId}`,
        timestamp: new Date().toISOString()
      });
    }
    
    console.log('📋 SENDING SPECIFIC OPTIMIZATION:', optimizationId);
    
    res.json({
      success: true,
      data: optimization,
      message: 'Optimization retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving optimization:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve optimization: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * PUT /api/optimizations/:optimizationId/status
 * Update optimization status (for execution tracking)
 */
router.put('/:optimizationId/status', (req, res) => {
  try {
    const { optimizationId } = req.params;
    const { status, executionResult, rollbackData } = req.body;
    
    const optimizationIndex = optimizations.findIndex(o => o.optimizationId === optimizationId);
    
    if (optimizationIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Optimization not found: ${optimizationId}`,
        timestamp: new Date().toISOString()
      });
    }
    
    const optimization = new CostOptimization(optimizations[optimizationIndex]);
    
    // Update status based on the request
    if (status === 'executed' && executionResult) {
      optimization.markExecuted(executionResult);
    } else {
      optimization.status = status;
      if (rollbackData) {
        optimization.rollbackData = rollbackData;
      }
    }
    
    optimizations[optimizationIndex] = optimization.toJSON();
    
    console.log('🔄 UPDATED OPTIMIZATION STATUS:', optimizationId, 'to', status);
    
    res.json({
      success: true,
      data: optimization.toJSON(),
      message: `Optimization status updated to ${status}`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error updating optimization status:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to update optimization status: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/optimizations/stats/summary
 * Get optimization statistics and summary
 */
router.get('/stats/summary', (req, res) => {
  try {
    const stats = {
      totalOptimizations: optimizations.length,
      byStatus: {},
      byRiskLevel: {},
      byType: {},
      totalPotentialSavings: 0,
      approvedSavings: 0,
      executedSavings: 0,
      averageConfidenceScore: 0
    };
    
    let totalConfidence = 0;
    
    optimizations.forEach(optimization => {
      // Count by status
      stats.byStatus[optimization.status] = (stats.byStatus[optimization.status] || 0) + 1;
      
      // Count by risk level
      stats.byRiskLevel[optimization.riskLevel] = (stats.byRiskLevel[optimization.riskLevel] || 0) + 1;
      
      // Count by type
      stats.byType[optimization.optimizationType] = (stats.byType[optimization.optimizationType] || 0) + 1;
      
      // Sum savings
      stats.totalPotentialSavings += optimization.estimatedSavings || 0;
      
      if (optimization.status === 'approved' || optimization.status === 'executed') {
        stats.approvedSavings += optimization.estimatedSavings || 0;
      }
      
      if (optimization.status === 'executed') {
        stats.executedSavings += optimization.estimatedSavings || 0;
      }
      
      // Sum confidence scores
      totalConfidence += optimization.confidenceScore || 0;
    });
    
    // Calculate average confidence
    stats.averageConfidenceScore = optimizations.length > 0 ? 
      Math.round(totalConfidence / optimizations.length) : 0;
    
    console.log('📈 SENDING OPTIMIZATION STATS');
    
    res.json({
      success: true,
      data: stats,
      message: 'Optimization statistics retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error generating optimization stats:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to generate optimization statistics: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

router.optimizations = optimizations;
module.exports = router;