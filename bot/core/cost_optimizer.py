#!/usr/bin/env python3
"""
Cost Optimizer Engine for Advanced FinOps Platform

Core optimization orchestration engine that:
- Coordinates optimization across EC2, RDS, Lambda, S3, EBS services
- Applies service-specific optimization rules
- Generates recommendations with appropriate risk levels
- Integrates with existing scanners and provides unified optimization interface

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of cost optimizations."""
    CLEANUP = "cleanup"
    RIGHTSIZING = "rightsizing"
    PRICING = "pricing"
    STORAGE_OPTIMIZATION = "storage_optimization"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    GOVERNANCE = "governance"
    MONITORING = "monitoring"
    PERFORMANCE = "performance"


class RiskLevel(Enum):
    """Risk levels for optimization recommendations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConfidenceLevel(Enum):
    """Confidence levels for optimization recommendations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CostOptimizer:
    """
    Core cost optimization engine that orchestrates optimization across all AWS services.
    
    This engine coordinates with service-specific scanners to generate comprehensive
    optimization recommendations with risk assessment and prioritization.
    """
    
    def __init__(self, aws_config, region: str = 'us-east-1', custom_thresholds: Optional[Dict[str, Any]] = None):
        """
        Initialize cost optimizer engine.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region to optimize
            custom_thresholds: Optional custom thresholds to override defaults
        """
        self.aws_config = aws_config
        self.region = region
        self.optimization_rules = self._initialize_optimization_rules()
        
        # Apply custom thresholds if provided
        if custom_thresholds:
            self._apply_custom_thresholds(custom_thresholds)
        
        logger.info(f"Cost Optimizer Engine initialized for region {region}")
        if custom_thresholds:
            logger.info(f"Applied custom thresholds: {list(custom_thresholds.keys())}")
    
    def analyze_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compatibility wrapper for orchestrator.

        Orchestrator expects:
        - optimizations_found
        - potential_monthly_savings
        - categories
        - recommendations
        """
        result = self.optimize_resources(resources)

        optimizations = result.get("optimizations", [])

        total_savings = round(
            sum(opt.get("estimatedSavings", 0) for opt in optimizations),
            2
        )

        # Group optimizations by category (optimizationType)
        categories = {}
        for opt in optimizations:
            category = opt.get("optimizationType", "unknown")
            categories.setdefault(category, []).append(opt)

        return {
            "optimizations_found": len(optimizations),
            "potential_monthly_savings": total_savings,
            "categories": categories,
            "recommendations": optimizations,
            "summary": result.get("summary", {}),
            "timestamp": result.get("timestamp"),
            "region": result.get("region"),
        }
    
    def _apply_custom_thresholds(self, custom_thresholds: Dict[str, Any]) -> None:
        """
        Apply custom thresholds to override default optimization rules.
        
        Args:
            custom_thresholds: Dictionary of custom threshold values
        """
        for service, service_thresholds in custom_thresholds.items():
            if service in self.optimization_rules:
                for threshold_category, threshold_values in service_thresholds.items():
                    if threshold_category in self.optimization_rules[service]:
                        # Handle both dictionary and scalar threshold values
                        current_value = self.optimization_rules[service][threshold_category]
                        if isinstance(current_value, dict) and isinstance(threshold_values, dict):
                            current_value.update(threshold_values)
                            logger.info(f"Updated {service}.{threshold_category} thresholds: {threshold_values}")
                        elif not isinstance(current_value, dict):
                            # Direct scalar replacement
                            self.optimization_rules[service][threshold_category] = threshold_values
                            logger.info(f"Updated {service}.{threshold_category} threshold: {threshold_values}")
                        else:
                            logger.warning(f"Cannot update {service}.{threshold_category} - type mismatch")
    
    def get_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current optimization rules for inspection or modification.
        
        Returns:
            Dictionary of current optimization rules
        """
        return self.optimization_rules.copy()
    
    def update_optimization_rules(self, service: str, category: str, updates: Dict[str, Any]) -> None:
        """
        Update specific optimization rules at runtime.
        
        Args:
            service: Service name (e.g., 'ec2', 'rds')
            category: Rule category (e.g., 'unused_threshold')
            updates: Dictionary of updates to apply
        """
        if service in self.optimization_rules and category in self.optimization_rules[service]:
            self.optimization_rules[service][category].update(updates)
            logger.info(f"Updated optimization rules for {service}.{category}: {updates}")
        else:
            logger.warning(f"Cannot update rules for {service}.{category} - not found")
    
    def _initialize_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize service-specific optimization rules.
        
        Returns:
            Dictionary of optimization rules by service type
        """
        return {
            'ec2': {
                'unused_threshold': {
                    'cpu_avg': 2.0,
                    'cpu_max': 10.0,
                    'min_data_points': 24
                },
                'underutilized_threshold': {
                    'cpu_avg': 10.0,
                    'cpu_max': 30.0,
                    'min_data_points': 24
                },
                'spot_candidate_threshold': {
                    'cpu_min': 5.0,
                    'cpu_max': 80.0,
                    'stability_required': True
                }
            },
            'rds': {
                'unused_threshold': {
                    'cpu_avg': 5.0,
                    'cpu_max': 20.0,
                    'connections_avg': 1.0,
                    'min_data_points': 24
                },
                'underutilized_threshold': {
                    'cpu_avg': 20.0,
                    'cpu_max': 50.0,
                    'connections_avg': 10.0,
                    'min_data_points': 24
                },
                'storage_overprovisioned_threshold': 70.0  # % free space
            },
            'lambda': {
                'unused_threshold': {
                    'invocations': 0,
                    'min_data_points': 24
                },
                'rarely_used_threshold': {
                    'invocations': 10,
                    'min_data_points': 24
                },
                'memory_optimization_threshold': {
                    'timeout_usage_ratio': 0.5,  # Using less than 50% of timeout
                    'min_memory_size': 512
                },
                'timeout_optimization_threshold': {
                    'timeout_usage_ratio': 0.3  # Using less than 30% of timeout
                }
            },
            's3': {
                'unused_threshold': {
                    'days_since_last_access': 90,
                    'object_count': 0
                },
                'lifecycle_opportunity_threshold': {
                    'days_since_last_access': 30,
                    'storage_class': 'STANDARD'
                },
                'intelligent_tiering_threshold': {
                    'object_count': 1000,
                    'storage_size_gb': 100
                }
            },
            'ebs': {
                'unused_threshold': {
                    'state': 'available',
                    'days_unattached': 7
                },
                'underutilized_threshold': {
                    'iops_utilization': 10.0,  # % of provisioned IOPS used
                    'volume_type': 'io1'
                },
                'snapshot_cleanup_threshold': {
                    'days_old': 30,
                    'no_recent_usage': True
                }
            }
        }
    
    def optimize_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive optimization recommendations for all resources.
        
        Args:
            resources: List of resources from all service scanners
            
        Returns:
            Comprehensive optimization analysis with recommendations
        """
        logger.info(f"Starting optimization analysis for {len(resources)} resources")
        
        # Group resources by service type
        resources_by_service = self._group_resources_by_service(resources)
        
        # Generate service-specific optimizations
        service_optimizations = {}
        total_optimizations = []
        
        for service_type, service_resources in resources_by_service.items():
            logger.info(f"Optimizing {len(service_resources)} {service_type} resources")
            
            if service_type == 'ec2':
                optimizations = self._optimize_ec2_resources(service_resources)
            elif service_type == 'rds':
                optimizations = self._optimize_rds_resources(service_resources)
            elif service_type == 'lambda':
                optimizations = self._optimize_lambda_resources(service_resources)
            elif service_type == 's3':
                optimizations = self._optimize_s3_resources(service_resources)
            elif service_type == 'ebs':
                optimizations = self._optimize_ebs_resources(service_resources)
            else:
                logger.warning(f"No optimization rules defined for service type: {service_type}")
                optimizations = []
            
            service_optimizations[service_type] = optimizations
            total_optimizations.extend(optimizations)
        
        # Prioritize and rank optimizations
        prioritized_optimizations = self._prioritize_optimizations(total_optimizations)
        
        # Generate optimization summary
        summary = self._generate_optimization_summary(
            resources_by_service, 
            service_optimizations, 
            prioritized_optimizations
        )
        
        logger.info(f"Generated {len(total_optimizations)} optimization recommendations")
        
        return {
            'summary': summary,
            'optimizations': prioritized_optimizations,
            'serviceBreakdown': service_optimizations,
            'totalResources': len(resources),
            'totalOptimizations': len(total_optimizations),
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region
        }
    
    def _group_resources_by_service(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group resources by their service type."""
        grouped = {}
        
        for resource in resources:
            service_type = resource.get('resourceType', 'unknown')
            if service_type not in grouped:
                grouped[service_type] = []
            grouped[service_type].append(resource)
        
        return grouped
    
    def _optimize_ec2_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate EC2-specific optimization recommendations.
        
        Requirements: 7.1 (part of multi-service optimization)
        """
        optimizations = []
        rules = self.optimization_rules['ec2']
        
        for resource in resources:
            resource_id = resource.get('resourceId')
            metrics = resource.get('utilizationMetrics', {})
            
            # Skip if insufficient data
            data_points = metrics.get('dataPoints', 0)
            if data_points < rules['unused_threshold']['min_data_points']:
                continue
            
            avg_cpu = metrics.get('avgCpuUtilization', 0)
            max_cpu = metrics.get('maxCpuUtilization', 0)
            current_cost = resource.get('currentCost', 0)
            
            # Unused instance detection
            if (avg_cpu < rules['unused_threshold']['cpu_avg'] and 
                max_cpu < rules['unused_threshold']['cpu_max']):
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='ec2',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Terminate unused EC2 instance",
                    description=f"Instance shows very low utilization: {avg_cpu:.1f}% avg CPU, {max_cpu:.1f}% max CPU",
                    current_cost=current_cost,
                    projected_cost=0.0,
                    estimated_savings=current_cost * 0.95,
                    risk_level=RiskLevel.HIGH,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Terminate instance after verifying no critical workloads",
                    resource_data=resource
                ))
            
            # Underutilized instance right-sizing
            elif (avg_cpu < rules['underutilized_threshold']['cpu_avg'] and 
                  max_cpu < rules['underutilized_threshold']['cpu_max']):
                
                recommended_type = self._recommend_smaller_instance_type(resource.get('instanceType', ''))
                projected_cost = current_cost * 0.7  # Assume 30% savings
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='ec2',
                    optimization_type=OptimizationType.RIGHTSIZING,
                    title="Right-size underutilized EC2 instance",
                    description=f"Instance underutilized: {avg_cpu:.1f}% avg CPU. Recommend {recommended_type}",
                    current_cost=current_cost,
                    projected_cost=projected_cost,
                    estimated_savings=current_cost - projected_cost,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="Medium",
                    recommended_action=f"Resize to {recommended_type} during maintenance window",
                    resource_data=resource,
                    additional_details={
                        'recommendedInstanceType': recommended_type,
                        'currentInstanceType': resource.get('instanceType')
                    }
                ))
            
            # Spot instance opportunity
            elif (avg_cpu >= rules['spot_candidate_threshold']['cpu_min'] and 
                  max_cpu <= rules['spot_candidate_threshold']['cpu_max']):
                
                projected_cost = current_cost * 0.3  # Assume 70% savings with spot
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='ec2',
                    optimization_type=OptimizationType.PRICING,
                    title="Convert to Spot instance",
                    description="Stable workload suitable for Spot instances",
                    current_cost=current_cost,
                    projected_cost=projected_cost,
                    estimated_savings=current_cost - projected_cost,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="High",
                    recommended_action="Evaluate workload fault tolerance and convert to Spot",
                    resource_data=resource
                ))
        
        return optimizations
    
    def _optimize_rds_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate RDS-specific optimization recommendations.
        
        Requirements: 7.1 - RDS optimization (database right-sizing, storage optimization, unused database cleanup)
        """
        optimizations = []
        rules = self.optimization_rules['rds']
        
        for resource in resources:
            resource_id = resource.get('resourceId')
            metrics = resource.get('utilizationMetrics', {})
            
            # Skip if insufficient data
            data_points = metrics.get('dataPoints', 0)
            if data_points < rules['unused_threshold']['min_data_points']:
                continue
            
            avg_cpu = metrics.get('avgCpuUtilization', 0)
            max_cpu = metrics.get('maxCpuUtilization', 0)
            avg_connections = metrics.get('avgConnections', 0)
            current_cost = resource.get('currentCost', 0)
            
            # Unused database detection
            if (avg_cpu < rules['unused_threshold']['cpu_avg'] and 
                max_cpu < rules['unused_threshold']['cpu_max'] and
                avg_connections < rules['unused_threshold']['connections_avg']):
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='rds',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Remove unused RDS database",
                    description=f"Database shows no activity: {avg_cpu:.1f}% avg CPU, {avg_connections:.1f} avg connections",
                    current_cost=current_cost,
                    projected_cost=0.0,
                    estimated_savings=current_cost * 0.95,
                    risk_level=RiskLevel.CRITICAL,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Take final backup and terminate database after stakeholder approval",
                    resource_data=resource
                ))
            
            # Underutilized database right-sizing
            elif (avg_cpu < rules['underutilized_threshold']['cpu_avg'] and 
                  max_cpu < rules['underutilized_threshold']['cpu_max'] and
                  avg_connections < rules['underutilized_threshold']['connections_avg']):
                
                recommended_class = self._recommend_smaller_db_instance_class(resource.get('dbInstanceClass', ''))
                projected_cost = current_cost * 0.6  # Assume 40% savings
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='rds',
                    optimization_type=OptimizationType.RIGHTSIZING,
                    title="Right-size underutilized RDS database",
                    description=f"Database underutilized: {avg_cpu:.1f}% avg CPU, {avg_connections:.1f} avg connections",
                    current_cost=current_cost,
                    projected_cost=projected_cost,
                    estimated_savings=current_cost - projected_cost,
                    risk_level=RiskLevel.HIGH,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="High",
                    recommended_action=f"Resize to {recommended_class} during maintenance window",
                    resource_data=resource,
                    additional_details={
                        'recommendedInstanceClass': recommended_class,
                        'currentInstanceClass': resource.get('dbInstanceClass')
                    }
                ))
            
            # Storage optimization
            free_storage_points = metrics.get('freeStorageSpace', [])
            if free_storage_points:
                allocated_storage_bytes = resource.get('allocatedStorage', 0) * 1024 * 1024 * 1024
                if allocated_storage_bytes > 0:
                    avg_free_storage = sum(dp['average'] for dp in free_storage_points) / len(free_storage_points)
                    free_storage_percentage = (avg_free_storage / allocated_storage_bytes) * 100
                    
                    if free_storage_percentage > rules['storage_overprovisioned_threshold']:
                        storage_savings = current_cost * 0.2  # Assume 20% of cost is storage
                        
                        optimizations.append(self._create_optimization_record(
                            resource_id=resource_id,
                            resource_type='rds',
                            optimization_type=OptimizationType.STORAGE_OPTIMIZATION,
                            title="Optimize RDS storage allocation",
                            description=f"Over-provisioned storage: {free_storage_percentage:.1f}% free space",
                            current_cost=current_cost,
                            projected_cost=current_cost - storage_savings,
                            estimated_savings=storage_savings,
                            risk_level=RiskLevel.MEDIUM,
                            confidence=ConfidenceLevel.MEDIUM,
                            implementation_effort="Medium",
                            recommended_action="Reduce allocated storage during maintenance window",
                            resource_data=resource,
                            additional_details={
                                'freeStoragePercentage': free_storage_percentage,
                                'currentAllocatedStorage': resource.get('allocatedStorage')
                            }
                        ))
            
            # Multi-AZ optimization for non-production
            if resource.get('multiAZ', False):
                tags = resource.get('tags', {})
                environment = tags.get('Environment', '').lower()
                if environment in ['dev', 'test', 'development', 'testing', 'staging']:
                    multi_az_savings = current_cost * 0.5  # Multi-AZ doubles cost
                    
                    optimizations.append(self._create_optimization_record(
                        resource_id=resource_id,
                        resource_type='rds',
                        optimization_type=OptimizationType.CONFIGURATION,
                        title="Disable Multi-AZ for non-production database",
                        description=f"Multi-AZ enabled for {environment} environment",
                        current_cost=current_cost,
                        projected_cost=current_cost - multi_az_savings,
                        estimated_savings=multi_az_savings,
                        risk_level=RiskLevel.MEDIUM,
                        confidence=ConfidenceLevel.HIGH,
                        implementation_effort="Low",
                        recommended_action="Disable Multi-AZ for non-production workloads",
                        resource_data=resource,
                        additional_details={
                            'environment': environment,
                            'currentMultiAZ': True
                        }
                    ))
        
        return optimizations
    
    def _optimize_lambda_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate Lambda-specific optimization recommendations.
        
        Requirements: 7.2 - Lambda optimization (memory allocation, timeout settings, unused functions)
        """
        optimizations = []
        rules = self.optimization_rules['lambda']
        
        for resource in resources:
            resource_id = resource.get('resourceId')
            metrics = resource.get('utilizationMetrics', {})
            
            total_invocations = metrics.get('totalInvocations', 0)
            avg_duration = metrics.get('avgDuration', 0)
            max_duration = metrics.get('maxDuration', 0)
            current_cost = resource.get('currentCost', 0)
            
            memory_size = resource.get('memorySize', 128)
            timeout = resource.get('timeout', 3)
            data_points = metrics.get('dataPoints', 0)
            
            # Skip if insufficient data
            if data_points < rules['unused_threshold']['min_data_points']:
                continue
            
            # Unused function detection
            if total_invocations <= rules['unused_threshold']['invocations']:
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='lambda',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Remove unused Lambda function",
                    description="Function has not been invoked in the monitoring period",
                    current_cost=current_cost,
                    projected_cost=0.0,
                    estimated_savings=current_cost,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Verify function is not needed and delete",
                    resource_data=resource
                ))
            
            # Rarely used function
            elif total_invocations <= rules['rarely_used_threshold']['invocations']:
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='lambda',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Review rarely used Lambda function",
                    description=f"Function rarely used: {total_invocations} invocations in monitoring period",
                    current_cost=current_cost,
                    projected_cost=current_cost * 0.2,
                    estimated_savings=current_cost * 0.8,
                    risk_level=RiskLevel.LOW,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="Low",
                    recommended_action="Review necessity and consider consolidation",
                    resource_data=resource
                ))
            
            # Memory optimization
            elif (avg_duration > 0 and max_duration < (timeout * 1000 * rules['memory_optimization_threshold']['timeout_usage_ratio']) and
                  memory_size >= rules['memory_optimization_threshold']['min_memory_size']):
                
                recommended_memory = max(128, int(memory_size * 0.7))
                memory_savings = current_cost * 0.3  # Assume 30% savings
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='lambda',
                    optimization_type=OptimizationType.RIGHTSIZING,
                    title="Optimize Lambda memory allocation",
                    description=f"Over-provisioned memory: {avg_duration:.0f}ms avg duration vs {timeout}s timeout",
                    current_cost=current_cost,
                    projected_cost=current_cost - memory_savings,
                    estimated_savings=memory_savings,
                    risk_level=RiskLevel.LOW,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="Low",
                    recommended_action=f"Reduce memory allocation to {recommended_memory}MB",
                    resource_data=resource,
                    additional_details={
                        'recommendedMemorySize': recommended_memory,
                        'currentMemorySize': memory_size,
                        'avgDuration': avg_duration,
                        'timeout': timeout
                    }
                ))
            
            # Timeout optimization
            elif (max_duration > 0 and max_duration < (timeout * 1000 * rules['timeout_optimization_threshold']['timeout_usage_ratio'])):
                recommended_timeout = max(3, int((max_duration / 1000) * 1.5))
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='lambda',
                    optimization_type=OptimizationType.CONFIGURATION,
                    title="Optimize Lambda timeout setting",
                    description=f"Over-provisioned timeout: {max_duration:.0f}ms max duration vs {timeout}s timeout",
                    current_cost=current_cost,
                    projected_cost=current_cost,  # No direct cost savings but better resource management
                    estimated_savings=0.0,
                    risk_level=RiskLevel.LOW,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="Low",
                    recommended_action=f"Reduce timeout to {recommended_timeout}s",
                    resource_data=resource,
                    additional_details={
                        'recommendedTimeout': recommended_timeout,
                        'currentTimeout': timeout,
                        'maxDuration': max_duration
                    }
                ))
        
        return optimizations
    
    def _optimize_s3_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate S3-specific optimization recommendations.
        
        Requirements: 7.3 - S3 optimization (storage class transitions, lifecycle policies, unused bucket cleanup)
        """
        optimizations = []
        rules = self.optimization_rules['s3']
        
        for resource in resources:
            resource_id = resource.get('resourceId')
            current_cost = resource.get('currentCost', 0)
            
            # Unused bucket detection
            object_count = resource.get('objectCount', 0)
            days_since_last_access = resource.get('daysSinceLastAccess', 0)
            
            if (object_count <= rules['unused_threshold']['object_count'] or
                days_since_last_access >= rules['unused_threshold']['days_since_last_access']):
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='s3',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Remove unused S3 bucket",
                    description=f"Bucket unused: {object_count} objects, {days_since_last_access} days since last access",
                    current_cost=current_cost,
                    projected_cost=0.0,
                    estimated_savings=current_cost,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Verify bucket is not needed and delete after backup",
                    resource_data=resource
                ))
            
            # Lifecycle policy optimization
            elif (days_since_last_access >= rules['lifecycle_opportunity_threshold']['days_since_last_access'] and
                  resource.get('storageClass') == rules['lifecycle_opportunity_threshold']['storage_class']):
                
                lifecycle_savings = current_cost * 0.4  # Assume 40% savings with IA/Glacier
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='s3',
                    optimization_type=OptimizationType.STORAGE_OPTIMIZATION,
                    title="Implement S3 lifecycle policy",
                    description=f"Objects not accessed for {days_since_last_access} days in STANDARD storage",
                    current_cost=current_cost,
                    projected_cost=current_cost - lifecycle_savings,
                    estimated_savings=lifecycle_savings,
                    risk_level=RiskLevel.LOW,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Configure lifecycle policy to transition to IA/Glacier",
                    resource_data=resource,
                    additional_details={
                        'daysSinceLastAccess': days_since_last_access,
                        'currentStorageClass': resource.get('storageClass'),
                        'recommendedAction': 'transition_to_ia_glacier'
                    }
                ))
            
            # Intelligent Tiering opportunity
            elif (object_count >= rules['intelligent_tiering_threshold']['object_count'] and
                  resource.get('storageSizeGB', 0) >= rules['intelligent_tiering_threshold']['storage_size_gb']):
                
                intelligent_tiering_savings = current_cost * 0.2  # Assume 20% savings
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='s3',
                    optimization_type=OptimizationType.STORAGE_OPTIMIZATION,
                    title="Enable S3 Intelligent Tiering",
                    description=f"Large bucket suitable for Intelligent Tiering: {object_count} objects, {resource.get('storageSizeGB', 0)}GB",
                    current_cost=current_cost,
                    projected_cost=current_cost - intelligent_tiering_savings,
                    estimated_savings=intelligent_tiering_savings,
                    risk_level=RiskLevel.LOW,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="Low",
                    recommended_action="Enable S3 Intelligent Tiering",
                    resource_data=resource,
                    additional_details={
                        'objectCount': object_count,
                        'storageSizeGB': resource.get('storageSizeGB', 0)
                    }
                ))
        
        return optimizations
    
    def _optimize_ebs_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate EBS-specific optimization recommendations.
        
        Requirements: 7.4 - EBS optimization (unused volumes, volume types, snapshot cleanup)
        """
        optimizations = []
        rules = self.optimization_rules['ebs']
        
        for resource in resources:
            resource_id = resource.get('resourceId')
            current_cost = resource.get('currentCost', 0)
            
            # Unused volume detection
            state = resource.get('state', '')
            days_unattached = resource.get('daysUnattached', 0)
            
            if (state == rules['unused_threshold']['state'] and
                days_unattached >= rules['unused_threshold']['days_unattached']):
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='ebs',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Remove unused EBS volume",
                    description=f"Volume unattached for {days_unattached} days",
                    current_cost=current_cost,
                    projected_cost=0.0,
                    estimated_savings=current_cost,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Create snapshot and delete unused volume",
                    resource_data=resource
                ))
            
            # Volume type optimization
            elif (resource.get('volumeType') == 'io1' and
                  resource.get('iopsUtilization', 100) < rules['underutilized_threshold']['iops_utilization']):
                
                type_optimization_savings = current_cost * 0.3  # Assume 30% savings switching to gp2
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='ebs',
                    optimization_type=OptimizationType.STORAGE_OPTIMIZATION,
                    title="Optimize EBS volume type",
                    description=f"Provisioned IOPS volume with low utilization: {resource.get('iopsUtilization', 0):.1f}%",
                    current_cost=current_cost,
                    projected_cost=current_cost - type_optimization_savings,
                    estimated_savings=type_optimization_savings,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.MEDIUM,
                    implementation_effort="Medium",
                    recommended_action="Convert from io1 to gp2 volume type",
                    resource_data=resource,
                    additional_details={
                        'currentVolumeType': resource.get('volumeType'),
                        'recommendedVolumeType': 'gp2',
                        'iopsUtilization': resource.get('iopsUtilization', 0)
                    }
                ))
            
            # Snapshot cleanup
            snapshots = resource.get('snapshots', [])
            old_snapshots = [s for s in snapshots if s.get('daysOld', 0) >= rules['snapshot_cleanup_threshold']['days_old']]
            
            if old_snapshots:
                snapshot_savings = len(old_snapshots) * 0.05 * resource.get('sizeGB', 0) * 0.05  # Rough estimate
                
                optimizations.append(self._create_optimization_record(
                    resource_id=resource_id,
                    resource_type='ebs',
                    optimization_type=OptimizationType.CLEANUP,
                    title="Clean up old EBS snapshots",
                    description=f"{len(old_snapshots)} snapshots older than {rules['snapshot_cleanup_threshold']['days_old']} days",
                    current_cost=current_cost,
                    projected_cost=current_cost - snapshot_savings,
                    estimated_savings=snapshot_savings,
                    risk_level=RiskLevel.LOW,
                    confidence=ConfidenceLevel.HIGH,
                    implementation_effort="Low",
                    recommended_action="Delete old snapshots after verifying they're not needed",
                    resource_data=resource,
                    additional_details={
                        'oldSnapshotCount': len(old_snapshots),
                        'snapshotAgeThreshold': rules['snapshot_cleanup_threshold']['days_old']
                    }
                ))
        
        return optimizations
    
    def _create_optimization_record(self, 
                                   resource_id: str,
                                   resource_type: str,
                                   optimization_type: OptimizationType,
                                   title: str,
                                   description: str,
                                   current_cost: float,
                                   projected_cost: float,
                                   estimated_savings: float,
                                   risk_level: RiskLevel,
                                   confidence: ConfidenceLevel,
                                   implementation_effort: str,
                                   recommended_action: str,
                                   resource_data: Dict[str, Any],
                                   additional_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a standardized optimization record with implementation timeline estimates."""
        
        # Calculate implementation timeline based on effort and risk level
        implementation_timeline = self._calculate_implementation_timeline(
            implementation_effort, risk_level, optimization_type
        )
        
        # Enhanced cost-benefit analysis
        cost_benefit_analysis = self._calculate_cost_benefit_analysis(
            current_cost, projected_cost, estimated_savings, implementation_timeline
        )
        
        # Map ConfidenceLevel enum or string to a numeric score between 0 and 100
        confidence_map = {
            'LOW': 30,
            'MEDIUM': 60,
            'HIGH': 90,
            ConfidenceLevel.LOW: 30,
            ConfidenceLevel.MEDIUM: 60,
            ConfidenceLevel.HIGH: 90
        }
        confidence_val = confidence_map.get(confidence, 80)

        return {
            'optimizationId': f"{resource_type}-{resource_id}-{optimization_type.value}-{int(datetime.utcnow().timestamp())}",
            'resourceId': resource_id,
            'resourceType': resource_type,
            'optimizationType': optimization_type.value,
            'title': title,
            'description': description,
            'currentCost': current_cost,
            'projectedCost': projected_cost,
            'estimatedSavings': estimated_savings,
            'savingsPercentage': (estimated_savings / current_cost * 100) if current_cost > 0 else 0,
            'riskLevel': risk_level.value,
            'confidenceScore': confidence_val,
            'implementationEffort': implementation_effort,
            'implementationTimeline': implementation_timeline,
            'costBenefitAnalysis': cost_benefit_analysis,
            'recommendedAction': recommended_action,
            'status': 'pending',
            'approvalRequired': risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            'region': self.region,
            'timestamp': datetime.utcnow().isoformat(),
            'resourceData': resource_data,
            'additionalDetails': additional_details or {}
        }
    
    def _prioritize_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize optimizations based on savings potential, risk, and confidence.
        
        Args:
            optimizations: List of optimization recommendations
            
        Returns:
            Sorted list of optimizations by priority
        """
        def priority_score(opt):
            # Calculate priority score based on multiple factors
            savings = opt.get('estimatedSavings', 0)
            risk_multiplier = {
                'LOW': 1.0,
                'MEDIUM': 0.8,
                'HIGH': 0.6,
                'CRITICAL': 0.4
            }.get(opt.get('riskLevel', 'MEDIUM'), 0.8)
            
            conf_val = opt.get('confidenceScore', 'MEDIUM')
            if isinstance(conf_val, (int, float)):
                if conf_val >= 80:
                    conf_key = 'HIGH'
                elif conf_val >= 50:
                    conf_key = 'MEDIUM'
                else:
                    conf_key = 'LOW'
            else:
                conf_key = str(conf_val)

            confidence_multiplier = {
                'HIGH': 1.0,
                'MEDIUM': 0.8,
                'LOW': 0.6
            }.get(conf_key, 0.8)
            
            effort_multiplier = {
                'Low': 1.0,
                'Medium': 0.8,
                'High': 0.6
            }.get(opt.get('implementationEffort', 'Medium'), 0.8)
            
            return savings * risk_multiplier * confidence_multiplier * effort_multiplier
        
        # Sort by priority score (highest first)
        return sorted(optimizations, key=priority_score, reverse=True)
    
    def _generate_optimization_summary(self, 
                                     resources_by_service: Dict[str, List[Dict[str, Any]]],
                                     service_optimizations: Dict[str, List[Dict[str, Any]]],
                                     prioritized_optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive optimization summary with enhanced analytics."""
        
        total_current_cost = sum(
            sum(resource.get('currentCost', 0) for resource in resources)
            for resources in resources_by_service.values()
        )
        
        total_estimated_savings = sum(opt.get('estimatedSavings', 0) for opt in prioritized_optimizations)
        total_implementation_cost = sum(
            opt.get('costBenefitAnalysis', {}).get('implementationCost', 0) 
            for opt in prioritized_optimizations
        )
        
        # Calculate aggregate timeline metrics
        avg_payback_months = 0
        total_annual_savings = 0
        total_npv = 0
        
        if prioritized_optimizations:
            payback_periods = [
                opt.get('costBenefitAnalysis', {}).get('paybackPeriodMonths', 0)
                for opt in prioritized_optimizations
                if opt.get('costBenefitAnalysis', {}).get('paybackPeriodMonths', 0) != float('inf')
            ]
            avg_payback_months = sum(payback_periods) / len(payback_periods) if payback_periods else 0
            
            total_annual_savings = sum(
                opt.get('costBenefitAnalysis', {}).get('annualSavings', 0)
                for opt in prioritized_optimizations
            )
            
            total_npv = sum(
                opt.get('costBenefitAnalysis', {}).get('npv', 0)
                for opt in prioritized_optimizations
            )
        
        # Group by optimization type
        optimization_type_breakdown = {}
        for opt in prioritized_optimizations:
            opt_type = opt.get('optimizationType', 'unknown')
            if opt_type not in optimization_type_breakdown:
                optimization_type_breakdown[opt_type] = {
                    'count': 0,
                    'totalSavings': 0.0,
                    'avgImplementationDays': 0.0,
                    'totalImplementationCost': 0.0
                }
            optimization_type_breakdown[opt_type]['count'] += 1
            optimization_type_breakdown[opt_type]['totalSavings'] += opt.get('estimatedSavings', 0)
            optimization_type_breakdown[opt_type]['totalImplementationCost'] += opt.get('costBenefitAnalysis', {}).get('implementationCost', 0)
            
            # Calculate average implementation days
            timeline = opt.get('implementationTimeline', {})
            if timeline.get('totalDays', 0) > 0:
                current_avg = optimization_type_breakdown[opt_type]['avgImplementationDays']
                current_count = optimization_type_breakdown[opt_type]['count']
                new_avg = ((current_avg * (current_count - 1)) + timeline['totalDays']) / current_count
                optimization_type_breakdown[opt_type]['avgImplementationDays'] = round(new_avg, 1)
        
        # Group by risk level
        risk_level_breakdown = {}
        for opt in prioritized_optimizations:
            risk_level = opt.get('riskLevel', 'MEDIUM')
            if risk_level not in risk_level_breakdown:
                risk_level_breakdown[risk_level] = {
                    'count': 0,
                    'totalSavings': 0.0,
                    'avgPaybackMonths': 0.0
                }
            risk_level_breakdown[risk_level]['count'] += 1
            risk_level_breakdown[risk_level]['totalSavings'] += opt.get('estimatedSavings', 0)
            
            # Calculate average payback period for this risk level
            payback = opt.get('costBenefitAnalysis', {}).get('paybackPeriodMonths', 0)
            if payback != float('inf'):
                current_avg = risk_level_breakdown[risk_level]['avgPaybackMonths']
                current_count = risk_level_breakdown[risk_level]['count']
                new_avg = ((current_avg * (current_count - 1)) + payback) / current_count
                risk_level_breakdown[risk_level]['avgPaybackMonths'] = round(new_avg, 1)
        
        # Service breakdown with enhanced metrics
        service_breakdown = {}
        for service, optimizations in service_optimizations.items():
            service_resources = resources_by_service.get(service, [])
            service_current_cost = sum(resource.get('currentCost', 0) for resource in service_resources)
            service_savings = sum(opt.get('estimatedSavings', 0) for opt in optimizations)
            service_implementation_cost = sum(
                opt.get('costBenefitAnalysis', {}).get('implementationCost', 0) 
                for opt in optimizations
            )
            
            service_breakdown[service] = {
                'resourceCount': len(service_resources),
                'optimizationCount': len(optimizations),
                'currentCost': service_current_cost,
                'totalSavings': service_savings,
                'savingsPercentage': (service_savings / service_current_cost * 100) if service_current_cost > 0 else 0,
                'implementationCost': service_implementation_cost,
                'netBenefit': service_savings * 12 - service_implementation_cost,  # Annual net benefit
                'avgSavingsPerResource': (service_savings / len(service_resources)) if service_resources else 0,
                'roi': ((service_savings * 12 - service_implementation_cost) / service_implementation_cost * 100) if service_implementation_cost > 0 else 0
            }
        
        # Implementation timeline summary
        timeline_summary = self._calculate_aggregate_timeline(prioritized_optimizations)
        
        # Quick wins analysis (low risk, low effort, high savings)
        quick_wins = [
            opt for opt in prioritized_optimizations 
            if (opt.get('riskLevel') == 'LOW' and 
                opt.get('implementationEffort') == 'Low' and
                opt.get('estimatedSavings', 0) > 0)
        ][:5]
        
        # High-impact opportunities (high savings regardless of effort)
        high_impact = sorted(
            [opt for opt in prioritized_optimizations if opt.get('estimatedSavings', 0) > total_estimated_savings * 0.1],
            key=lambda x: x.get('estimatedSavings', 0),
            reverse=True
        )[:5]
        
        return {
            'totalCurrentCost': total_current_cost,
            'totalEstimatedSavings': total_estimated_savings,
            'totalAnnualSavings': total_annual_savings,
            'totalImplementationCost': total_implementation_cost,
            'netAnnualBenefit': total_annual_savings - total_implementation_cost,
            'aggregateROI': ((total_annual_savings - total_implementation_cost) / total_implementation_cost * 100) if total_implementation_cost > 0 else 0,
            'aggregatePaybackMonths': round(avg_payback_months, 1),
            'totalNPV': round(total_npv, 2),
            'savingsPercentage': (total_estimated_savings / total_current_cost * 100) if total_current_cost > 0 else 0,
            'totalOptimizations': len(prioritized_optimizations),
            'optimizationTypeBreakdown': optimization_type_breakdown,
            'riskLevelBreakdown': risk_level_breakdown,
            'serviceBreakdown': service_breakdown,
            'timelineAnalysis': timeline_summary,
            'topOpportunities': prioritized_optimizations[:10],
            'quickWins': quick_wins,
            'highImpactOpportunities': high_impact,
            'implementationRecommendations': self._generate_implementation_recommendations(
                prioritized_optimizations, quick_wins, high_impact
            )
        }
    
    def _calculate_aggregate_timeline(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate implementation timeline across all optimizations."""
        if not optimizations:
            return {}
        
        # Parallel vs sequential implementation analysis
        total_sequential_days = sum(
            opt.get('implementationTimeline', {}).get('totalDays', 0)
            for opt in optimizations
        )
        
        # Assume some optimizations can be done in parallel
        # Group by service type for parallel execution
        service_groups = {}
        for opt in optimizations:
            service = opt.get('resourceType', 'unknown')
            if service not in service_groups:
                service_groups[service] = []
            service_groups[service].append(opt.get('implementationTimeline', {}).get('totalDays', 0))
        
        # Calculate parallel timeline (max days per service group)
        parallel_days = sum(max(days_list) if days_list else 0 for days_list in service_groups.values())
        
        # Risk-based phasing recommendations
        low_risk_opts = [opt for opt in optimizations if opt.get('riskLevel') == 'LOW']
        medium_risk_opts = [opt for opt in optimizations if opt.get('riskLevel') == 'MEDIUM']
        high_risk_opts = [opt for opt in optimizations if opt.get('riskLevel') in ['HIGH', 'CRITICAL']]
        
        return {
            'totalSequentialDays': total_sequential_days,
            'totalSequentialWeeks': round(total_sequential_days / 7, 1),
            'estimatedParallelDays': parallel_days,
            'estimatedParallelWeeks': round(parallel_days / 7, 1),
            'timelineSavings': round((total_sequential_days - parallel_days) / 7, 1),
            'phasedApproach': {
                'phase1_low_risk': {
                    'count': len(low_risk_opts),
                    'estimatedWeeks': round(sum(opt.get('implementationTimeline', {}).get('totalDays', 0) for opt in low_risk_opts) / 7, 1)
                },
                'phase2_medium_risk': {
                    'count': len(medium_risk_opts),
                    'estimatedWeeks': round(sum(opt.get('implementationTimeline', {}).get('totalDays', 0) for opt in medium_risk_opts) / 7, 1)
                },
                'phase3_high_risk': {
                    'count': len(high_risk_opts),
                    'estimatedWeeks': round(sum(opt.get('implementationTimeline', {}).get('totalDays', 0) for opt in high_risk_opts) / 7, 1)
                }
            }
        }
    
    def _generate_implementation_recommendations(self, 
                                               all_optimizations: List[Dict[str, Any]],
                                               quick_wins: List[Dict[str, Any]],
                                               high_impact: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate strategic implementation recommendations."""
        
        total_savings = sum(opt.get('estimatedSavings', 0) for opt in all_optimizations)
        quick_wins_savings = sum(opt.get('estimatedSavings', 0) for opt in quick_wins)
        
        recommendations = {
            'immediate_actions': [],
            'short_term_goals': [],
            'long_term_strategy': [],
            'resource_requirements': {},
            'success_metrics': {}
        }
        
        # Immediate actions (next 30 days)
        if quick_wins:
            recommendations['immediate_actions'].append(
                f"Implement {len(quick_wins)} quick wins for ${quick_wins_savings:.2f}/month savings"
            )
        
        cleanup_opts = [opt for opt in all_optimizations if opt.get('optimizationType') == 'cleanup']
        if cleanup_opts:
            cleanup_savings = sum(opt.get('estimatedSavings', 0) for opt in cleanup_opts)
            recommendations['immediate_actions'].append(
                f"Execute {len(cleanup_opts)} cleanup optimizations for ${cleanup_savings:.2f}/month savings"
            )
        
        # Short-term goals (next 90 days)
        medium_risk_opts = [opt for opt in all_optimizations if opt.get('riskLevel') == 'MEDIUM']
        if medium_risk_opts:
            medium_savings = sum(opt.get('estimatedSavings', 0) for opt in medium_risk_opts)
            recommendations['short_term_goals'].append(
                f"Complete {len(medium_risk_opts)} medium-risk optimizations for ${medium_savings:.2f}/month savings"
            )
        
        # Long-term strategy (next 6-12 months)
        high_risk_opts = [opt for opt in all_optimizations if opt.get('riskLevel') in ['HIGH', 'CRITICAL']]
        if high_risk_opts:
            high_risk_savings = sum(opt.get('estimatedSavings', 0) for opt in high_risk_opts)
            recommendations['long_term_strategy'].append(
                f"Plan and execute {len(high_risk_opts)} high-risk optimizations for ${high_risk_savings:.2f}/month savings"
            )
        
        # Resource requirements
        total_implementation_days = sum(
            opt.get('implementationTimeline', {}).get('totalDays', 0)
            for opt in all_optimizations
        )
        
        recommendations['resource_requirements'] = {
            'estimated_effort_days': total_implementation_days,
            'estimated_effort_weeks': round(total_implementation_days / 7, 1),
            'recommended_team_size': max(1, min(5, len(all_optimizations) // 10)),
            'budget_required': sum(
                opt.get('costBenefitAnalysis', {}).get('implementationCost', 0)
                for opt in all_optimizations
            )
        }
        
        # Success metrics
        recommendations['success_metrics'] = {
            'target_monthly_savings': total_savings,
            'target_annual_savings': total_savings * 12,
            'target_cost_reduction_percentage': (total_savings / max(
                sum(resource.get('currentCost', 0) for resource in all_optimizations),
                0.01  # avoid divide-by-zero when all resources have $0 cost
            ) * 100) if all_optimizations else 0,

            'kpis': [
                'Monthly cost reduction achieved',
                'Number of optimizations implemented',
                'Average implementation time vs. estimate',
                'ROI achieved vs. projected',
                'System performance impact (should be neutral or positive)'
            ]
        }
        
        return recommendations
    
    def _recommend_smaller_instance_type(self, current_type: str) -> str:
        """Recommend a smaller EC2 instance type."""
        downsize_map = {
            't3.large': 't3.medium',
            't3.medium': 't3.small',
            't3.small': 't3.micro',
            't3.xlarge': 't3.large',
            't3.2xlarge': 't3.xlarge',
            'm5.large': 'm5.medium',
            'm5.xlarge': 'm5.large',
            'm5.2xlarge': 'm5.xlarge',
            'm5.4xlarge': 'm5.2xlarge',
            'c5.large': 'c5.medium',
            'c5.xlarge': 'c5.large',
            'c5.2xlarge': 'c5.xlarge',
            'c5.4xlarge': 'c5.2xlarge',
            'r5.large': 'r5.medium',
            'r5.xlarge': 'r5.large',
            'r5.2xlarge': 'r5.xlarge',
            'r5.4xlarge': 'r5.2xlarge',
        }
        return downsize_map.get(current_type, current_type)
    
    def _recommend_smaller_db_instance_class(self, current_class: str) -> str:
        """Recommend a smaller RDS instance class."""
        downsize_map = {
            'db.t3.large': 'db.t3.medium',
            'db.t3.medium': 'db.t3.small',
            'db.t3.small': 'db.t3.micro',
            'db.t3.xlarge': 'db.t3.large',
            'db.t3.2xlarge': 'db.t3.xlarge',
            'db.m5.large': 'db.m5.medium',
            'db.m5.xlarge': 'db.m5.large',
            'db.m5.2xlarge': 'db.m5.xlarge',
            'db.m5.4xlarge': 'db.m5.2xlarge',
            'db.r5.large': 'db.r5.medium',
            'db.r5.xlarge': 'db.r5.large',
            'db.r5.2xlarge': 'db.r5.xlarge',
            'db.r5.4xlarge': 'db.r5.2xlarge',
        }
        return downsize_map.get(current_class, current_class)
    
    def _calculate_implementation_timeline(self, 
                                         implementation_effort: str, 
                                         risk_level: RiskLevel, 
                                         optimization_type: OptimizationType) -> Dict[str, Any]:
        """
        Calculate implementation timeline estimates based on effort, risk, and optimization type.
        
        Args:
            implementation_effort: Low, Medium, or High
            risk_level: Risk level of the optimization
            optimization_type: Type of optimization being performed
            
        Returns:
            Dictionary with timeline estimates and phases
        """
        # Base timeline estimates in days
        base_timelines = {
            'Low': {'planning': 1, 'testing': 1, 'implementation': 1, 'validation': 1},
            'Medium': {'planning': 2, 'testing': 3, 'implementation': 2, 'validation': 2},
            'High': {'planning': 5, 'testing': 7, 'implementation': 5, 'validation': 3}
        }
        
        # Risk level multipliers
        risk_multipliers = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 1.2,
            RiskLevel.HIGH: 1.5,
            RiskLevel.CRITICAL: 2.0
        }
        
        # Optimization type adjustments
        type_adjustments = {
            OptimizationType.CLEANUP: 0.8,  # Cleanup is usually faster
            OptimizationType.RIGHTSIZING: 1.2,  # Rightsizing needs more testing
            OptimizationType.PRICING: 1.0,  # Standard timeline
            OptimizationType.STORAGE_OPTIMIZATION: 0.9,  # Usually straightforward
            OptimizationType.CONFIGURATION: 0.7,  # Configuration changes are quick
            OptimizationType.SECURITY: 1.3,  # Security changes need extra validation
            OptimizationType.GOVERNANCE: 1.1,  # Governance changes need approval
            OptimizationType.MONITORING: 0.6,  # Monitoring changes are low risk
            OptimizationType.PERFORMANCE: 1.4  # Performance changes need thorough testing
        }
        
        base_timeline = base_timelines.get(implementation_effort, base_timelines['Medium'])
        risk_multiplier = risk_multipliers.get(risk_level, 1.2)
        type_adjustment = type_adjustments.get(optimization_type, 1.0)
        
        # Calculate adjusted timeline
        adjusted_timeline = {}
        total_days = 0
        
        for phase, days in base_timeline.items():
            adjusted_days = max(1, int(days * risk_multiplier * type_adjustment))
            adjusted_timeline[phase] = adjusted_days
            total_days += adjusted_days
        
        # Add buffer for high-risk optimizations
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            buffer_days = max(1, int(total_days * 0.2))
            adjusted_timeline['buffer'] = buffer_days
            total_days += buffer_days
        
        return {
            'totalDays': total_days,
            'totalWeeks': round(total_days / 7, 1),
            'phases': adjusted_timeline,
            'criticalPath': self._identify_critical_path(adjusted_timeline, risk_level),
            'prerequisites': self._identify_prerequisites(optimization_type, risk_level),
            'rollbackTime': self._calculate_rollback_time(optimization_type, implementation_effort)
        }
    
    def _calculate_cost_benefit_analysis(self, 
                                       current_cost: float, 
                                       projected_cost: float, 
                                       estimated_savings: float,
                                       implementation_timeline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive cost-benefit analysis including ROI and payback period.
        
        Args:
            current_cost: Current monthly cost
            projected_cost: Projected monthly cost after optimization
            estimated_savings: Estimated monthly savings
            implementation_timeline: Implementation timeline details
            
        Returns:
            Dictionary with cost-benefit analysis metrics
        """
        # Estimate implementation costs (rough estimates based on timeline)
        daily_implementation_cost = 500  # Assume $500/day for implementation effort
        total_implementation_cost = implementation_timeline['totalDays'] * daily_implementation_cost
        
        # Calculate payback period
        if estimated_savings > 0:
            payback_months = total_implementation_cost / estimated_savings
        else:
            payback_months = float('inf')
        
        # Calculate ROI metrics
        annual_savings = estimated_savings * 12
        roi_percentage = ((annual_savings - total_implementation_cost) / total_implementation_cost * 100) if total_implementation_cost > 0 else 0
        
        # Calculate NPV (assuming 10% discount rate)
        discount_rate = 0.10
        npv_years = 3  # Calculate NPV over 3 years
        npv = -total_implementation_cost
        
        for year in range(1, npv_years + 1):
            npv += annual_savings / ((1 + discount_rate) ** year)
        
        # Risk-adjusted savings (account for implementation risk)
        risk_adjustment_factors = {
            'LOW': 0.95,
            'MEDIUM': 0.85,
            'HIGH': 0.75,
            'CRITICAL': 0.65
        }
        
        # Confidence-adjusted savings
        confidence_adjustment_factors = {
            'HIGH': 0.95,
            'MEDIUM': 0.80,
            'LOW': 0.65
        }
        
        return {
            'monthlySavings': estimated_savings,
            'annualSavings': annual_savings,
            'implementationCost': total_implementation_cost,
            'paybackPeriodMonths': round(payback_months, 1),
            'roiPercentage': round(roi_percentage, 1),
            'npv': round(npv, 2),
            'costReductionPercentage': round((estimated_savings / current_cost * 100), 1) if current_cost > 0 else 0,
            'breakEvenPoint': {
                'months': round(payback_months, 1),
                'description': f"Break-even after {round(payback_months, 1)} months"
            },
            'riskAdjustedSavings': {
                'monthly': round(estimated_savings * risk_adjustment_factors.get('MEDIUM', 0.85), 2),
                'annual': round(annual_savings * risk_adjustment_factors.get('MEDIUM', 0.85), 2)
            },
            'confidenceLevel': 'MEDIUM',  # Default confidence level
            'businessCase': self._generate_business_case(
                estimated_savings, total_implementation_cost, payback_months, roi_percentage
            )
        }
    
    def _identify_critical_path(self, timeline_phases: Dict[str, int], risk_level: RiskLevel) -> List[str]:
        """Identify the critical path phases for implementation."""
        critical_phases = ['planning', 'implementation', 'validation']
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            critical_phases.extend(['testing', 'approval'])
        
        return critical_phases
    
    def _identify_prerequisites(self, optimization_type: OptimizationType, risk_level: RiskLevel) -> List[str]:
        """Identify prerequisites for different optimization types."""
        prerequisites = []
        
        # Common prerequisites
        prerequisites.append("Stakeholder notification")
        prerequisites.append("Change management approval")
        
        # Type-specific prerequisites
        if optimization_type == OptimizationType.CLEANUP:
            prerequisites.extend([
                "Data backup verification",
                "Dependency analysis",
                "Final usage confirmation"
            ])
        elif optimization_type == OptimizationType.RIGHTSIZING:
            prerequisites.extend([
                "Performance baseline establishment",
                "Load testing in staging",
                "Rollback plan preparation"
            ])
        elif optimization_type == OptimizationType.PRICING:
            prerequisites.extend([
                "Workload stability analysis",
                "Spot instance interruption handling",
                "Reserved instance commitment analysis"
            ])
        elif optimization_type == OptimizationType.STORAGE_OPTIMIZATION:
            prerequisites.extend([
                "Data access pattern analysis",
                "Compliance requirement review",
                "Backup strategy validation"
            ])
        
        # Risk-specific prerequisites
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            prerequisites.extend([
                "Executive approval",
                "Detailed rollback testing",
                "24/7 monitoring setup",
                "Emergency contact list preparation"
            ])
        
        return prerequisites
    
    def _calculate_rollback_time(self, optimization_type: OptimizationType, implementation_effort: str) -> Dict[str, Any]:
        """Calculate estimated rollback time for different optimization types."""
        base_rollback_times = {
            'Low': 30,  # 30 minutes
            'Medium': 120,  # 2 hours
            'High': 480  # 8 hours
        }
        
        type_multipliers = {
            OptimizationType.CLEANUP: 0.5,  # Hard to rollback deletions
            OptimizationType.RIGHTSIZING: 1.0,  # Standard rollback
            OptimizationType.PRICING: 0.8,  # Pricing changes are quick to revert
            OptimizationType.STORAGE_OPTIMIZATION: 1.2,  # Storage changes take time
            OptimizationType.CONFIGURATION: 0.6,  # Config changes are quick
            OptimizationType.SECURITY: 1.5,  # Security changes need careful rollback
            OptimizationType.GOVERNANCE: 1.1,  # Governance changes need approval
            OptimizationType.MONITORING: 0.3,  # Monitoring changes are very quick
            OptimizationType.PERFORMANCE: 1.3  # Performance changes need validation
        }
        
        base_time = base_rollback_times.get(implementation_effort, 120)
        multiplier = type_multipliers.get(optimization_type, 1.0)
        rollback_minutes = int(base_time * multiplier)
        
        return {
            'estimatedMinutes': rollback_minutes,
            'estimatedHours': round(rollback_minutes / 60, 1),
            'complexity': 'Low' if rollback_minutes < 60 else 'Medium' if rollback_minutes < 240 else 'High',
            'automatable': optimization_type in [
                OptimizationType.CONFIGURATION, 
                OptimizationType.MONITORING, 
                OptimizationType.PRICING
            ]
        }
    
    def _generate_business_case(self, 
                              monthly_savings: float, 
                              implementation_cost: float, 
                              payback_months: float, 
                              roi_percentage: float) -> str:
        """Generate a business case summary for the optimization."""
        if payback_months < 3:
            urgency = "High Priority"
            recommendation = "Implement immediately"
        elif payback_months < 6:
            urgency = "Medium Priority"
            recommendation = "Implement within next quarter"
        elif payback_months < 12:
            urgency = "Low Priority"
            recommendation = "Consider for next budget cycle"
        else:
            urgency = "Review Required"
            recommendation = "Evaluate if benefits justify implementation"
        
        return f"{urgency}: ${monthly_savings:.2f}/month savings with {payback_months:.1f} month payback. {recommendation}."