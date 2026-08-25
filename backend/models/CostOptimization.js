/**
 * CostOptimization Model
 * 
 * Represents cost optimization recommendations with approval workflow,
 * risk assessment, and savings projections.
 * 
 * Requirements: 8.1, 8.3, 2.1, 2.2, 2.3
 */

class CostOptimization {
  constructor(data = {}) {
    // Handle null input
    if (data === null || data === undefined) {
      data = {};
    }
    // Required fields
    this.optimizationId = data.optimizationId || this.generateId();
    this.resourceId = data.resourceId || '';
    this.region = data.region || '';
    this.accountId = data.accountId || '123456789012';
    this.timestamp = data.timestamp || new Date().toISOString();
    
    // Optimization details
    this.optimizationType = data.optimizationType || ''; // 'rightsizing', 'pricing', 'cleanup', 'scheduling'
    this.currentCost = data.currentCost || 0;
    this.projectedCost = data.projectedCost || 0;
    this.estimatedSavings = data.estimatedSavings || 0;
    
    // Confidence and risk assessment
    this.confidenceScore = data.confidenceScore || 0; // 0-100
    this.riskLevel = data.riskLevel || 'MEDIUM'; // 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    
    // Approval workflow
    this.status = data.status || 'pending'; // 'pending', 'approved', 'executed', 'rolled_back', 'rejected'
    this.approvalRequired = data.approvalRequired !== undefined ? data.approvalRequired : true;
    this.approvedBy = data.approvedBy || null;
    this.approvedAt = data.approvedAt || null;
    
    // Implementation details
    this.description = data.description || '';
    this.recommendedAction = data.recommendedAction || '';
    this.currentConfiguration = data.currentConfiguration || {};
    this.recommendedConfiguration = data.recommendedConfiguration || {};
    
    // Execution tracking
    this.executedAt = data.executedAt || null;
    this.executionResult = data.executionResult || null;
    this.rollbackCapable = data.rollbackCapable !== undefined ? data.rollbackCapable : true;
    this.rollbackData = data.rollbackData || null;
    
    // Additional metadata
    this.tags = data.tags || {};
    this.category = data.category || ''; // 'compute', 'storage', 'network', 'database', etc.
    this.priority = data.priority || 'medium'; // 'low', 'medium', 'high', 'urgent'
  }

  /**
   * Generate a unique optimization ID
   * @returns {string} Unique ID
   */
  generateId() {
    return 'opt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Calculate savings percentage
   * @returns {number} Savings percentage
   */
  getSavingsPercentage() {
    if (this.currentCost === 0) return 0;
    return ((this.currentCost - this.projectedCost) / this.currentCost) * 100;
  }

  /**
   * Determine if approval is required based on risk level and savings amount
   * @returns {boolean} Whether approval is required
   */
  requiresApproval() {
    // High-risk optimizations always require approval
    if (this.riskLevel === 'HIGH' || this.riskLevel === 'CRITICAL') {
      return true;
    }
    
    // Large savings amounts require approval regardless of risk
    if (this.estimatedSavings > 1000) {
      return true;
    }
    
    // Low-risk, low-savings optimizations can be auto-approved
    if (this.riskLevel === 'LOW' && this.estimatedSavings <= 100) {
      return false;
    }
    
    // Default to requiring approval
    return true;
  }

  /**
   * Approve the optimization
   * @param {string} approvedBy User who approved
   * @returns {boolean} Success status
   */
  approve(approvedBy) {
    if (this.status !== 'pending') {
      return false;
    }
    
    this.status = 'approved';
    this.approvedBy = approvedBy;
    this.approvedAt = new Date().toISOString();
    return true;
  }

  /**
   * Mark optimization as executed
   * @param {Object} executionResult Result of execution
   * @returns {boolean} Success status
   */
  markExecuted(executionResult = {}) {
    if (this.status !== 'approved') {
      return false;
    }
    
    this.status = 'executed';
    this.executedAt = new Date().toISOString();
    this.executionResult = executionResult;
    return true;
  }

  /**
   * Validate the optimization data
   * @returns {Object} Validation result with isValid boolean and errors array
   */
  validate() {
    const errors = [];
    
    if (!this.resourceId) {
      errors.push('resourceId is required');
    }
    
    if (!this.optimizationType) {
      errors.push('optimizationType is required');
    }
    
    const validOptimizationTypes = ['rightsizing', 'pricing', 'cleanup', 'scheduling'];
    if (this.optimizationType && !validOptimizationTypes.includes(this.optimizationType)) {
      errors.push(`optimizationType must be one of: ${validOptimizationTypes.join(', ')}`);
    }
    
    const validRiskLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    if (!validRiskLevels.includes(this.riskLevel)) {
      errors.push(`riskLevel must be one of: ${validRiskLevels.join(', ')}`);
    }
    
    const validStatuses = ['pending', 'approved', 'executed', 'rolled_back', 'rejected'];
    if (!validStatuses.includes(this.status)) {
      errors.push(`status must be one of: ${validStatuses.join(', ')}`);
    }
    
    if (typeof this.currentCost !== 'number' || this.currentCost < 0) {
      errors.push('currentCost must be a non-negative number');
    }
    
    if (typeof this.projectedCost !== 'number' || this.projectedCost < 0) {
      errors.push('projectedCost must be a non-negative number');
    }
    
    if (typeof this.confidenceScore !== 'number' || this.confidenceScore < 0 || this.confidenceScore > 100) {
      errors.push('confidenceScore must be a number between 0 and 100');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Convert to JSON representation
   * @returns {Object} JSON object
   */
  toJSON() {
    return {
      optimizationId: this.optimizationId,
      resourceId: this.resourceId,
      region: this.region,
      accountId: this.accountId,
      optimizationType: this.optimizationType,
      currentCost: this.currentCost,
      projectedCost: this.projectedCost,
      estimatedSavings: this.estimatedSavings,
      confidenceScore: this.confidenceScore,
      riskLevel: this.riskLevel,
      status: this.status,
      approvalRequired: this.approvalRequired,
      approvedBy: this.approvedBy,
      approvedAt: this.approvedAt,
      description: this.description,
      recommendedAction: this.recommendedAction,
      currentConfiguration: this.currentConfiguration,
      recommendedConfiguration: this.recommendedConfiguration,
      executedAt: this.executedAt,
      executionResult: this.executionResult,
      rollbackCapable: this.rollbackCapable,
      rollbackData: this.rollbackData,
      tags: this.tags,
      category: this.category,
      priority: this.priority,
      timestamp: this.timestamp,
      savingsPercentage: this.getSavingsPercentage()
    };
  }

  /**
   * Create CostOptimization from JSON data
   * @param {Object} json JSON object
   * @returns {CostOptimization} New CostOptimization instance
   */
  static fromJSON(json) {
    return new CostOptimization(json);
  }
}

module.exports = CostOptimization;