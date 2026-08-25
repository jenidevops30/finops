/**
 * Savings Routes
 * 
 * API endpoints for tracking achieved savings and ROI analysis.
 * Handles savings data from optimization executions and provides dashboard-ready formats.
 * 
 * Requirements: 8.5, 9.4, 9.2, 9.3
 */

const express = require('express');
const router = express.Router();

// In-memory storage (will be replaced with database in production)
let savingsRecords = [];
let savingsTargets = [];

/**
 * GET /api/savings
 * Retrieve savings records with dashboard formatting and filtering
 */
router.get('/', (req, res) => {
  try {
    const { 
      timeRange = '30d',
      service,
      region,
      optimizationType,
      minAmount,
      maxAmount,
      groupBy = 'day',
      format = 'standard',
      limit = 100, 
      offset = 0,
      accountId
    } = req.query;
    
    let filteredSavings = [...savingsRecords];
    
    // Apply time range filter
    const now = new Date();
    let startDate;
    switch (timeRange) {
      case '7d':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90d':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      case '1y':
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }
    
    filteredSavings = filteredSavings.filter(s => 
      new Date(s.achievedAt) >= startDate
    );
    
    // Apply other filters
    if (service) {
      filteredSavings = filteredSavings.filter(s => s.serviceType === service);
    }
    
    if (accountId && accountId !== 'all') {
      filteredSavings = filteredSavings.filter(s => s.accountId === accountId);
    }
    
    if (region && region !== 'all') {
      filteredSavings = filteredSavings.filter(s => s.region === region);
    }
    
    if (optimizationType) {
      filteredSavings = filteredSavings.filter(s => s.optimizationType === optimizationType);
    }
    
    if (minAmount) {
      filteredSavings = filteredSavings.filter(s => s.savingsAmount >= parseFloat(minAmount));
    }
    
    if (maxAmount) {
      filteredSavings = filteredSavings.filter(s => s.savingsAmount <= parseFloat(maxAmount));
    }
    
    // Format data based on request type
    let responseData;
    if (format === 'chart') {
      responseData = formatForCharts(filteredSavings, groupBy, timeRange);
    } else if (format === 'summary') {
      responseData = formatSummary(filteredSavings);
    } else {
      // Apply pagination for standard format
      const startIndex = parseInt(offset);
      const endIndex = startIndex + parseInt(limit);
      responseData = filteredSavings.slice(startIndex, endIndex);
    }
    
    console.log(`💰 SENDING SAVINGS DATA: ${format} format, ${Array.isArray(responseData) ? responseData.length : 'summary'} records`);
    
    const response = {
      success: true,
      data: responseData,
      message: `Retrieved savings data in ${format} format`,
      timestamp: new Date().toISOString()
    };
    
    // Add metadata for standard format
    if (format === 'standard') {
      response.metadata = {
        total: filteredSavings.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: parseInt(offset) + parseInt(limit) < filteredSavings.length,
        totalSavings: filteredSavings.reduce((sum, s) => sum + s.savingsAmount, 0),
        timeRange,
        filters: { service, region, optimizationType, minAmount, maxAmount }
      };
    }
    
    res.json(response);
  } catch (error) {
    console.error('❌ Error retrieving savings:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve savings: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/savings
 * Record new savings achievement
 */
router.post('/', (req, res) => {
  try {
    const savingsData = req.body;
    
    console.log('💰 RECEIVED SAVINGS RECORD:', savingsData);
    
    // Validate required fields
    const requiredFields = ['optimizationId', 'savingsAmount', 'serviceType'];
    const missingFields = requiredFields.filter(field => !savingsData[field]);
    
    if (missingFields.length > 0) {
      return res.status(400).json({
        success: false,
        data: null,
        message: `Missing required fields: ${missingFields.join(', ')}`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Create savings record
    const newSavings = {
      savingsId: savingsData.savingsId || `savings_${Date.now()}`,
      optimizationId: savingsData.optimizationId,
      resourceId: savingsData.resourceId || '',
      serviceType: savingsData.serviceType,
      region: savingsData.region || 'us-east-1',
      optimizationType: savingsData.optimizationType || 'unknown',
      savingsAmount: parseFloat(savingsData.savingsAmount),
      previousCost: parseFloat(savingsData.previousCost || 0),
      newCost: parseFloat(savingsData.newCost || 0),
      savingsPercentage: savingsData.savingsPercentage || 0,
      achievedAt: savingsData.achievedAt || new Date().toISOString(),
      validatedAt: savingsData.validatedAt || null,
      annualizedSavings: parseFloat(savingsData.savingsAmount) * 12, // Estimate annual savings
      currency: savingsData.currency || 'USD',
      tags: savingsData.tags || {},
      executionDetails: savingsData.executionDetails || {},
      timestamp: new Date().toISOString()
    };
    
    // Check for duplicate savings records
    const existingIndex = savingsRecords.findIndex(
      s => s.optimizationId === newSavings.optimizationId
    );
    
    if (existingIndex >= 0) {
      // Update existing record
      savingsRecords[existingIndex] = newSavings;
      console.log('🔄 UPDATED EXISTING SAVINGS RECORD:', newSavings.savingsId);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('savings_updated', {
          savings: newSavings,
          totalSavings: savingsRecords.reduce((sum, s) => sum + s.savingsAmount, 0),
          totalRecords: savingsRecords.length
        });
      }
    } else {
      // Add new record
      savingsRecords.push(newSavings);
      console.log('➕ ADDED NEW SAVINGS RECORD:', newSavings.savingsId);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('savings_added', {
          savings: newSavings,
          totalSavings: savingsRecords.reduce((sum, s) => sum + s.savingsAmount, 0),
          totalRecords: savingsRecords.length
        });
      }
    }
    
    res.json({
      success: true,
      data: newSavings,
      message: existingIndex >= 0 ? 'Savings record updated successfully' : 'Savings record created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error saving savings record:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to save savings record: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/savings/chart-data
 * Get savings data formatted for Recharts
 */
router.get('/chart-data', (req, res) => {
  try {
    const { 
      timeRange = '30d',
      groupBy = 'day',
      service,
      region,
      accountId
    } = req.query;
    
    let filteredSavings = [...savingsRecords];
    
    // Apply filters
    if (service) {
      filteredSavings = filteredSavings.filter(s => s.serviceType === service);
    }
    
    if (accountId && accountId !== 'all') {
      filteredSavings = filteredSavings.filter(s => s.accountId === accountId);
    }
    
    if (region && region !== 'all') {
      filteredSavings = filteredSavings.filter(s => s.region === region);
    }
    
    // Apply time range
    const now = new Date();
    let startDate;
    switch (timeRange) {
      case '7d':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90d':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      case '1y':
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }
    
    filteredSavings = filteredSavings.filter(s => 
      new Date(s.achievedAt) >= startDate
    );
    
    const chartData = formatForCharts(filteredSavings, groupBy, timeRange);
    
    console.log('📊 SENDING CHART DATA:', chartData.timeSeries?.length || 0, 'data points');
    
    res.json({
      success: true,
      data: chartData,
      message: 'Chart data retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving chart data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve chart data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/savings/summary
 * Get savings summary with KPIs
 */
router.get('/summary', (req, res) => {
  try {
    const { timeRange = '30d', accountId, region } = req.query;
    
    let filteredSavings = [...savingsRecords];
    
    if (accountId && accountId !== 'all') {
      filteredSavings = filteredSavings.filter(s => s.accountId === accountId);
    }
    
    if (region && region !== 'all') {
      filteredSavings = filteredSavings.filter(s => s.region === region);
    }
    
    // Apply time range
    const now = new Date();
    let startDate;
    switch (timeRange) {
      case '7d':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90d':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      case '1y':
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }
    
    filteredSavings = filteredSavings.filter(s => 
      new Date(s.achievedAt) >= startDate
    );
    
    const summary = formatSummary(filteredSavings);
    
    console.log('📈 SENDING SAVINGS SUMMARY');
    
    res.json({
      success: true,
      data: summary,
      message: 'Savings summary retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving savings summary:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve savings summary: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/savings/targets
 * Get savings targets and progress
 */
router.get('/targets', (req, res) => {
  try {
    const targets = savingsTargets.map(target => {
      const actualSavings = savingsRecords
        .filter(s => s.serviceType === target.serviceType || !target.serviceType)
        .filter(s => new Date(s.achievedAt) >= new Date(target.startDate))
        .filter(s => new Date(s.achievedAt) <= new Date(target.endDate))
        .reduce((sum, s) => sum + s.savingsAmount, 0);
      
      return {
        ...target,
        actualSavings,
        progress: target.targetAmount > 0 ? (actualSavings / target.targetAmount) * 100 : 0,
        remaining: Math.max(0, target.targetAmount - actualSavings)
      };
    });
    
    res.json({
      success: true,
      data: targets,
      message: 'Savings targets retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving savings targets:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve savings targets: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/savings/targets
 * Create or update savings target
 */
router.post('/targets', (req, res) => {
  try {
    const targetData = req.body;
    
    const newTarget = {
      targetId: targetData.targetId || `target_${Date.now()}`,
      name: targetData.name || 'Savings Target',
      targetAmount: parseFloat(targetData.targetAmount),
      serviceType: targetData.serviceType || null,
      region: targetData.region || null,
      startDate: targetData.startDate || new Date().toISOString(),
      endDate: targetData.endDate || new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
      description: targetData.description || '',
      createdAt: new Date().toISOString()
    };
    
    savingsTargets.push(newTarget);
    
    res.status(201).json({
      success: true,
      data: newTarget,
      message: 'Savings target created successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error creating savings target:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create savings target: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Helper function to format data for charts (Recharts compatibility)
 */
function formatForCharts(savings, groupBy, timeRange) {
  // Group savings by time period
  const grouped = {};
  const now = new Date();
  
  // Initialize time buckets
  let buckets = [];
  let bucketSize;
  
  switch (groupBy) {
    case 'hour':
      bucketSize = 60 * 60 * 1000; // 1 hour
      break;
    case 'day':
      bucketSize = 24 * 60 * 60 * 1000; // 1 day
      break;
    case 'week':
      bucketSize = 7 * 24 * 60 * 60 * 1000; // 1 week
      break;
    case 'month':
      bucketSize = 30 * 24 * 60 * 60 * 1000; // 30 days
      break;
    default:
      bucketSize = 24 * 60 * 60 * 1000; // Default to day
  }
  
  // Create time buckets
  const timeRangeDays = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
  const startTime = now.getTime() - (timeRangeDays * 24 * 60 * 60 * 1000);
  
  for (let time = startTime; time <= now.getTime(); time += bucketSize) {
    const bucketKey = new Date(time).toISOString().split('T')[0];
    buckets.push({
      date: bucketKey,
      timestamp: time,
      totalSavings: 0,
      count: 0,
      cumulativeSavings: 0
    });
  }
  
  // Aggregate savings into buckets
  savings.forEach(saving => {
    const savingTime = new Date(saving.achievedAt).getTime();
    const bucketIndex = Math.floor((savingTime - startTime) / bucketSize);
    
    if (bucketIndex >= 0 && bucketIndex < buckets.length) {
      buckets[bucketIndex].totalSavings += saving.savingsAmount;
      buckets[bucketIndex].count += 1;
    }
  });
  
  // Calculate cumulative savings
  let cumulative = 0;
  buckets.forEach(bucket => {
    cumulative += bucket.totalSavings;
    bucket.cumulativeSavings = cumulative;
  });
  
  // Service breakdown
  const serviceBreakdown = {};
  savings.forEach(saving => {
    if (!serviceBreakdown[saving.serviceType]) {
      serviceBreakdown[saving.serviceType] = {
        name: saving.serviceType,
        value: 0,
        count: 0
      };
    }
    serviceBreakdown[saving.serviceType].value += saving.savingsAmount;
    serviceBreakdown[saving.serviceType].count += 1;
  });
  
  // Optimization type breakdown
  const optimizationBreakdown = {};
  savings.forEach(saving => {
    if (!optimizationBreakdown[saving.optimizationType]) {
      optimizationBreakdown[saving.optimizationType] = {
        name: saving.optimizationType,
        value: 0,
        count: 0
      };
    }
    optimizationBreakdown[saving.optimizationType].value += saving.savingsAmount;
    optimizationBreakdown[saving.optimizationType].count += 1;
  });
  
  return {
    timeSeries: buckets,
    serviceBreakdown: Object.values(serviceBreakdown),
    optimizationBreakdown: Object.values(optimizationBreakdown),
    totalSavings: savings.reduce((sum, s) => sum + s.savingsAmount, 0),
    totalCount: savings.length,
    averageSavings: savings.length > 0 ? savings.reduce((sum, s) => sum + s.savingsAmount, 0) / savings.length : 0
  };
}

/**
 * Helper function to format summary data
 */
function formatSummary(savings) {
  const totalSavings = savings.reduce((sum, s) => sum + s.savingsAmount, 0);
  const totalCount = savings.length;
  const averageSavings = totalCount > 0 ? totalSavings / totalCount : 0;
  
  // Calculate annualized savings
  const annualizedSavings = savings.reduce((sum, s) => sum + (s.annualizedSavings || s.savingsAmount * 12), 0);
  
  // Service distribution
  const serviceDistribution = {};
  savings.forEach(saving => {
    serviceDistribution[saving.serviceType] = (serviceDistribution[saving.serviceType] || 0) + saving.savingsAmount;
  });
  
  // Region distribution
  const regionDistribution = {};
  savings.forEach(saving => {
    regionDistribution[saving.region] = (regionDistribution[saving.region] || 0) + saving.savingsAmount;
  });
  
  // Top savings opportunities
  const topSavings = [...savings]
    .sort((a, b) => b.savingsAmount - a.savingsAmount)
    .slice(0, 10);
  
  return {
    totalSavings,
    totalCount,
    averageSavings,
    annualizedSavings,
    serviceDistribution,
    regionDistribution,
    topSavings,
    savingsRate: totalCount > 0 ? (totalSavings / totalCount) : 0,
    lastUpdated: new Date().toISOString()
  };
}

router.savingsRecords = savingsRecords;
module.exports = router;