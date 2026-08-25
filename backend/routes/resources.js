/**
 * Resource Routes
 * 
 * API endpoints for managing AWS resource inventory across multiple services.
 * Handles resource discovery data from the Python automation engine.
 * 
 * Requirements: 1.1, 1.2, 1.3, 9.1
 */

const express = require('express');
const router = express.Router();
const ResourceInventory = require('../models/ResourceInventory');

// In-memory storage (will be replaced with database in production)
let resources = [];

/**
 * GET /api/resources
 * Retrieve resource inventory with optional filtering and dashboard formatting
 */
router.get('/', (req, res) => {
  try {
    const { 
      resourceType, 
      region, 
      state,
      service,
      costThreshold,
      utilizationThreshold,
      timeRange = '30d',
      format = 'standard',
      limit = 100, 
      offset = 0,
      sortBy = 'timestamp',
      sortOrder = 'desc',
      accountId
    } = req.query;
    
    let filteredResources = [...resources];
    
    // Apply filters
    if (resourceType) {
      filteredResources = filteredResources.filter(r => r.resourceType === resourceType);
    }
    
    if (accountId && accountId !== 'all') {
      filteredResources = filteredResources.filter(r => r.accountId === accountId);
    }
    
    if (region && region !== 'all') {
      filteredResources = filteredResources.filter(r => r.region === region);
    }
    
    if (state) {
      filteredResources = filteredResources.filter(r => r.state === state);
    }
    
    if (service) {
      filteredResources = filteredResources.filter(r => r.serviceType === service);
    }
    
    if (costThreshold) {
      const threshold = parseFloat(costThreshold);
      filteredResources = filteredResources.filter(r => r.currentCost >= threshold);
    }
    
    if (utilizationThreshold) {
      const threshold = parseFloat(utilizationThreshold);
      filteredResources = filteredResources.filter(r => {
        const avgUtilization = r.utilizationMetrics?.averageUtilization || 0;
        return avgUtilization <= threshold;
      });
    }
    
    // Apply time range filter
    if (timeRange !== 'all') {
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
        default:
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      }
      
      filteredResources = filteredResources.filter(r => 
        new Date(r.timestamp) >= startDate
      );
    }
    
    // Apply sorting
    filteredResources.sort((a, b) => {
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
      
      // Handle date sorting
      if (sortBy === 'timestamp') {
        return sortOrder === 'desc' ? 
          new Date(b.timestamp) - new Date(a.timestamp) : 
          new Date(a.timestamp) - new Date(b.timestamp);
      }
      
      return 0;
    });
    
    // Format data based on request type
    let responseData;
    if (format === 'chart') {
      responseData = formatResourcesForChart(filteredResources);
    } else if (format === 'summary') {
      responseData = formatResourcesSummary(filteredResources);
    } else {
      // Apply pagination for standard format
      const startIndex = parseInt(offset);
      const endIndex = startIndex + parseInt(limit);
      responseData = filteredResources.slice(startIndex, endIndex);
    }
    
    console.log(`📊 SENDING RESOURCES: ${format} format, ${Array.isArray(responseData) ? responseData.length : 'summary'} records`);
    
    const response = {
      success: true,
      data: responseData,
      message: `Retrieved ${Array.isArray(responseData) ? responseData.length : 'summary'} resources`,
      timestamp: new Date().toISOString()
    };
    
    // Add metadata for standard format
    if (format === 'standard') {
      response.metadata = {
        total: filteredResources.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: parseInt(offset) + parseInt(limit) < filteredResources.length,
        totalCost: filteredResources.reduce((sum, r) => sum + (r.currentCost || 0), 0),
        filters: { resourceType, region, state, service, costThreshold, utilizationThreshold, timeRange },
        sorting: { sortBy, sortOrder }
      };
    }
    
    res.json(response);
  } catch (error) {
    console.error('❌ Error retrieving resources:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve resources: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/resources
 * Add or update resource inventory data
 */
router.post('/', (req, res) => {
  try {
    console.log('📥 RECEIVED RESOURCE DATA:', req.body);
    
    // Create ResourceInventory instance for validation
    const resource = new ResourceInventory(req.body);
    
    // Validate the resource data
    const validation = resource.validate();
    if (!validation.isValid) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'Invalid resource data: ' + validation.errors.join(', '),
        errors: validation.errors,
        timestamp: new Date().toISOString()
      });
    }
    
    // Check if resource already exists (update vs create)
    const existingIndex = resources.findIndex(
      r => r.resourceId === resource.resourceId && r.region === resource.region
    );
    
    if (existingIndex >= 0) {
      // Update existing resource
      resources[existingIndex] = resource.toJSON();
      console.log('🔄 UPDATED EXISTING RESOURCE:', resource.resourceId);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('resource_updated', {
          resource: resource.toJSON(),
          totalResources: resources.length
        });
      }
    } else {
      // Add new resource
      resources.push(resource.toJSON());
      console.log('➕ ADDED NEW RESOURCE:', resource.resourceId);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('resource_added', {
          resource: resource.toJSON(),
          totalResources: resources.length
        });
      }
    }
    
    res.json({
      success: true,
      data: resource.toJSON(),
      message: existingIndex >= 0 ? 'Resource updated successfully' : 'Resource added successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error saving resource:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to save resource: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/resources/:resourceId
 * Get specific resource by ID
 */
router.get('/:resourceId', (req, res) => {
  try {
    const { resourceId } = req.params;
    const { region } = req.query;
    
    const resource = resources.find(r => {
      if (region) {
        return r.resourceId === resourceId && r.region === region;
      }
      return r.resourceId === resourceId;
    });
    
    if (!resource) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Resource not found: ${resourceId}`,
        timestamp: new Date().toISOString()
      });
    }
    
    console.log('📋 SENDING SPECIFIC RESOURCE:', resourceId);
    
    res.json({
      success: true,
      data: resource,
      message: 'Resource retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving resource:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve resource: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * DELETE /api/resources/:resourceId
 * Remove resource from inventory (for cleanup)
 */
router.delete('/:resourceId', (req, res) => {
  try {
    const { resourceId } = req.params;
    const { region } = req.query;
    
    const resourceIndex = resources.findIndex(r => {
      if (region) {
        return r.resourceId === resourceId && r.region === region;
      }
      return r.resourceId === resourceId;
    });
    
    if (resourceIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Resource not found: ${resourceId}`,
        timestamp: new Date().toISOString()
      });
    }
    
    const removedResource = resources.splice(resourceIndex, 1)[0];
    console.log('🗑️ REMOVED RESOURCE:', resourceId);
    
    res.json({
      success: true,
      data: removedResource,
      message: 'Resource removed successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error removing resource:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to remove resource: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/resources/stats/summary
 * Get resource inventory statistics
 */
router.get('/stats/summary', (req, res) => {
  try {
    const stats = {
      totalResources: resources.length,
      byType: {},
      byRegion: {},
      byState: {},
      totalCost: 0,
      optimizationOpportunities: 0
    };
    
    resources.forEach(resource => {
      // Count by type
      stats.byType[resource.resourceType] = (stats.byType[resource.resourceType] || 0) + 1;
      
      // Count by region
      stats.byRegion[resource.region] = (stats.byRegion[resource.region] || 0) + 1;
      
      // Count by state
      stats.byState[resource.state] = (stats.byState[resource.state] || 0) + 1;
      
      // Sum costs
      stats.totalCost += resource.currentCost || 0;
      
      // Count optimization opportunities
      stats.optimizationOpportunities += (resource.optimizationOpportunities || []).length;
    });
    
    console.log('📈 SENDING RESOURCE STATS');
    
    res.json({
      success: true,
      data: stats,
      message: 'Resource statistics retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error generating resource stats:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to generate resource statistics: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Helper function to format resources data for charts
 */
function formatResourcesForChart(resources) {
  // Service distribution
  const serviceDistribution = {};
  resources.forEach(resource => {
    if (!serviceDistribution[resource.resourceType]) {
      serviceDistribution[resource.resourceType] = {
        name: resource.resourceType,
        value: 0,
        cost: 0,
        count: 0
      };
    }
    serviceDistribution[resource.resourceType].value += 1;
    serviceDistribution[resource.resourceType].cost += resource.currentCost || 0;
    serviceDistribution[resource.resourceType].count += 1;
  });
  
  // Region distribution
  const regionDistribution = {};
  resources.forEach(resource => {
    if (!regionDistribution[resource.region]) {
      regionDistribution[resource.region] = {
        name: resource.region,
        value: 0,
        cost: 0,
        count: 0
      };
    }
    regionDistribution[resource.region].value += 1;
    regionDistribution[resource.region].cost += resource.currentCost || 0;
    regionDistribution[resource.region].count += 1;
  });
  
  // Cost vs Utilization scatter plot
  const costUtilizationData = resources.map(resource => ({
    x: resource.utilizationMetrics?.averageUtilization || 0,
    y: resource.currentCost || 0,
    resourceType: resource.resourceType,
    resourceId: resource.resourceId,
    region: resource.region
  }));
  
  return {
    serviceDistribution: Object.values(serviceDistribution),
    regionDistribution: Object.values(regionDistribution),
    costUtilizationScatter: costUtilizationData,
    totalResources: resources.length,
    totalCost: resources.reduce((sum, r) => sum + (r.currentCost || 0), 0)
  };
}

/**
 * Helper function to format resources summary
 */
function formatResourcesSummary(resources) {
  const totalResources = resources.length;
  const totalCost = resources.reduce((sum, r) => sum + (r.currentCost || 0), 0);
  const averageCost = totalResources > 0 ? totalCost / totalResources : 0;
  
  // State distribution
  const stateDistribution = {};
  resources.forEach(resource => {
    stateDistribution[resource.state] = (stateDistribution[resource.state] || 0) + 1;
  });
  
  // Service distribution
  const serviceDistribution = {};
  resources.forEach(resource => {
    serviceDistribution[resource.resourceType] = (serviceDistribution[resource.resourceType] || 0) + (resource.currentCost || 0);
  });
  
  // Optimization opportunities
  const optimizationOpportunities = resources.reduce((sum, r) => sum + (r.optimizationOpportunities?.length || 0), 0);
  
  // Underutilized resources (utilization < 20%)
  const underutilizedResources = resources.filter(r => 
    (r.utilizationMetrics?.averageUtilization || 100) < 20
  ).length;
  
  return {
    totalResources,
    totalCost,
    averageCost,
    stateDistribution,
    serviceDistribution,
    optimizationOpportunities,
    underutilizedResources,
    utilizationRate: totalResources > 0 ? ((totalResources - underutilizedResources) / totalResources) * 100 : 0,
    lastUpdated: new Date().toISOString()
  };
}

router.resources = resources;
module.exports = router;