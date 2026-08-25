/**
 * Anomaly Routes
 * 
 * API endpoints for managing cost anomalies and alerts.
 * Handles anomaly data from the Python anomaly detector engine.
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 9.1
 */

const express = require('express');
const router = express.Router();
const CostAnomaly = require('../models/CostAnomaly');

// In-memory storage (will be replaced with database in production)
let anomalies = [];
let anomalyAlerts = [];

/**
 * GET /api/anomalies
 * Retrieve all anomalies with optional filtering
 */
router.get('/', (req, res) => {
  try {
    const { 
      severity, 
      anomalyType, 
      region,
      resolved,
      startDate,
      endDate,
      limit = 100, 
      offset = 0,
      accountId
    } = req.query;
    
    let filteredAnomalies = [...anomalies];
    
    // Apply filters
    if (severity) {
      filteredAnomalies = filteredAnomalies.filter(a => a.severity === severity);
    }
    
    if (anomalyType) {
      filteredAnomalies = filteredAnomalies.filter(a => a.anomalyType === anomalyType);
    }
    
    if (accountId && accountId !== 'all') {
      filteredAnomalies = filteredAnomalies.filter(a => a.accountId === accountId);
    }
    
    if (region && region !== 'all') {
      filteredAnomalies = filteredAnomalies.filter(a => a.region === region);
    }
    
    if (resolved !== undefined) {
      const isResolved = resolved === 'true';
      filteredAnomalies = filteredAnomalies.filter(a => a.resolved === isResolved);
    }
    
    // Date range filtering
    if (startDate) {
      filteredAnomalies = filteredAnomalies.filter(a => 
        new Date(a.detectedAt) >= new Date(startDate)
      );
    }
    
    if (endDate) {
      filteredAnomalies = filteredAnomalies.filter(a => 
        new Date(a.detectedAt) <= new Date(endDate)
      );
    }
    
    // Sort by detection date (newest first)
    filteredAnomalies.sort((a, b) => new Date(b.detectedAt) - new Date(a.detectedAt));
    
    // Apply pagination
    const startIndex = parseInt(offset);
    const endIndex = startIndex + parseInt(limit);
    const paginatedAnomalies = filteredAnomalies.slice(startIndex, endIndex);
    
    res.json({
      success: true,
      data: {
        anomalies: paginatedAnomalies,
        total: filteredAnomalies.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: endIndex < filteredAnomalies.length
      },
      message: `Retrieved ${paginatedAnomalies.length} anomalies`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving anomalies:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve anomalies',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/anomalies/:anomalyId
 * Get specific anomaly by ID
 */
router.get('/:anomalyId', (req, res) => {
  try {
    const { anomalyId } = req.params;
    const anomaly = anomalies.find(a => a.anomalyId === anomalyId);
    
    if (!anomaly) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Anomaly ${anomalyId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    res.json({
      success: true,
      data: anomaly,
      message: `Retrieved anomaly ${anomalyId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving anomaly:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve anomaly',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/anomalies
 * Create new anomaly record
 */
router.post('/', (req, res) => {
  try {
    const anomalyData = req.body;
    
    // Validate required fields
    const requiredFields = ['anomalyId', 'anomalyType', 'severity', 'actualCost', 'expectedCost'];
    const missingFields = requiredFields.filter(field => !anomalyData[field]);
    
    if (missingFields.length > 0) {
      return res.status(400).json({
        success: false,
        data: null,
        message: `Missing required fields: ${missingFields.join(', ')}`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Check if anomaly already exists
    const existingAnomaly = anomalies.find(a => a.anomalyId === anomalyData.anomalyId);
    if (existingAnomaly) {
      return res.status(409).json({
        success: false,
        data: null,
        message: `Anomaly ${anomalyData.anomalyId} already exists`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Create anomaly with defaults
    const newAnomaly = {
      anomalyId: anomalyData.anomalyId,
      detectedAt: anomalyData.detectedAt || new Date().toISOString(),
      anomalyType: anomalyData.anomalyType,
      severity: anomalyData.severity,
      region: anomalyData.region || 'us-east-1',
      serviceType: anomalyData.serviceType || 'unknown',
      actualCost: parseFloat(anomalyData.actualCost),
      expectedCost: parseFloat(anomalyData.expectedCost),
      deviationPercentage: anomalyData.deviationPercentage || 0,
      deviationStandardDeviations: anomalyData.deviationStandardDeviations || 0,
      baselineModel: anomalyData.baselineModel || 'unknown',
      rootCause: anomalyData.rootCause || 'Analysis pending',
      rootCauseAnalysis: anomalyData.rootCauseAnalysis || {},
      affectedResources: anomalyData.affectedResources || [],
      resolved: false,
      resolvedAt: null,
      resolvedBy: null,
      resolutionNotes: null,
      timestamp: anomalyData.timestamp || new Date().toISOString(),
      createdAt: new Date().toISOString()
    };
    
    anomalies.push(newAnomaly);
    
    res.status(201).json({
      success: true,
      data: newAnomaly,
      message: `Anomaly ${anomalyData.anomalyId} created successfully`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error creating anomaly:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create anomaly',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * PUT /api/anomalies/:anomalyId/resolve
 * Mark anomaly as resolved
 */
router.put('/:anomalyId/resolve', (req, res) => {
  try {
    const { anomalyId } = req.params;
    const { resolvedBy, resolutionNotes } = req.body;
    
    const anomalyIndex = anomalies.findIndex(a => a.anomalyId === anomalyId);
    if (anomalyIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Anomaly ${anomalyId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    // Update anomaly resolution status
    anomalies[anomalyIndex].resolved = true;
    anomalies[anomalyIndex].resolvedAt = new Date().toISOString();
    anomalies[anomalyIndex].resolvedBy = resolvedBy || 'system';
    anomalies[anomalyIndex].resolutionNotes = resolutionNotes || '';
    anomalies[anomalyIndex].lastUpdated = new Date().toISOString();
    
    res.json({
      success: true,
      data: anomalies[anomalyIndex],
      message: `Anomaly ${anomalyId} marked as resolved`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error resolving anomaly:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to resolve anomaly',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/anomalies/batch
 * Create multiple anomalies in batch
 */
router.post('/batch', (req, res) => {
  try {
    const { anomalies: anomalyList } = req.body;
    
    if (!Array.isArray(anomalyList) || anomalyList.length === 0) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'Invalid anomaly list provided',
        timestamp: new Date().toISOString()
      });
    }
    
    const createdAnomalies = [];
    const errors = [];
    
    for (const anomalyData of anomalyList) {
      try {
        // Validate required fields
        const requiredFields = ['anomalyId', 'anomalyType', 'severity', 'actualCost', 'expectedCost'];
        const missingFields = requiredFields.filter(field => !anomalyData[field]);
        
        if (missingFields.length > 0) {
          errors.push({
            anomalyId: anomalyData.anomalyId || 'unknown',
            error: `Missing required fields: ${missingFields.join(', ')}`
          });
          continue;
        }
        
        // Check if anomaly already exists
        const existingAnomaly = anomalies.find(a => a.anomalyId === anomalyData.anomalyId);
        if (existingAnomaly) {
          errors.push({
            anomalyId: anomalyData.anomalyId,
            error: 'Anomaly already exists'
          });
          continue;
        }
        
        // Create anomaly
        const newAnomaly = {
          anomalyId: anomalyData.anomalyId,
          detectedAt: anomalyData.detectedAt || new Date().toISOString(),
          anomalyType: anomalyData.anomalyType,
          severity: anomalyData.severity,
          region: anomalyData.region || 'us-east-1',
          serviceType: anomalyData.serviceType || 'unknown',
          actualCost: parseFloat(anomalyData.actualCost),
          expectedCost: parseFloat(anomalyData.expectedCost),
          deviationPercentage: anomalyData.deviationPercentage || 0,
          deviationStandardDeviations: anomalyData.deviationStandardDeviations || 0,
          baselineModel: anomalyData.baselineModel || 'unknown',
          rootCause: anomalyData.rootCause || 'Analysis pending',
          rootCauseAnalysis: anomalyData.rootCauseAnalysis || {},
          affectedResources: anomalyData.affectedResources || [],
          resolved: false,
          resolvedAt: null,
          resolvedBy: null,
          resolutionNotes: null,
          timestamp: anomalyData.timestamp || new Date().toISOString(),
          createdAt: new Date().toISOString()
        };
        
        anomalies.push(newAnomaly);
        createdAnomalies.push(newAnomaly);
        
      } catch (error) {
        errors.push({
          anomalyId: anomalyData.anomalyId || 'unknown',
          error: error.message
        });
      }
    }
    
    res.status(201).json({
      success: true,
      data: {
        created: createdAnomalies,
        errors: errors,
        totalProcessed: anomalyList.length,
        successCount: createdAnomalies.length,
        errorCount: errors.length
      },
      message: `Batch processed: ${createdAnomalies.length} created, ${errors.length} errors`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error processing batch anomalies:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to process batch anomalies',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/anomalies/alerts
 * Get anomaly alerts
 */
router.get('/alerts', (req, res) => {
  try {
    const { severity, acknowledged } = req.query;
    
    let filteredAlerts = [...anomalyAlerts];
    
    // Apply filters
    if (severity) {
      filteredAlerts = filteredAlerts.filter(a => a.severity === severity);
    }
    
    if (acknowledged !== undefined) {
      const isAcknowledged = acknowledged === 'true';
      filteredAlerts = filteredAlerts.filter(a => a.acknowledged === isAcknowledged);
    }
    
    // Sort by timestamp (newest first)
    filteredAlerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    res.json({
      success: true,
      data: {
        alerts: filteredAlerts,
        total: filteredAlerts.length
      },
      message: `Retrieved ${filteredAlerts.length} anomaly alerts`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving anomaly alerts:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve anomaly alerts',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * POST /api/anomalies/alerts
 * Create new anomaly alert
 */
router.post('/alerts', (req, res) => {
  try {
    const alertData = req.body;
    
    const newAlert = {
      alertId: alertData.alertId || `alert_${Date.now()}`,
      timestamp: alertData.timestamp || new Date().toISOString(),
      severity: alertData.severity || 'MEDIUM',
      title: alertData.title || 'Cost Anomaly Detected',
      description: alertData.description || '',
      anomaly: alertData.anomaly || {},
      rootCause: alertData.rootCause || {},
      recommendations: alertData.recommendations || [],
      region: alertData.region || 'us-east-1',
      alertType: 'COST_ANOMALY',
      acknowledged: false,
      acknowledgedAt: null,
      acknowledgedBy: null,
      createdAt: new Date().toISOString()
    };
    
    anomalyAlerts.push(newAlert);
    
    res.status(201).json({
      success: true,
      data: newAlert,
      message: `Anomaly alert ${newAlert.alertId} created successfully`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error creating anomaly alert:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to create anomaly alert',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * PUT /api/anomalies/alerts/:alertId/acknowledge
 * Acknowledge an anomaly alert
 */
router.put('/alerts/:alertId/acknowledge', (req, res) => {
  try {
    const { alertId } = req.params;
    const { acknowledgedBy } = req.body;
    
    const alertIndex = anomalyAlerts.findIndex(a => a.alertId === alertId);
    if (alertIndex === -1) {
      return res.status(404).json({
        success: false,
        data: null,
        message: `Alert ${alertId} not found`,
        timestamp: new Date().toISOString()
      });
    }
    
    anomalyAlerts[alertIndex].acknowledged = true;
    anomalyAlerts[alertIndex].acknowledgedAt = new Date().toISOString();
    anomalyAlerts[alertIndex].acknowledgedBy = acknowledgedBy || 'system';
    
    res.json({
      success: true,
      data: anomalyAlerts[alertIndex],
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
 * GET /api/anomalies/stats/summary
 * Get anomaly statistics summary
 */
router.get('/stats/summary', (req, res) => {
  try {
    const totalAnomalies = anomalies.length;
    const unresolvedAnomalies = anomalies.filter(a => !a.resolved).length;
    const resolvedAnomalies = anomalies.filter(a => a.resolved).length;
    
    // Severity distribution
    const severityDistribution = anomalies.reduce((acc, anomaly) => {
      acc[anomaly.severity] = (acc[anomaly.severity] || 0) + 1;
      return acc;
    }, {});
    
    // Type distribution
    const typeDistribution = anomalies.reduce((acc, anomaly) => {
      acc[anomaly.anomalyType] = (acc[anomaly.anomalyType] || 0) + 1;
      return acc;
    }, {});
    
    // Region distribution
    const regionDistribution = anomalies.reduce((acc, anomaly) => {
      acc[anomaly.region] = (acc[anomaly.region] || 0) + 1;
      return acc;
    }, {});
    
    // Calculate total cost impact
    const totalCostImpact = anomalies.reduce((sum, anomaly) => {
      return sum + (anomaly.actualCost - anomaly.expectedCost);
    }, 0);
    
    // Recent anomalies (last 24 hours)
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const recentAnomalies = anomalies.filter(a => 
      new Date(a.detectedAt) >= oneDayAgo
    ).length;
    
    const activeAlerts = anomalyAlerts.filter(a => !a.acknowledged).length;
    
    res.json({
      success: true,
      data: {
        totalAnomalies,
        unresolvedAnomalies,
        resolvedAnomalies,
        severityDistribution,
        typeDistribution,
        regionDistribution,
        totalCostImpact,
        recentAnomalies,
        activeAlerts,
        resolutionRate: totalAnomalies > 0 ? (resolvedAnomalies / totalAnomalies) * 100 : 0,
        averageCostImpact: totalAnomalies > 0 ? totalCostImpact / totalAnomalies : 0
      },
      message: 'Anomaly statistics retrieved successfully',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error retrieving anomaly statistics:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve anomaly statistics',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Export the router
router.anomalies = anomalies;
module.exports = router;