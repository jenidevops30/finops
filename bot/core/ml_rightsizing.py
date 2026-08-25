#!/usr/bin/env python3
"""
ML Right-Sizing Engine for Advanced FinOps Platform

Machine learning-powered resource sizing recommendations that:
- Collect historical CPU, memory, network, and storage metrics
- Use ML algorithms for pattern recognition and trend analysis
- Generate size recommendations with confidence intervals
- Estimate cost savings and performance impact
- Provide rollback capabilities and validation

Requirements: 3.1, 3.2, 3.3
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json
import statistics
import pickle
import os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MLModelType(Enum):
    """Types of ML models used for right-sizing."""
    LINEAR_REGRESSION = "linear_regression"
    POLYNOMIAL_REGRESSION = "polynomial_regression"
    MOVING_AVERAGE = "moving_average"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    CLUSTERING = "clustering"


class ResourceType(Enum):
    """Types of resources that can be right-sized."""
    EC2_INSTANCE = "ec2"
    RDS_INSTANCE = "rds"
    LAMBDA_FUNCTION = "lambda"
    EBS_VOLUME = "ebs"


class ConfidenceLevel(Enum):
    """Confidence levels for ML recommendations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(Enum):
    """Risk levels for right-sizing recommendations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MLRightSizingEngine:
    """
    Machine learning-powered right-sizing engine that analyzes historical usage
    patterns and generates intelligent resource sizing recommendations.
    
    This engine implements multiple ML algorithms to predict optimal resource
    configurations based on actual usage patterns rather than guesswork.
    """
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize ML right-sizing engine.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region for analysis
        """
        self.aws_config = aws_config
        self.region = region
        self.ml_thresholds = self._initialize_ml_thresholds()
        self.trained_models = {}
        self.model_metrics = {}
        self.model_cache_dir = 'ml_models'
        self.historical_data_cache = {}
        self.trend_detection_cache = {}
        
        # Create model cache directory
        if not os.path.exists(self.model_cache_dir):
            os.makedirs(self.model_cache_dir)
        
        # Load existing trained models
        self._load_trained_models()
        
        logger.info(f"ML Right-Sizing Engine initialized for region {region}")
        logger.info(f"Loaded {len(self.trained_models)} pre-trained models")
    
    def _initialize_ml_thresholds(self) -> Dict[str, Any]:
        """
        Initialize ML analysis thresholds and parameters.
        
        Returns:
            Dictionary of ML thresholds and parameters
        """
        return {
            'data_requirements': {
                'min_data_points': 168,  # 1 week of hourly data minimum
                'optimal_data_points': 720,  # 1 month of hourly data
                'max_data_age_days': 90,  # Maximum age of data to consider
                'min_variance_threshold': 0.1  # Minimum variance to consider patterns
            },
            'confidence_scoring': {
                'high_confidence_threshold': 85.0,
                'medium_confidence_threshold': 70.0,
                'data_quality_weight': 0.4,
                'pattern_consistency_weight': 0.3,
                'prediction_accuracy_weight': 0.3
            },
            'sizing_parameters': {
                'safety_buffer_percentage': 20.0,  # Safety buffer for recommendations
                'peak_utilization_percentile': 95,  # Percentile for peak analysis
                'avg_utilization_weight': 0.6,
                'peak_utilization_weight': 0.4,
                'cost_optimization_threshold': 15.0  # Minimum % savings to recommend
            },
            'performance_impact': {
                'cpu_headroom_percentage': 15.0,
                'memory_headroom_percentage': 10.0,
                'network_headroom_percentage': 25.0,
                'storage_headroom_percentage': 20.0
            }
        }
    
    def analyze_rightsizing_opportunities(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze right-sizing opportunities using ML algorithms.
        
        Args:
            resources: List of resources with historical utilization data
            
        Returns:
            Comprehensive ML-powered right-sizing analysis
            
        Requirements: 3.1, 3.2, 3.3
        """
        logger.info(f"Starting ML right-sizing analysis for {len(resources)} resources")
        
        # Group resources by type for specialized analysis
        resources_by_type = self._group_resources_by_type(resources)
        
        # Generate ML-powered recommendations for each resource type
        all_recommendations = []
        analysis_summary = {
            'totalResources': len(resources),
            'analyzedResources': 0,
            'recommendationsGenerated': 0,
            'totalPotentialSavings': 0.0,
            'highConfidenceRecommendations': 0,
            'mediumConfidenceRecommendations': 0,
            'lowConfidenceRecommendations': 0
        }
        
        for resource_type, type_resources in resources_by_type.items():
            logger.info(f"Analyzing {len(type_resources)} {resource_type} resources with ML")
            
            type_recommendations = self._analyze_resource_type_ml(resource_type, type_resources)
            all_recommendations.extend(type_recommendations)
            
            # Update summary statistics
            analysis_summary['analyzedResources'] += len(type_resources)
            analysis_summary['recommendationsGenerated'] += len(type_recommendations)
            
            for rec in type_recommendations:
                analysis_summary['totalPotentialSavings'] += rec.get('estimatedMonthlySavings', 0)
                confidence = rec.get('confidenceLevel', 'LOW')
                if confidence == 'HIGH':
                    analysis_summary['highConfidenceRecommendations'] += 1
                elif confidence == 'MEDIUM':
                    analysis_summary['mediumConfidenceRecommendations'] += 1
                else:
                    analysis_summary['lowConfidenceRecommendations'] += 1
        
        # Prioritize recommendations by confidence and savings potential
        prioritized_recommendations = self._prioritize_ml_recommendations(all_recommendations)
        
        logger.info(f"Generated {len(all_recommendations)} ML-powered right-sizing recommendations")
        
        return {
            'summary': analysis_summary,
            'recommendations': prioritized_recommendations,
            'mlModelsUsed': list(self.trained_models.keys()),
            'analysisTimestamp': datetime.utcnow().isoformat(),
            'region': self.region,
            'confidenceDistribution': {
                'high': analysis_summary['highConfidenceRecommendations'],
                'medium': analysis_summary['mediumConfidenceRecommendations'],
                'low': analysis_summary['lowConfidenceRecommendations']
            }
        }
    
    def _group_resources_by_type(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group resources by their type for specialized ML analysis."""
        grouped = {}
        
        for resource in resources:
            resource_type = resource.get('resourceType', 'unknown')
            if resource_type not in grouped:
                grouped[resource_type] = []
            grouped[resource_type].append(resource)
        
        return grouped
    
    def _analyze_resource_type_ml(self, resource_type: str, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply ML analysis to specific resource type.
        
        Args:
            resource_type: Type of resource (ec2, rds, lambda, ebs)
            resources: List of resources of this type
            
        Returns:
            List of ML-powered right-sizing recommendations
        """
        recommendations = []
        
        for resource in resources:
            # Collect and validate historical metrics
            historical_metrics = self._collect_historical_metrics(resource)
            
            if not self._validate_historical_data_quality(historical_metrics):
                logger.debug(f"Insufficient data quality for resource {resource.get('resourceId')}")
                continue
            
            # Apply ML algorithms based on resource type
            if resource_type == 'ec2':
                recommendation = self._analyze_ec2_ml_rightsizing(resource, historical_metrics)
            elif resource_type == 'rds':
                recommendation = self._analyze_rds_ml_rightsizing(resource, historical_metrics)
            elif resource_type == 'lambda':
                recommendation = self._analyze_lambda_ml_rightsizing(resource, historical_metrics)
            elif resource_type == 'ebs':
                recommendation = self._analyze_ebs_ml_rightsizing(resource, historical_metrics)
            else:
                logger.warning(f"ML analysis not implemented for resource type: {resource_type}")
                continue
            
            if recommendation:
                recommendations.append(recommendation)
        
        return recommendations
    
    def analyze_historical_data_with_trends(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Implement historical data analysis with trend detection.
        
        This method provides comprehensive trend analysis including:
        - Seasonal pattern detection
        - Growth trend identification
        - Usage pattern classification
        - Anomaly detection in historical data
        
        Requirements: 3.1 - Collect historical CPU, memory, network, and storage metrics
        """
        logger.info(f"Starting historical data analysis with trend detection for {len(resources)} resources")
        
        trend_analysis_results = {
            'totalResourcesAnalyzed': len(resources),
            'trendsDetected': 0,
            'seasonalPatternsFound': 0,
            'growthTrendsIdentified': 0,
            'anomaliesDetected': 0,
            'resourceTrends': [],
            'overallTrends': {},
            'analysisTimestamp': datetime.utcnow().isoformat()
        }
        
        for resource in resources:
            resource_id = resource.get('resourceId')
            resource_type = resource.get('resourceType')
            
            # Collect comprehensive historical metrics
            historical_metrics = self._collect_comprehensive_historical_metrics(resource)
            
            if not self._validate_historical_data_quality(historical_metrics):
                logger.debug(f"Insufficient historical data for trend analysis: {resource_id}")
                continue
            
            # Perform trend detection
            trend_results = self._detect_resource_trends(resource_id, resource_type, historical_metrics)
            
            if trend_results:
                trend_analysis_results['resourceTrends'].append(trend_results)
                trend_analysis_results['trendsDetected'] += 1
                
                # Update counters
                if trend_results.get('seasonalPattern'):
                    trend_analysis_results['seasonalPatternsFound'] += 1
                if trend_results.get('growthTrend'):
                    trend_analysis_results['growthTrendsIdentified'] += 1
                if trend_results.get('anomaliesDetected', 0) > 0:
                    trend_analysis_results['anomaliesDetected'] += trend_results['anomaliesDetected']
        
        # Calculate overall trends across all resources
        trend_analysis_results['overallTrends'] = self._calculate_overall_trends(
            trend_analysis_results['resourceTrends']
        )
        
        # Cache results for future use
        self.trend_detection_cache[datetime.utcnow().isoformat()] = trend_analysis_results
        
        logger.info(f"Trend analysis completed: {trend_analysis_results['trendsDetected']} trends detected")
        return trend_analysis_results
    
    def _collect_comprehensive_historical_metrics(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect comprehensive historical metrics including CPU, memory, network, and storage.
        
        Enhanced version that collects more detailed metrics for trend analysis.
        Requirements: 3.1 - Collect historical CPU, memory, network, and storage metrics
        """
        metrics = resource.get('utilizationMetrics', {})
        
        # Extract all available time-series data
        comprehensive_data = {
            # CPU metrics
            'cpu_utilization': metrics.get('cpuUtilizationHistory', []),
            'cpu_credit_usage': metrics.get('cpuCreditUsageHistory', []),
            'cpu_credit_balance': metrics.get('cpuCreditBalanceHistory', []),
            
            # Memory metrics
            'memory_utilization': metrics.get('memoryUtilizationHistory', []),
            'memory_available': metrics.get('memoryAvailableHistory', []),
            'memory_used': metrics.get('memoryUsedHistory', []),
            
            # Network metrics
            'network_in': metrics.get('networkInHistory', []),
            'network_out': metrics.get('networkOutHistory', []),
            'network_packets_in': metrics.get('networkPacketsInHistory', []),
            'network_packets_out': metrics.get('networkPacketsOutHistory', []),
            
            # Storage metrics
            'disk_read_ops': metrics.get('diskReadOpsHistory', []),
            'disk_write_ops': metrics.get('diskWriteOpsHistory', []),
            'disk_read_bytes': metrics.get('diskReadBytesHistory', []),
            'disk_write_bytes': metrics.get('diskWriteBytesHistory', []),
            'disk_queue_depth': metrics.get('diskQueueDepthHistory', []),
            
            # Metadata
            'timestamps': metrics.get('timestamps', []),
            'data_points': metrics.get('dataPoints', 0),
            'collection_interval': metrics.get('collectionInterval', 300),  # 5 minutes default
            'data_age_days': metrics.get('dataAgeDays', 0)
        }
        
        # Calculate enhanced derived metrics
        if comprehensive_data['cpu_utilization']:
            cpu_data = comprehensive_data['cpu_utilization']
            comprehensive_data.update({
                'cpu_avg': statistics.mean(cpu_data),
                'cpu_median': statistics.median(cpu_data),
                'cpu_max': max(cpu_data),
                'cpu_min': min(cpu_data),
                'cpu_std': statistics.stdev(cpu_data) if len(cpu_data) > 1 else 0,
                'cpu_variance': statistics.variance(cpu_data) if len(cpu_data) > 1 else 0,
                'cpu_p95': sorted(cpu_data)[int(0.95 * len(cpu_data))] if cpu_data else 0,
                'cpu_p99': sorted(cpu_data)[int(0.99 * len(cpu_data))] if cpu_data else 0
            })
        
        if comprehensive_data['memory_utilization']:
            memory_data = comprehensive_data['memory_utilization']
            comprehensive_data.update({
                'memory_avg': statistics.mean(memory_data),
                'memory_median': statistics.median(memory_data),
                'memory_max': max(memory_data),
                'memory_min': min(memory_data),
                'memory_std': statistics.stdev(memory_data) if len(memory_data) > 1 else 0,
                'memory_variance': statistics.variance(memory_data) if len(memory_data) > 1 else 0,
                'memory_p95': sorted(memory_data)[int(0.95 * len(memory_data))] if memory_data else 0,
                'memory_p99': sorted(memory_data)[int(0.99 * len(memory_data))] if memory_data else 0
            })
        
        # Calculate network and storage derived metrics
        if comprehensive_data['network_in'] and comprehensive_data['network_out']:
            comprehensive_data.update({
                'network_total_avg': statistics.mean([
                    sum(pair) for pair in zip(comprehensive_data['network_in'], comprehensive_data['network_out'])
                ]),
                'network_ratio': (
                    statistics.mean(comprehensive_data['network_out']) / 
                    max(statistics.mean(comprehensive_data['network_in']), 1)
                )
            })
        
        if comprehensive_data['disk_read_ops'] and comprehensive_data['disk_write_ops']:
            comprehensive_data.update({
                'disk_total_ops_avg': statistics.mean([
                    sum(pair) for pair in zip(comprehensive_data['disk_read_ops'], comprehensive_data['disk_write_ops'])
                ]),
                'disk_read_write_ratio': (
                    statistics.mean(comprehensive_data['disk_write_ops']) / 
                    max(statistics.mean(comprehensive_data['disk_read_ops']), 1)
                )
            })
        
        return comprehensive_data
    
    def _validate_historical_data_quality(self, historical_metrics: Dict[str, Any]) -> bool:
        """
        Enhanced validation for historical data quality including trend analysis requirements.
        """
        thresholds = self.ml_thresholds['data_requirements']
        
        # Check minimum data points for trend analysis
        data_points = historical_metrics.get('data_points', 0)
        if data_points < thresholds['min_data_points']:
            return False
        
        # Check data recency
        timestamps = historical_metrics.get('timestamps', [])
        if timestamps:
            latest_timestamp = max(timestamps)
            if isinstance(latest_timestamp, str):
                try:
                    latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    return False
            
            age_days = (datetime.utcnow() - latest_timestamp).days
            if age_days > thresholds['max_data_age_days']:
                return False
        
        # Check data variance and completeness
        cpu_variance = historical_metrics.get('cpu_variance', 0)
        if cpu_variance < thresholds['min_variance_threshold']:
            return False
        
    def _validate_historical_data_quality(self, historical_metrics: Dict[str, Any]) -> bool:
        """
        Enhanced validation for historical data quality including trend analysis requirements.
        """
        thresholds = self.ml_thresholds['data_requirements']
        
        # Check minimum data points for trend analysis
        data_points = historical_metrics.get('data_points', 0)
        if data_points < thresholds['min_data_points']:
            return False
        
        # Check data recency
        timestamps = historical_metrics.get('timestamps', [])
        if timestamps:
            latest_timestamp = max(timestamps)
            if isinstance(latest_timestamp, str):
                try:
                    latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    return False
            
            age_days = (datetime.utcnow() - latest_timestamp).days
            if age_days > thresholds['max_data_age_days']:
                return False
        
        # Check data variance and completeness
        cpu_variance = historical_metrics.get('cpu_variance', 0)
        if cpu_variance < thresholds['min_variance_threshold']:
            return False
        
        # Check for data completeness (at least 80% of expected data points)
        expected_points = historical_metrics.get('data_points', 0)
        actual_cpu_points = len(historical_metrics.get('cpu_utilization', []))
        if actual_cpu_points < (expected_points * 0.8):
            return False
        
        return True
    
    def train_enhanced_ml_models(self, historical_data: List[Dict[str, Any]], 
                                validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Enhanced ML model training with comprehensive accuracy metrics and validation.
        
        This method provides:
        - Cross-validation for robust accuracy assessment
        - Multiple accuracy metrics (R², MAE, RMSE, MAPE)
        - Feature importance analysis
        - Model comparison and selection
        - Hyperparameter optimization
        
        Requirements: 3.5 - Add model training and validation with accuracy metrics
        """
        logger.info(f"Starting enhanced ML model training with {len(historical_data)} data points")
        
        training_results = {
            'models_trained': 0,
            'training_metrics': {},
            'validation_metrics': {},
            'cross_validation_scores': {},
            'feature_importance': {},
            'model_comparison': {},
            'best_models': {},
            'training_timestamp': datetime.utcnow().isoformat(),
            'hyperparameter_optimization': {}
        }
        
        # Group data by resource type for specialized training
        data_by_type = self._group_training_data_by_type(historical_data)
        
        for resource_type, type_data in data_by_type.items():
            if len(type_data) < 100:  # Need substantial data for enhanced training
                logger.warning(f"Insufficient data for enhanced training {resource_type} models: {len(type_data)} samples")
                continue
            
            logger.info(f"Enhanced training for {resource_type} with {len(type_data)} samples")
            
            # Train resource-specific models with enhanced validation
            if resource_type == 'ec2':
                model_results = self._train_enhanced_ec2_models(type_data, validation_split)
            elif resource_type == 'rds':
                model_results = self._train_enhanced_rds_models(type_data, validation_split)
            elif resource_type == 'lambda':
                model_results = self._train_enhanced_lambda_models(type_data, validation_split)
            else:
                continue
            
            # Store enhanced training results
            training_results['models_trained'] += len(model_results.get('models', {}))
            training_results['training_metrics'][resource_type] = model_results.get('training_metrics', {})
            training_results['validation_metrics'][resource_type] = model_results.get('validation_metrics', {})
            training_results['cross_validation_scores'][resource_type] = model_results.get('cv_scores', {})
            training_results['feature_importance'][resource_type] = model_results.get('feature_importance', {})
            training_results['model_comparison'][resource_type] = model_results.get('model_comparison', {})
            training_results['best_models'][resource_type] = model_results.get('best_model', None)
            training_results['hyperparameter_optimization'][resource_type] = model_results.get('hyperparameter_results', {})
        
        # Save enhanced trained models
        self._save_enhanced_trained_models()
        
        # Generate training summary
        training_summary = self._generate_training_summary(training_results)
        training_results['training_summary'] = training_summary
        
        logger.info(f"Enhanced ML model training completed. Trained {training_results['models_trained']} models")
        return training_results
    
    def _detect_resource_trends(self, resource_id: str, resource_type: str, 
                               historical_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect trends in resource utilization data.
        
        Identifies:
        - Seasonal patterns (daily, weekly, monthly)
        - Growth trends (increasing/decreasing usage)
        - Usage pattern classification (steady, bursty, cyclical)
        - Historical anomalies
        """
        cpu_data = historical_metrics.get('cpu_utilization', [])
        memory_data = historical_metrics.get('memory_utilization', [])
        timestamps = historical_metrics.get('timestamps', [])
        
        if not cpu_data or len(cpu_data) < 168:  # Need at least 1 week of hourly data
            return None
        
        trend_results = {
            'resourceId': resource_id,
            'resourceType': resource_type,
            'analysisTimestamp': datetime.utcnow().isoformat(),
            'dataPoints': len(cpu_data),
            'timeSpan': self._calculate_time_span(timestamps),
            'seasonalPattern': None,
            'growthTrend': None,
            'usagePattern': None,
            'anomaliesDetected': 0,
            'trendConfidence': 0.0,
            'recommendations': []
        }
        
        try:
            # Detect seasonal patterns
            seasonal_analysis = self._detect_seasonal_patterns(cpu_data, timestamps)
            if seasonal_analysis['pattern_detected']:
                trend_results['seasonalPattern'] = seasonal_analysis
                trend_results['trendConfidence'] += 25
            
            # Detect growth trends
            growth_analysis = self._detect_growth_trends(cpu_data, memory_data, timestamps)
            if growth_analysis['trend_detected']:
                trend_results['growthTrend'] = growth_analysis
                trend_results['trendConfidence'] += 25
            
            # Classify usage patterns
            usage_pattern = self._classify_usage_pattern(cpu_data, memory_data)
            trend_results['usagePattern'] = usage_pattern
            trend_results['trendConfidence'] += 20
            
            # Detect historical anomalies
            anomalies = self._detect_historical_anomalies(cpu_data, memory_data)
            trend_results['anomaliesDetected'] = len(anomalies)
            if anomalies:
                trend_results['historicalAnomalies'] = anomalies
                trend_results['trendConfidence'] += 10
            
            # Generate trend-based recommendations
            trend_results['recommendations'] = self._generate_trend_recommendations(
                trend_results, historical_metrics
            )
            
            # Final confidence adjustment
            trend_results['trendConfidence'] = min(100, trend_results['trendConfidence'])
            
        except Exception as e:
            logger.error(f"Error detecting trends for resource {resource_id}: {e}")
            return None
        
        return trend_results
        """
        Collect historical CPU, memory, network, and storage metrics.
        
        Requirements: 3.1 - Collect historical CPU, memory, network, and storage metrics
        """
        metrics = resource.get('utilizationMetrics', {})
        
        # Extract time-series data for different metrics
        historical_data = {
            'cpu_utilization': metrics.get('cpuUtilizationHistory', []),
            'memory_utilization': metrics.get('memoryUtilizationHistory', []),
            'network_in': metrics.get('networkInHistory', []),
            'network_out': metrics.get('networkOutHistory', []),
            'disk_read_ops': metrics.get('diskReadOpsHistory', []),
            'disk_write_ops': metrics.get('diskWriteOpsHistory', []),
            'disk_read_bytes': metrics.get('diskReadBytesHistory', []),
            'disk_write_bytes': metrics.get('diskWriteBytesHistory', []),
            'timestamps': metrics.get('timestamps', []),
            'data_points': metrics.get('dataPoints', 0)
        }
        
        # Add derived metrics
        if historical_data['cpu_utilization']:
            historical_data['cpu_avg'] = statistics.mean(historical_data['cpu_utilization'])
            historical_data['cpu_max'] = max(historical_data['cpu_utilization'])
            # Use statistics module instead of numpy for percentiles
            sorted_cpu = sorted(historical_data['cpu_utilization'])
            n = len(sorted_cpu)
            historical_data['cpu_p95'] = sorted_cpu[int(0.95 * n)] if n > 0 else 0
            historical_data['cpu_variance'] = statistics.variance(historical_data['cpu_utilization'])
        
        if historical_data['memory_utilization']:
            historical_data['memory_avg'] = statistics.mean(historical_data['memory_utilization'])
            historical_data['memory_max'] = max(historical_data['memory_utilization'])
            # Use statistics module instead of numpy for percentiles
            sorted_memory = sorted(historical_data['memory_utilization'])
            n = len(sorted_memory)
            historical_data['memory_p95'] = sorted_memory[int(0.95 * n)] if n > 0 else 0
            historical_data['memory_variance'] = statistics.variance(historical_data['memory_utilization'])
        
    def _collect_historical_metrics(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect historical CPU, memory, network, and storage metrics.
        
        Requirements: 3.1 - Collect historical CPU, memory, network, and storage metrics
        """
        # Use the comprehensive version for better analysis
        return self._collect_comprehensive_historical_metrics(resource)
    
    def _calculate_time_span(self, timestamps: List[str]) -> Dict[str, Any]:
        """Calculate the time span of the data."""
        if not timestamps or len(timestamps) < 2:
            return {'days': 0, 'hours': 0, 'start': None, 'end': None}
        
        try:
            start_time = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            time_diff = end_time - start_time
            
            return {
                'days': time_diff.days,
                'hours': time_diff.total_seconds() / 3600,
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        except (ValueError, IndexError):
            return {'days': 0, 'hours': 0, 'start': None, 'end': None}
    
    def _detect_seasonal_patterns(self, cpu_data: List[float], timestamps: List[str]) -> Dict[str, Any]:
        """Detect seasonal patterns in CPU utilization data."""
        if len(cpu_data) < 168:  # Need at least 1 week
            return {'pattern_detected': False, 'reason': 'insufficient_data'}
        
        try:
            # Convert to numpy array for analysis
            data = np.array(cpu_data)
            
            # Detect daily patterns (24-hour cycle)
            daily_pattern = self._analyze_daily_pattern(data)
            
            # Detect weekly patterns (7-day cycle) if we have enough data
            weekly_pattern = None
            if len(cpu_data) >= 168 * 4:  # 4 weeks
                weekly_pattern = self._analyze_weekly_pattern(data)
            
            # Determine if patterns are significant
            pattern_detected = (
                daily_pattern['significance'] > 0.3 or 
                (weekly_pattern and weekly_pattern['significance'] > 0.3)
            )
            
            return {
                'pattern_detected': pattern_detected,
                'daily_pattern': daily_pattern,
                'weekly_pattern': weekly_pattern,
                'confidence': max(
                    daily_pattern['significance'],
                    weekly_pattern['significance'] if weekly_pattern else 0
                ) * 100
            }
            
        except Exception as e:
            logger.debug(f"Error detecting seasonal patterns: {e}")
            return {'pattern_detected': False, 'error': str(e)}
    
    def _analyze_daily_pattern(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze daily patterns in the data."""
        if len(data) < 24:
            return {'significance': 0, 'pattern': None}
        
        # Group data by hour of day
        hours_data = [[] for _ in range(24)]
        for i, value in enumerate(data):
            hour = i % 24
            hours_data[hour].append(value)
        
        # Calculate average for each hour
        hourly_averages = [np.mean(hour_data) if hour_data else 0 for hour_data in hours_data]
        
        # Calculate significance (variance between hours vs within hours)
        overall_mean = np.mean(data)
        between_hour_variance = np.var(hourly_averages)
        within_hour_variance = np.mean([np.var(hour_data) if len(hour_data) > 1 else 0 for hour_data in hours_data])
        
        significance = between_hour_variance / (between_hour_variance + within_hour_variance + 1e-6)
        
        return {
            'significance': significance,
            'pattern': hourly_averages,
            'peak_hours': [i for i, avg in enumerate(hourly_averages) if avg > overall_mean * 1.2],
            'low_hours': [i for i, avg in enumerate(hourly_averages) if avg < overall_mean * 0.8]
        }
    
    def _analyze_weekly_pattern(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze weekly patterns in the data."""
        if len(data) < 168:  # 1 week
            return {'significance': 0, 'pattern': None}
        
        # Group data by day of week
        days_data = [[] for _ in range(7)]
        for i, value in enumerate(data):
            day = (i // 24) % 7
            days_data[day].append(value)
        
        # Calculate average for each day
        daily_averages = [np.mean(day_data) if day_data else 0 for day_data in days_data]
        
        # Calculate significance
        overall_mean = np.mean(data)
        between_day_variance = np.var(daily_averages)
        within_day_variance = np.mean([np.var(day_data) if len(day_data) > 1 else 0 for day_data in days_data])
        
        significance = between_day_variance / (between_day_variance + within_day_variance + 1e-6)
        
        return {
            'significance': significance,
            'pattern': daily_averages,
            'peak_days': [i for i, avg in enumerate(daily_averages) if avg > overall_mean * 1.2],
            'low_days': [i for i, avg in enumerate(daily_averages) if avg < overall_mean * 0.8]
        }
    
    def _detect_growth_trends(self, cpu_data: List[float], memory_data: List[float], 
                             timestamps: List[str]) -> Dict[str, Any]:
        """Detect growth trends in resource utilization."""
        if len(cpu_data) < 48:  # Need at least 2 days
            return {'trend_detected': False, 'reason': 'insufficient_data'}
        
        try:
            # Analyze CPU trend
            cpu_trend = self._calculate_linear_trend(cpu_data)
            
            # Analyze memory trend if available
            memory_trend = None
            if memory_data and len(memory_data) >= len(cpu_data) * 0.8:
                memory_trend = self._calculate_linear_trend(memory_data)
            
            # Determine overall trend
            trend_detected = abs(cpu_trend['slope']) > 0.1  # Significant slope
            trend_direction = 'increasing' if cpu_trend['slope'] > 0 else 'decreasing'
            
            return {
                'trend_detected': trend_detected,
                'direction': trend_direction,
                'cpu_trend': cpu_trend,
                'memory_trend': memory_trend,
                'confidence': cpu_trend['r_squared'] * 100,
                'projected_change_30_days': cpu_trend['slope'] * 30 * 24  # Assuming hourly data
            }
            
        except Exception as e:
            logger.debug(f"Error detecting growth trends: {e}")
            return {'trend_detected': False, 'error': str(e)}
    
    def _calculate_linear_trend(self, data: List[float]) -> Dict[str, Any]:
        """Calculate linear trend for time series data."""
        if len(data) < 2:
            return {'slope': 0, 'intercept': 0, 'r_squared': 0}
        
        x = np.arange(len(data))
        y = np.array(data)
        
        # Calculate linear regression
        n = len(data)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': max(0, r_squared)
        }
    
    def _classify_usage_pattern(self, cpu_data: List[float], memory_data: List[float]) -> Dict[str, Any]:
        """Classify the usage pattern of the resource."""
        if not cpu_data:
            return {'pattern': 'unknown', 'confidence': 0}
        
        cpu_array = np.array(cpu_data)
        cpu_mean = np.mean(cpu_array)
        cpu_std = np.std(cpu_array)
        cpu_cv = cpu_std / cpu_mean if cpu_mean > 0 else 0  # Coefficient of variation
        
        # Calculate burstiness
        cpu_max = np.max(cpu_array)
        cpu_min = np.min(cpu_array)
        burstiness = (cpu_max - cpu_min) / cpu_mean if cpu_mean > 0 else 0
        
        # Classify pattern
        if cpu_cv < 0.2 and burstiness < 1.0:
            pattern = 'steady'
            confidence = 0.9
        elif cpu_cv > 0.5 or burstiness > 2.0:
            pattern = 'bursty'
            confidence = 0.8
        elif self._has_cyclical_pattern(cpu_array):
            pattern = 'cyclical'
            confidence = 0.7
        else:
            pattern = 'variable'
            confidence = 0.6
        
        return {
            'pattern': pattern,
            'confidence': confidence,
            'coefficient_of_variation': cpu_cv,
            'burstiness': burstiness,
            'statistics': {
                'mean': cpu_mean,
                'std': cpu_std,
                'min': cpu_min,
                'max': cpu_max
            }
        }
    
    def _has_cyclical_pattern(self, data: np.ndarray) -> bool:
        """Check if data has cyclical patterns using autocorrelation."""
        if len(data) < 48:  # Need at least 2 days
            return False
        
        try:
            # Calculate autocorrelation for different lags
            autocorr_24h = np.corrcoef(data[:-24], data[24:])[0, 1] if len(data) > 24 else 0
            autocorr_168h = np.corrcoef(data[:-168], data[168:])[0, 1] if len(data) > 168 else 0
            
            # Consider cyclical if strong autocorrelation at 24h or 168h
            return autocorr_24h > 0.5 or autocorr_168h > 0.5
        except:
            return False
    
    def _detect_historical_anomalies(self, cpu_data: List[float], memory_data: List[float]) -> List[Dict[str, Any]]:
        """Detect anomalies in historical data."""
        anomalies = []
        
        if not cpu_data or len(cpu_data) < 24:
            return anomalies
        
        cpu_array = np.array(cpu_data)
        cpu_mean = np.mean(cpu_array)
        cpu_std = np.std(cpu_array)
        
        # Use 3-sigma rule for anomaly detection
        threshold = 3 * cpu_std
        
        for i, value in enumerate(cpu_array):
            if abs(value - cpu_mean) > threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'expected': cpu_mean,
                    'deviation': abs(value - cpu_mean),
                    'severity': 'high' if abs(value - cpu_mean) > 4 * cpu_std else 'medium'
                })
        
        return anomalies
    
    def _generate_trend_recommendations(self, trend_results: Dict[str, Any], 
                                      historical_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on trend analysis."""
        recommendations = []
        
        # Seasonal pattern recommendations
        if trend_results.get('seasonalPattern', {}).get('pattern_detected'):
            seasonal = trend_results['seasonalPattern']
            if seasonal.get('daily_pattern'):
                recommendations.append(
                    "Consider scheduled scaling based on detected daily usage patterns"
                )
            if seasonal.get('weekly_pattern'):
                recommendations.append(
                    "Implement weekly scaling schedule to optimize for workday vs weekend usage"
                )
        
        # Growth trend recommendations
        if trend_results.get('growthTrend', {}).get('trend_detected'):
            growth = trend_results['growthTrend']
            if growth['direction'] == 'increasing':
                recommendations.append(
                    f"Resource usage is trending upward. Consider proactive scaling in next 30 days"
                )
            else:
                recommendations.append(
                    f"Resource usage is trending downward. Consider downsizing opportunities"
                )
        
        # Usage pattern recommendations
        usage_pattern = trend_results.get('usagePattern', {})
        if usage_pattern.get('pattern') == 'bursty':
            recommendations.append(
                "Bursty usage pattern detected. Consider burstable instance types or auto-scaling"
            )
        elif usage_pattern.get('pattern') == 'steady':
            recommendations.append(
                "Steady usage pattern detected. Reserved instances may provide cost savings"
            )
        
        # Anomaly recommendations
        if trend_results.get('anomaliesDetected', 0) > 0:
            recommendations.append(
                f"Historical anomalies detected ({trend_results['anomaliesDetected']}). "
                "Monitor for recurring issues and consider alerting thresholds"
            )
        
        return recommendations
    
    def _calculate_overall_trends(self, resource_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall trends across all analyzed resources."""
        if not resource_trends:
            return {}
        
        # Aggregate trend statistics
        total_resources = len(resource_trends)
        seasonal_resources = sum(1 for trend in resource_trends 
                               if trend.get('seasonalPattern', {}).get('pattern_detected'))
        growth_resources = sum(1 for trend in resource_trends 
                             if trend.get('growthTrend', {}).get('trend_detected'))
        
        # Calculate average confidence
        avg_confidence = np.mean([trend.get('trendConfidence', 0) for trend in resource_trends])
        
        # Identify common patterns
        pattern_counts = {}
        for trend in resource_trends:
            pattern = trend.get('usagePattern', {}).get('pattern', 'unknown')
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        most_common_pattern = max(pattern_counts.items(), key=lambda x: x[1]) if pattern_counts else ('unknown', 0)
        
        return {
            'totalResources': total_resources,
            'resourcesWithSeasonalPatterns': seasonal_resources,
            'resourcesWithGrowthTrends': growth_resources,
            'averageConfidence': avg_confidence,
            'mostCommonUsagePattern': most_common_pattern[0],
            'patternDistribution': pattern_counts,
            'seasonalPatternPercentage': (seasonal_resources / total_resources) * 100,
            'growthTrendPercentage': (growth_resources / total_resources) * 100
        }
    
    def generate_recommendations_with_uncertainty_bounds(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate size recommendations with confidence intervals and uncertainty bounds.
        
        This method provides comprehensive uncertainty quantification including:
        - Confidence intervals for predictions
        - Uncertainty bounds for cost savings
        - Risk assessment for recommendations
        - Sensitivity analysis
        
        Requirements: 3.2 - Generate ML-powered size recommendations with confidence intervals
        """
        logger.info(f"Generating ML recommendations with uncertainty bounds for {len(resources)} resources")
        
        uncertainty_analysis = {
            'totalResources': len(resources),
            'recommendationsGenerated': 0,
            'highConfidenceRecommendations': 0,
            'mediumConfidenceRecommendations': 0,
            'lowConfidenceRecommendations': 0,
            'recommendations': [],
            'uncertaintyMetrics': {},
            'sensitivityAnalysis': {},
            'analysisTimestamp': datetime.utcnow().isoformat()
        }
        
        for resource in resources:
            # Generate base ML recommendation
            historical_metrics = self._collect_comprehensive_historical_metrics(resource)
            
            if not self._validate_historical_data_quality(historical_metrics):
                continue
            
            # Generate recommendation with uncertainty quantification
            recommendation = self._generate_recommendation_with_uncertainty(resource, historical_metrics)
            
            if recommendation:
                uncertainty_analysis['recommendations'].append(recommendation)
                uncertainty_analysis['recommendationsGenerated'] += 1
                
                # Update confidence counters
                confidence_level = recommendation.get('confidenceAnalysis', {}).get('confidence_level', 'MEDIUM')
                if confidence_level == 'HIGH':
                    uncertainty_analysis['highConfidenceRecommendations'] += 1
                elif confidence_level == 'MEDIUM':
                    uncertainty_analysis['mediumConfidenceRecommendations'] += 1
                else:
                    uncertainty_analysis['lowConfidenceRecommendations'] += 1
        
        # Calculate overall uncertainty metrics
        uncertainty_analysis['uncertaintyMetrics'] = self._calculate_uncertainty_metrics(
            uncertainty_analysis['recommendations']
        )
        
        # Perform sensitivity analysis
        uncertainty_analysis['sensitivityAnalysis'] = self._perform_sensitivity_analysis(
            uncertainty_analysis['recommendations']
        )
        
        logger.info(f"Generated {uncertainty_analysis['recommendationsGenerated']} recommendations with uncertainty bounds")
        return uncertainty_analysis
    
    def _generate_recommendation_with_uncertainty(self, resource: Dict[str, Any], 
                                                 historical_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a single recommendation with comprehensive uncertainty analysis."""
        resource_type = resource.get('resourceType', 'unknown')
        
        # Apply ML models and get predictions
        if resource_type == 'ec2':
            ml_predictions = self._apply_ml_models_ec2(historical_metrics, resource.get('instanceType', ''))
        elif resource_type == 'rds':
            ml_predictions = self._apply_ml_models_rds(historical_metrics, resource.get('dbInstanceClass', ''))
        elif resource_type == 'lambda':
            ml_predictions = self._apply_ml_models_lambda(
                historical_metrics, resource.get('memorySize', 128), resource.get('timeout', 3)
            )
        elif resource_type == 'ebs':
            ml_predictions = self._apply_ml_models_ebs(
                historical_metrics, resource.get('volumeType', 'gp2'), resource.get('size', 0)
            )
        else:
            return None
        
        if not ml_predictions:
            return None
        
        # Calculate enhanced confidence intervals
        confidence_analysis = self._calculate_enhanced_confidence_intervals(ml_predictions, historical_metrics)
        
        # Calculate uncertainty bounds for cost savings
        cost_uncertainty = self._calculate_cost_uncertainty_bounds(resource, ml_predictions, confidence_analysis)
        
        # Perform risk assessment
        risk_assessment = self._assess_recommendation_risk(resource, ml_predictions, confidence_analysis)
        
        # Generate the recommendation based on resource type
        if resource_type == 'ec2':
            base_recommendation = self._analyze_ec2_ml_rightsizing(resource, historical_metrics)
        elif resource_type == 'rds':
            base_recommendation = self._analyze_rds_ml_rightsizing(resource, historical_metrics)
        elif resource_type == 'lambda':
            base_recommendation = self._analyze_lambda_ml_rightsizing(resource, historical_metrics)
        elif resource_type == 'ebs':
            base_recommendation = self._analyze_ebs_ml_rightsizing(resource, historical_metrics)
        else:
            return None
        
        if not base_recommendation:
            return None
        
        # Enhance with uncertainty information
        base_recommendation['uncertaintyBounds'] = cost_uncertainty
        base_recommendation['riskAssessment'] = risk_assessment
        base_recommendation['confidenceAnalysis'] = confidence_analysis
        
        return base_recommendation
    
    def _calculate_enhanced_confidence_intervals(self, ml_predictions: Dict[str, Any], 
                                               historical_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate enhanced confidence intervals with multiple uncertainty sources.
        
        Requirements: 3.2 - Generate ML-powered size recommendations with confidence intervals
        """
        confidences = []
        predictions = []
        model_uncertainties = []
        
        # Collect predictions and confidences from all models
        for model_name, prediction in ml_predictions.items():
            if 'confidence' in prediction:
                confidences.append(prediction['confidence'])
            if 'predicted_cpu_avg' in prediction:
                predictions.append(prediction['predicted_cpu_avg'])
            
            # Calculate model-specific uncertainty
            model_uncertainty = self._calculate_model_uncertainty(model_name, prediction)
            model_uncertainties.append(model_uncertainty)
        
        if not confidences or not predictions:
            return {
                'overall_confidence': 50.0,
                'confidence_level': ConfidenceLevel.MEDIUM.value,
                'confidence_interval': {'lower': 0, 'upper': 100},
                'uncertainty_sources': {}
            }
        
        # Calculate overall confidence with uncertainty propagation
        overall_confidence = self._calculate_weighted_confidence(confidences, model_uncertainties)
        
        # Determine confidence level with enhanced thresholds
        thresholds = self.ml_thresholds['confidence_scoring']
        if overall_confidence >= thresholds['high_confidence_threshold']:
            confidence_level = ConfidenceLevel.HIGH.value
        elif overall_confidence >= thresholds['medium_confidence_threshold']:
            confidence_level = ConfidenceLevel.MEDIUM.value
        else:
            confidence_level = ConfidenceLevel.LOW.value
        
        # Calculate prediction confidence intervals
        pred_mean = np.mean(predictions)
        pred_std = np.std(predictions) if len(predictions) > 1 else pred_mean * 0.15
        
        # Adjust for data quality
        data_quality_factor = self._assess_data_quality_factor(historical_metrics)
        adjusted_std = pred_std * (2 - data_quality_factor)  # Lower quality = higher uncertainty
        
        # Calculate multiple confidence intervals
        confidence_intervals = {
            '68_percent': {  # 1 sigma
                'lower': max(0, pred_mean - adjusted_std),
                'upper': pred_mean + adjusted_std
            },
            '95_percent': {  # 2 sigma
                'lower': max(0, pred_mean - 2 * adjusted_std),
                'upper': pred_mean + 2 * adjusted_std
            },
            '99_percent': {  # 3 sigma
                'lower': max(0, pred_mean - 3 * adjusted_std),
                'upper': pred_mean + 3 * adjusted_std
            }
        }
        
        # Identify uncertainty sources
        uncertainty_sources = {
            'model_disagreement': np.std(predictions) / pred_mean if pred_mean > 0 else 0,
            'data_quality': 1 - data_quality_factor,
            'temporal_variability': self._calculate_temporal_uncertainty(historical_metrics),
            'measurement_noise': self._estimate_measurement_noise(historical_metrics)
        }
        
        return {
            'overall_confidence': overall_confidence,
            'confidence_level': confidence_level,
            'confidence_intervals': confidence_intervals,
            'prediction_mean': pred_mean,
            'prediction_std': adjusted_std,
            'uncertainty_sources': uncertainty_sources,
            'model_confidences': {model: pred.get('confidence', 50) for model, pred in ml_predictions.items()},
            'data_quality_factor': data_quality_factor
        }
    
    def _calculate_model_uncertainty(self, model_name: str, prediction: Dict[str, Any]) -> float:
        """Calculate uncertainty specific to a model."""
        base_uncertainty = 0.1  # 10% base uncertainty
        
        # Adjust based on model type
        if 'linear_regression' in model_name:
            base_uncertainty *= 1.2  # Linear models have higher uncertainty for non-linear patterns
        elif 'random_forest' in model_name:
            base_uncertainty *= 0.8  # Ensemble methods typically have lower uncertainty
        elif 'trained_' in model_name:
            base_uncertainty *= 0.9  # Trained models have slightly lower uncertainty
        
        # Adjust based on prediction confidence
        confidence = prediction.get('confidence', 50) / 100
        adjusted_uncertainty = base_uncertainty * (2 - confidence)
        
        return adjusted_uncertainty
    
    def _calculate_weighted_confidence(self, confidences: List[float], uncertainties: List[float]) -> float:
        """Calculate weighted confidence considering model uncertainties."""
        if not confidences or not uncertainties:
            return 50.0
        
        # Use inverse uncertainty as weights
        weights = [1 / (unc + 1e-6) for unc in uncertainties]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return np.mean(confidences)
        
        weighted_confidence = sum(conf * weight for conf, weight in zip(confidences, weights)) / total_weight
        return max(0, min(100, weighted_confidence))
    
    def _assess_data_quality_factor(self, historical_metrics: Dict[str, Any]) -> float:
        """Assess data quality and return a factor between 0 and 1."""
        quality_factors = []
        
        # Data completeness
        expected_points = historical_metrics.get('data_points', 0)
        actual_points = len(historical_metrics.get('cpu_utilization', []))
        completeness = actual_points / max(expected_points, 1)
        quality_factors.append(min(1.0, completeness))
        
        # Data recency
        data_age_days = historical_metrics.get('data_age_days', 0)
        recency_factor = max(0, 1 - (data_age_days / 90))  # Decay over 90 days
        quality_factors.append(recency_factor)
        
        # Data variance (too low variance indicates poor quality)
        cpu_variance = historical_metrics.get('cpu_variance', 0)
        variance_factor = min(1.0, cpu_variance / 10)  # Normalize to reasonable range
        quality_factors.append(variance_factor)
        
        # Data consistency (coefficient of variation)
        cpu_avg = historical_metrics.get('cpu_avg', 0)
        cpu_std = historical_metrics.get('cpu_std', 0)
        if cpu_avg > 0:
            cv = cpu_std / cpu_avg
            consistency_factor = max(0, 1 - (cv / 2))  # Penalize high variability
            quality_factors.append(consistency_factor)
        
        return np.mean(quality_factors) if quality_factors else 0.5
    
    def _calculate_temporal_uncertainty(self, historical_metrics: Dict[str, Any]) -> float:
        """Calculate uncertainty due to temporal variations."""
        cpu_data = historical_metrics.get('cpu_utilization', [])
        if len(cpu_data) < 24:
            return 0.5  # High uncertainty for insufficient data
        
        # Calculate day-to-day variation
        daily_averages = []
        for i in range(0, len(cpu_data), 24):
            day_data = cpu_data[i:i+24]
            if day_data:
                daily_averages.append(np.mean(day_data))
        
        if len(daily_averages) < 2:
            return 0.3
        
        # Coefficient of variation for daily averages
        daily_cv = np.std(daily_averages) / max(np.mean(daily_averages), 1e-6)
        return min(1.0, daily_cv)
    
    def _estimate_measurement_noise(self, historical_metrics: Dict[str, Any]) -> float:
        """Estimate measurement noise in the data."""
        cpu_data = historical_metrics.get('cpu_utilization', [])
        if len(cpu_data) < 10:
            return 0.1
        
        # Estimate noise using high-frequency variations
        differences = [abs(cpu_data[i] - cpu_data[i-1]) for i in range(1, len(cpu_data))]
        noise_estimate = np.mean(differences) / max(np.mean(cpu_data), 1e-6)
        
        return min(0.5, noise_estimate)
    
    def _calculate_cost_uncertainty_bounds(self, resource: Dict[str, Any], ml_predictions: Dict[str, Any], 
                                         confidence_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate uncertainty bounds for cost savings estimates.
        
        Requirements: 3.3 - Estimate cost savings and performance impact
        """
        current_cost = resource.get('currentCost', 0)
        resource_type = resource.get('resourceType', 'unknown')
        
        # Get prediction intervals
        confidence_intervals = confidence_analysis.get('confidence_intervals', {})
        ci_95 = confidence_intervals.get('95_percent', {'lower': 0, 'upper': 100})
        
        # Calculate cost bounds based on prediction uncertainty
        if resource_type == 'ec2':
            cost_bounds = self._calculate_ec2_cost_bounds(resource, ci_95, current_cost)
        elif resource_type == 'rds':
            cost_bounds = self._calculate_rds_cost_bounds(resource, ci_95, current_cost)
        elif resource_type == 'lambda':
            cost_bounds = self._calculate_lambda_cost_bounds(resource, ci_95, current_cost)
        elif resource_type == 'ebs':
            cost_bounds = self._calculate_ebs_cost_bounds(resource, ci_95, current_cost)
        else:
            # Generic cost bounds
            cost_bounds = {
                'optimistic_savings': current_cost * 0.3,
                'expected_savings': current_cost * 0.15,
                'pessimistic_savings': current_cost * 0.05,
                'confidence_level': 'LOW'
            }
        
        # Add uncertainty metrics
        uncertainty_percentage = (cost_bounds['optimistic_savings'] - cost_bounds['pessimistic_savings']) / max(current_cost, 1)
        
        cost_bounds.update({
            'current_cost': current_cost,
            'uncertainty_percentage': uncertainty_percentage * 100,
            'savings_range': {
                'min': cost_bounds['pessimistic_savings'],
                'max': cost_bounds['optimistic_savings'],
                'expected': cost_bounds['expected_savings']
            }
        })
        
        return cost_bounds
    
    def _calculate_ec2_cost_bounds(self, resource: Dict[str, Any], prediction_interval: Dict[str, Any], 
                                  current_cost: float) -> Dict[str, Any]:
        """Calculate cost bounds for EC2 instances."""
        # Simplified cost calculation with bounds
        # In real implementation, use AWS Pricing API with instance type mapping
        
        lower_utilization = prediction_interval['lower']
        upper_utilization = prediction_interval['upper']
        
        # Map utilization to potential instance types and costs
        optimistic_savings = current_cost * 0.4  # Best case: significant downsizing
        expected_savings = current_cost * 0.2    # Expected case: moderate optimization
        pessimistic_savings = current_cost * 0.05 # Worst case: minimal savings
        
        return {
            'optimistic_savings': optimistic_savings,
            'expected_savings': expected_savings,
            'pessimistic_savings': pessimistic_savings,
            'confidence_level': 'MEDIUM'
        }
    
    def _calculate_rds_cost_bounds(self, resource: Dict[str, Any], prediction_interval: Dict[str, Any], 
                                  current_cost: float) -> Dict[str, Any]:
        """Calculate cost bounds for RDS instances."""
        return {
            'optimistic_savings': current_cost * 0.35,
            'expected_savings': current_cost * 0.18,
            'pessimistic_savings': current_cost * 0.03,
            'confidence_level': 'MEDIUM'
        }
    
    def _calculate_lambda_cost_bounds(self, resource: Dict[str, Any], prediction_interval: Dict[str, Any], 
                                     current_cost: float) -> Dict[str, Any]:
        """Calculate cost bounds for Lambda functions."""
        return {
            'optimistic_savings': current_cost * 0.5,
            'expected_savings': current_cost * 0.25,
            'pessimistic_savings': current_cost * 0.1,
            'confidence_level': 'HIGH'  # Lambda optimization is typically more predictable
        }
    
    def _calculate_ebs_cost_bounds(self, resource: Dict[str, Any], prediction_interval: Dict[str, Any], 
                                  current_cost: float) -> Dict[str, Any]:
        """Calculate cost bounds for EBS volumes."""
        return {
            'optimistic_savings': current_cost * 0.3,
            'expected_savings': current_cost * 0.15,
            'pessimistic_savings': current_cost * 0.02,
            'confidence_level': 'MEDIUM'
        }
    
    def _assess_recommendation_risk(self, resource: Dict[str, Any], ml_predictions: Dict[str, Any], 
                                   confidence_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the risk associated with the recommendation."""
        confidence_level = confidence_analysis.get('confidence_level', 'MEDIUM')
        overall_confidence = confidence_analysis.get('overall_confidence', 50)
        uncertainty_sources = confidence_analysis.get('uncertainty_sources', {})
        
        # Calculate risk factors
        risk_factors = []
        risk_score = 0
        
        # Confidence-based risk
        if confidence_level == 'LOW':
            risk_factors.append("Low prediction confidence")
            risk_score += 30
        elif confidence_level == 'MEDIUM':
            risk_score += 15
        
        # Data quality risk
        data_quality = confidence_analysis.get('data_quality_factor', 0.5)
        if data_quality < 0.7:
            risk_factors.append("Poor data quality")
            risk_score += 20
        
        # Model disagreement risk
        model_disagreement = uncertainty_sources.get('model_disagreement', 0)
        if model_disagreement > 0.3:
            risk_factors.append("High model disagreement")
            risk_score += 25
        
        # Temporal variability risk
        temporal_uncertainty = uncertainty_sources.get('temporal_variability', 0)
        if temporal_uncertainty > 0.4:
            risk_factors.append("High temporal variability")
            risk_score += 15
        
        # Determine overall risk level
        if risk_score >= 50:
            risk_level = RiskLevel.HIGH.value
        elif risk_score >= 25:
            risk_level = RiskLevel.MEDIUM.value
        else:
            risk_level = RiskLevel.LOW.value
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'mitigation_strategies': self._generate_risk_mitigation_strategies(risk_factors),
            'recommendation': self._generate_risk_recommendation(risk_level, risk_score)
        }
    
    def _generate_risk_mitigation_strategies(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation strategies based on identified risk factors."""
        strategies = []
        
        for factor in risk_factors:
            if "Low prediction confidence" in factor:
                strategies.append("Collect more historical data before implementing changes")
                strategies.append("Start with smaller configuration changes")
            elif "Poor data quality" in factor:
                strategies.append("Improve monitoring and data collection")
                strategies.append("Validate data sources and collection methods")
            elif "High model disagreement" in factor:
                strategies.append("Use ensemble predictions with conservative estimates")
                strategies.append("Implement gradual changes with monitoring")
            elif "High temporal variability" in factor:
                strategies.append("Consider seasonal patterns in implementation timing")
                strategies.append("Implement auto-scaling instead of fixed sizing")
        
        # Add general strategies
        strategies.extend([
            "Implement changes during low-usage periods",
            "Set up comprehensive monitoring and alerting",
            "Prepare rollback procedures before implementation"
        ])
        
        return list(set(strategies))  # Remove duplicates
    
    def _generate_risk_recommendation(self, risk_level: str, risk_score: int) -> str:
        """Generate risk-based recommendation."""
        if risk_level == RiskLevel.HIGH.value:
            return "High risk recommendation. Consider manual review and gradual implementation."
        elif risk_level == RiskLevel.MEDIUM.value:
            return "Medium risk recommendation. Implement with careful monitoring and rollback plan."
        else:
            return "Low risk recommendation. Safe to implement with standard monitoring."
    
    def _calculate_uncertainty_metrics(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall uncertainty metrics across all recommendations."""
        if not recommendations:
            return {}
        
        confidences = [rec.get('confidenceAnalysis', {}).get('overall_confidence', 50) 
                      for rec in recommendations]
        
        uncertainty_scores = [100 - conf for conf in confidences]
        
        return {
            'average_confidence': np.mean(confidences),
            'confidence_std': np.std(confidences),
            'average_uncertainty': np.mean(uncertainty_scores),
            'uncertainty_distribution': {
                'low_uncertainty': sum(1 for u in uncertainty_scores if u < 20),
                'medium_uncertainty': sum(1 for u in uncertainty_scores if 20 <= u < 40),
                'high_uncertainty': sum(1 for u in uncertainty_scores if u >= 40)
            }
        }
    
    def _perform_sensitivity_analysis(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform sensitivity analysis on recommendations."""
        if not recommendations:
            return {}
        
        # Analyze sensitivity to different factors
        sensitivity_results = {
            'data_quality_sensitivity': self._analyze_data_quality_sensitivity(recommendations),
            'confidence_threshold_sensitivity': self._analyze_confidence_sensitivity(recommendations),
            'cost_impact_sensitivity': self._analyze_cost_sensitivity(recommendations)
        }
        
        return sensitivity_results
    
    def _analyze_data_quality_sensitivity(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sensitivity to data quality variations."""
        quality_factors = [rec.get('confidenceAnalysis', {}).get('data_quality_factor', 0.5) 
                          for rec in recommendations]
        
        savings = [rec.get('estimatedMonthlySavings', 0) for rec in recommendations]
        
        # Calculate correlation between data quality and savings confidence
        if len(quality_factors) > 1 and len(savings) > 1:
            correlation = np.corrcoef(quality_factors, savings)[0, 1]
        else:
            correlation = 0
        
        return {
            'quality_savings_correlation': correlation,
            'average_quality_factor': np.mean(quality_factors),
            'quality_impact': 'high' if abs(correlation) > 0.5 else 'medium' if abs(correlation) > 0.3 else 'low'
        }
    
    def _analyze_confidence_sensitivity(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sensitivity to confidence threshold changes."""
        confidences = [rec.get('confidenceAnalysis', {}).get('overall_confidence', 50) 
                      for rec in recommendations]
        
        # Test different confidence thresholds
        thresholds = [60, 70, 80, 90]
        threshold_results = {}
        
        for threshold in thresholds:
            qualifying_recs = sum(1 for conf in confidences if conf >= threshold)
            threshold_results[f'threshold_{threshold}'] = {
                'qualifying_recommendations': qualifying_recs,
                'percentage': (qualifying_recs / len(recommendations)) * 100 if recommendations else 0
            }

        
        return threshold_results
    
    def _analyze_cost_sensitivity(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sensitivity of cost savings to uncertainty bounds."""
        cost_bounds = [rec.get('uncertaintyBounds', {}) for rec in recommendations]
        
        total_optimistic = sum(bounds.get('optimistic_savings', 0) for bounds in cost_bounds)
        total_expected = sum(bounds.get('expected_savings', 0) for bounds in cost_bounds)
        total_pessimistic = sum(bounds.get('pessimistic_savings', 0) for bounds in cost_bounds)
        
        return {
            'total_optimistic_savings': total_optimistic,
            'total_expected_savings': total_expected,
            'total_pessimistic_savings': total_pessimistic,
            'savings_uncertainty_range': total_optimistic - total_pessimistic,
            'uncertainty_percentage': ((total_optimistic - total_pessimistic) / max(total_expected, 1)) * 100
        }
        """
        Validate that historical data is sufficient for ML analysis.
        
        Args:
            historical_metrics: Historical metrics data
            
        Returns:
            True if data quality is sufficient for ML analysis
        """
        thresholds = self.ml_thresholds['data_requirements']
        
        # Check minimum data points
        data_points = historical_metrics.get('data_points', 0)
        if data_points < thresholds['min_data_points']:
            return False
        
        # Check data recency
        timestamps = historical_metrics.get('timestamps', [])
        if timestamps:
            latest_timestamp = max(timestamps)
            if isinstance(latest_timestamp, str):
                latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
            
            age_days = (datetime.utcnow() - latest_timestamp).days
            if age_days > thresholds['max_data_age_days']:
                return False
        
        # Check data variance (ensure there's actual variation in the data)
        cpu_variance = historical_metrics.get('cpu_variance', 0)
        if cpu_variance < thresholds['min_variance_threshold']:
            return False
        
        return True
    
    def train_ml_models(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train ML models using historical resource utilization data.
        
        Args:
            historical_data: List of historical resource data with utilization metrics
            
        Returns:
            Training results with accuracy metrics
            
        Requirements: 3.5 - Add model training and validation with accuracy metrics
        """
        logger.info(f"Starting ML model training with {len(historical_data)} data points")
        
        training_results = {
            'models_trained': 0,
            'training_accuracy': {},
            'validation_accuracy': {},
            'model_performance': {},
            'training_timestamp': datetime.utcnow().isoformat()
        }
        
        # Group data by resource type for specialized training
        data_by_type = self._group_training_data_by_type(historical_data)
        
        for resource_type, type_data in data_by_type.items():
            if len(type_data) < 50:  # Need minimum data for training
                logger.warning(f"Insufficient data for training {resource_type} models: {len(type_data)} samples")
                continue
            
            logger.info(f"Training models for {resource_type} with {len(type_data)} samples")
            
            # Train resource-specific models
            if resource_type == 'ec2':
                model_results = self._train_ec2_models(type_data)
            elif resource_type == 'rds':
                model_results = self._train_rds_models(type_data)
            elif resource_type == 'lambda':
                model_results = self._train_lambda_models(type_data)
            else:
                continue
            
            # Store training results
            training_results['models_trained'] += len(model_results)
            training_results['training_accuracy'][resource_type] = model_results.get('training_accuracy', {})
            training_results['validation_accuracy'][resource_type] = model_results.get('validation_accuracy', {})
            training_results['model_performance'][resource_type] = model_results.get('performance_metrics', {})
        
        # Save trained models
        self._save_trained_models()
        
        logger.info(f"ML model training completed. Trained {training_results['models_trained']} models")
        return training_results
    
    def validate_ml_models(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate trained ML models using separate validation dataset.
        
        Args:
            validation_data: Validation dataset
            
        Returns:
            Validation results with accuracy metrics
        """
        logger.info(f"Starting ML model validation with {len(validation_data)} validation samples")
        
        validation_results = {
            'models_validated': 0,
            'validation_accuracy': {},
            'prediction_errors': {},
            'confidence_calibration': {},
            'validation_timestamp': datetime.utcnow().isoformat()
        }
        
        # Group validation data by resource type
        data_by_type = self._group_training_data_by_type(validation_data)
        
        for resource_type, type_data in data_by_type.items():
            if resource_type not in self.trained_models:
                logger.warning(f"No trained models found for {resource_type}")
                continue
            
            logger.info(f"Validating {resource_type} models with {len(type_data)} samples")
            
            # Validate resource-specific models
            if resource_type == 'ec2':
                validation_result = self._validate_ec2_models(type_data)
            elif resource_type == 'rds':
                validation_result = self._validate_rds_models(type_data)
            elif resource_type == 'lambda':
                validation_result = self._validate_lambda_models(type_data)
            else:
                continue
            
            validation_results['models_validated'] += 1
            validation_results['validation_accuracy'][resource_type] = validation_result.get('accuracy', {})
            validation_results['prediction_errors'][resource_type] = validation_result.get('errors', {})
            validation_results['confidence_calibration'][resource_type] = validation_result.get('calibration', {})
        
        # Update model metrics
        self._update_model_metrics(validation_results)
        
        logger.info(f"ML model validation completed for {validation_results['models_validated']} model types")
        return validation_results
    
    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for all trained models.
        
        Returns:
            Model performance metrics and accuracy statistics
        """
        return {
            'model_metrics': self.model_metrics,
            'trained_models': list(self.trained_models.keys()),
            'model_count': len(self.trained_models),
            'last_training': max([metrics.get('last_trained', '') for metrics in self.model_metrics.values()] or ['']),
            'overall_accuracy': self._calculate_overall_accuracy(),
            'model_status': self._get_model_status()
        }
    
    def _group_training_data_by_type(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group training data by resource type."""
        grouped = {}
        
        for item in data:
            resource_type = item.get('resourceType', 'unknown')
            if resource_type not in grouped:
                grouped[resource_type] = []
            grouped[resource_type].append(item)
        
        return grouped
    
    def _train_ec2_models(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train ML models specifically for EC2 instances."""
        logger.info(f"Training EC2 models with {len(training_data)} samples")
        
        # Prepare training features and targets
        features, targets = self._prepare_ec2_training_data(training_data)
        
        if len(features) < 10:
            logger.warning("Insufficient EC2 training data after preprocessing")
            return {}
        
        # Split data for training and validation
        X_train, X_val, y_train, y_val = train_test_split(features, targets, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        models = {}
        training_accuracy = {}
        validation_accuracy = {}
        performance_metrics = {}
        
        # Train Linear Regression model
        try:
            lr_model = LinearRegression()
            lr_model.fit(X_train_scaled, y_train)
            
            # Training accuracy
            train_pred = lr_model.predict(X_train_scaled)
            train_r2 = r2_score(y_train, train_pred)
            train_mse = mean_squared_error(y_train, train_pred)
            
            # Validation accuracy
            val_pred = lr_model.predict(X_val_scaled)
            val_r2 = r2_score(y_val, val_pred)
            val_mse = mean_squared_error(y_val, val_pred)
            
            models['linear_regression'] = {
                'model': lr_model,
                'scaler': scaler,
                'type': 'linear_regression'
            }
            
            training_accuracy['linear_regression'] = {'r2': train_r2, 'mse': train_mse}
            validation_accuracy['linear_regression'] = {'r2': val_r2, 'mse': val_mse}
            
            logger.info(f"EC2 Linear Regression - Training R²: {train_r2:.3f}, Validation R²: {val_r2:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to train EC2 Linear Regression model: {e}")
        
        # Train Random Forest model
        try:
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            rf_model.fit(X_train_scaled, y_train)
            
            # Training accuracy
            train_pred = rf_model.predict(X_train_scaled)
            train_r2 = r2_score(y_train, train_pred)
            train_mse = mean_squared_error(y_train, train_pred)
            
            # Validation accuracy
            val_pred = rf_model.predict(X_val_scaled)
            val_r2 = r2_score(y_val, val_pred)
            val_mse = mean_squared_error(y_val, val_pred)
            
            models['random_forest'] = {
                'model': rf_model,
                'scaler': scaler,
                'type': 'random_forest'
            }
            
            training_accuracy['random_forest'] = {'r2': train_r2, 'mse': train_mse}
            validation_accuracy['random_forest'] = {'r2': val_r2, 'mse': val_mse}
            
            logger.info(f"EC2 Random Forest - Training R²: {train_r2:.3f}, Validation R²: {val_r2:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to train EC2 Random Forest model: {e}")
        
        # Store trained models
        self.trained_models['ec2'] = models
        
        # Calculate performance metrics
        performance_metrics = self._calculate_model_performance_metrics(models, X_val_scaled, y_val)
        
        return {
            'training_accuracy': training_accuracy,
            'validation_accuracy': validation_accuracy,
            'performance_metrics': performance_metrics,
            'models_trained': len(models)
        }
    
    def _train_rds_models(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train ML models specifically for RDS instances."""
        logger.info(f"Training RDS models with {len(training_data)} samples")
        
        # Similar structure to EC2 but with RDS-specific features
        features, targets = self._prepare_rds_training_data(training_data)
        
        if len(features) < 10:
            logger.warning("Insufficient RDS training data after preprocessing")
            return {}
        
        X_train, X_val, y_train, y_val = train_test_split(features, targets, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        models = {}
        training_accuracy = {}
        validation_accuracy = {}
        
        # Train Linear Regression for RDS
        try:
            lr_model = LinearRegression()
            lr_model.fit(X_train_scaled, y_train)
            
            train_pred = lr_model.predict(X_train_scaled)
            val_pred = lr_model.predict(X_val_scaled)
            
            models['linear_regression'] = {
                'model': lr_model,
                'scaler': scaler,
                'type': 'linear_regression'
            }
            
            training_accuracy['linear_regression'] = {
                'r2': r2_score(y_train, train_pred),
                'mse': mean_squared_error(y_train, train_pred)
            }
            validation_accuracy['linear_regression'] = {
                'r2': r2_score(y_val, val_pred),
                'mse': mean_squared_error(y_val, val_pred)
            }
            
        except Exception as e:
            logger.error(f"Failed to train RDS Linear Regression model: {e}")
        
        self.trained_models['rds'] = models
        
        performance_metrics = self._calculate_model_performance_metrics(models, X_val_scaled, y_val)
        
        return {
            'training_accuracy': training_accuracy,
            'validation_accuracy': validation_accuracy,
            'performance_metrics': performance_metrics,
            'models_trained': len(models)
        }
    
    def _train_lambda_models(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train ML models specifically for Lambda functions."""
        logger.info(f"Training Lambda models with {len(training_data)} samples")
        
        features, targets = self._prepare_lambda_training_data(training_data)
        
        if len(features) < 10:
            logger.warning("Insufficient Lambda training data after preprocessing")
            return {}
        
        X_train, X_val, y_train, y_val = train_test_split(features, targets, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        models = {}
        training_accuracy = {}
        validation_accuracy = {}
        
        # Train Linear Regression for Lambda
        try:
            lr_model = LinearRegression()
            lr_model.fit(X_train_scaled, y_train)
            
            train_pred = lr_model.predict(X_train_scaled)
            val_pred = lr_model.predict(X_val_scaled)
            
            models['linear_regression'] = {
                'model': lr_model,
                'scaler': scaler,
                'type': 'linear_regression'
            }
            
            training_accuracy['linear_regression'] = {
                'r2': r2_score(y_train, train_pred),
                'mse': mean_squared_error(y_train, train_pred)
            }
            validation_accuracy['linear_regression'] = {
                'r2': r2_score(y_val, val_pred),
                'mse': mean_squared_error(y_val, val_pred)
            }
            
        except Exception as e:
            logger.error(f"Failed to train Lambda Linear Regression model: {e}")
        
        self.trained_models['lambda'] = models
        
        performance_metrics = self._calculate_model_performance_metrics(models, X_val_scaled, y_val)
        
        return {
            'training_accuracy': training_accuracy,
            'validation_accuracy': validation_accuracy,
            'performance_metrics': performance_metrics,
            'models_trained': len(models)
        }
    
    def _prepare_ec2_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare EC2 training data for ML models."""
        features = []
        targets = []
        
        for item in training_data:
            metrics = item.get('utilizationMetrics', {})
            
            # Extract features
            cpu_avg = metrics.get('cpuAvg', 0)
            cpu_max = metrics.get('cpuMax', 0)
            memory_avg = metrics.get('memoryAvg', 0)
            memory_max = metrics.get('memoryMax', 0)
            network_in = metrics.get('networkIn', 0)
            network_out = metrics.get('networkOut', 0)
            
            # Skip if essential features are missing
            if cpu_avg == 0 and cpu_max == 0:
                continue
            
            feature_vector = [
                cpu_avg, cpu_max, memory_avg, memory_max,
                network_in, network_out,
                metrics.get('dataPoints', 0),
                metrics.get('cpuVariance', 0)
            ]
            
            # Target is the optimal CPU utilization (simplified)
            target = min(cpu_avg * 1.2, 80)  # 20% buffer, max 80%
            
            features.append(feature_vector)
            targets.append(target)
        
        return np.array(features), np.array(targets)
    
    def _prepare_rds_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare RDS training data for ML models."""
        features = []
        targets = []
        
        for item in training_data:
            metrics = item.get('utilizationMetrics', {})
            
            cpu_avg = metrics.get('cpuAvg', 0)
            cpu_max = metrics.get('cpuMax', 0)
            connections_avg = metrics.get('connectionsAvg', 0)
            connections_max = metrics.get('connectionsMax', 0)
            
            if cpu_avg == 0 and cpu_max == 0:
                continue
            
            feature_vector = [
                cpu_avg, cpu_max, connections_avg, connections_max,
                metrics.get('dataPoints', 0),
                metrics.get('cpuVariance', 0)
            ]
            
            target = min(cpu_avg * 1.15, 75)  # 15% buffer for databases
            
            features.append(feature_vector)
            targets.append(target)
        
        return np.array(features), np.array(targets)
    
    def _prepare_lambda_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare Lambda training data for ML models."""
        features = []
        targets = []
        
        for item in training_data:
            metrics = item.get('utilizationMetrics', {})
            
            duration_avg = metrics.get('durationAvg', 0)
            duration_max = metrics.get('durationMax', 0)
            memory_used_avg = metrics.get('memoryUsedAvg', 0)
            memory_used_max = metrics.get('memoryUsedMax', 0)
            
            if duration_avg == 0:
                continue
            
            feature_vector = [
                duration_avg, duration_max, memory_used_avg, memory_used_max,
                metrics.get('invocations', 0),
                metrics.get('errors', 0)
            ]
            
            target = memory_used_max * 1.1  # 10% buffer for Lambda
            
            features.append(feature_vector)
            targets.append(target)
        
        return np.array(features), np.array(targets)
    
    def _calculate_model_performance_metrics(self, models: Dict[str, Any], X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics for trained models."""
        performance_metrics = {}
        
        for model_name, model_info in models.items():
            try:
                model = model_info['model']
                predictions = model.predict(X_val)
                
                # Calculate various metrics
                r2 = r2_score(y_val, predictions)
                mse = mean_squared_error(y_val, predictions)
                mae = mean_absolute_error(y_val, predictions)
                rmse = np.sqrt(mse)
                
                # Calculate prediction accuracy within tolerance
                tolerance = 0.1  # 10% tolerance
                accurate_predictions = np.abs(predictions - y_val) <= (y_val * tolerance)
                accuracy_percentage = np.mean(accurate_predictions) * 100
                
                performance_metrics[model_name] = {
                    'r2_score': r2,
                    'mse': mse,
                    'mae': mae,
                    'rmse': rmse,
                    'accuracy_percentage': accuracy_percentage,
                    'prediction_count': len(predictions)
                }
                
            except Exception as e:
                logger.error(f"Failed to calculate metrics for {model_name}: {e}")
                performance_metrics[model_name] = {'error': str(e)}
        
        return performance_metrics
    
    def _validate_ec2_models(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate EC2 models with separate validation dataset."""
        if 'ec2' not in self.trained_models:
            return {'error': 'No trained EC2 models found'}
        
        features, targets = self._prepare_ec2_training_data(validation_data)
        
        if len(features) == 0:
            return {'error': 'No valid validation data'}
        
        validation_results = {}
        models = self.trained_models['ec2']
        
        for model_name, model_info in models.items():
            try:
                model = model_info['model']
                scaler = model_info['scaler']
                
                X_scaled = scaler.transform(features)
                predictions = model.predict(X_scaled)
                
                # Calculate validation metrics
                r2 = r2_score(targets, predictions)
                mse = mean_squared_error(targets, predictions)
                mae = mean_absolute_error(targets, predictions)
                
                validation_results[model_name] = {
                    'r2_score': r2,
                    'mse': mse,
                    'mae': mae,
                    'sample_count': len(targets)
                }
                
            except Exception as e:
                logger.error(f"Validation failed for EC2 {model_name}: {e}")
                validation_results[model_name] = {'error': str(e)}
        
        return {
            'accuracy': validation_results,
            'errors': {},
            'calibration': self._calculate_confidence_calibration(validation_results)
        }
    
    def _validate_rds_models(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate RDS models with separate validation dataset."""
        if 'rds' not in self.trained_models:
            return {'error': 'No trained RDS models found'}
        
        features, targets = self._prepare_rds_training_data(validation_data)
        
        if len(features) == 0:
            return {'error': 'No valid validation data'}
        
        validation_results = {}
        models = self.trained_models['rds']
        
        for model_name, model_info in models.items():
            try:
                model = model_info['model']
                scaler = model_info['scaler']
                
                X_scaled = scaler.transform(features)
                predictions = model.predict(X_scaled)
                
                r2 = r2_score(targets, predictions)
                mse = mean_squared_error(targets, predictions)
                mae = mean_absolute_error(targets, predictions)
                
                validation_results[model_name] = {
                    'r2_score': r2,
                    'mse': mse,
                    'mae': mae,
                    'sample_count': len(targets)
                }
                
            except Exception as e:
                logger.error(f"Validation failed for RDS {model_name}: {e}")
                validation_results[model_name] = {'error': str(e)}
        
        return {
            'accuracy': validation_results,
            'errors': {},
            'calibration': self._calculate_confidence_calibration(validation_results)
        }
    
    def _validate_lambda_models(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate Lambda models with separate validation dataset."""
        if 'lambda' not in self.trained_models:
            return {'error': 'No trained Lambda models found'}
        
        features, targets = self._prepare_lambda_training_data(validation_data)
        
        if len(features) == 0:
            return {'error': 'No valid validation data'}
        
        validation_results = {}
        models = self.trained_models['lambda']
        
        for model_name, model_info in models.items():
            try:
                model = model_info['model']
                scaler = model_info['scaler']
                
                X_scaled = scaler.transform(features)
                predictions = model.predict(X_scaled)
                
                r2 = r2_score(targets, predictions)
                mse = mean_squared_error(targets, predictions)
                mae = mean_absolute_error(targets, predictions)
                
                validation_results[model_name] = {
                    'r2_score': r2,
                    'mse': mse,
                    'mae': mae,
                    'sample_count': len(targets)
                }
                
            except Exception as e:
                logger.error(f"Validation failed for Lambda {model_name}: {e}")
                validation_results[model_name] = {'error': str(e)}
        
        return {
            'accuracy': validation_results,
            'errors': {},
            'calibration': self._calculate_confidence_calibration(validation_results)
        }
    
    def _calculate_confidence_calibration(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence calibration metrics."""
        calibration_metrics = {}
        
        for model_name, results in validation_results.items():
            if 'error' in results:
                continue
            
            r2_score = results.get('r2_score', 0)
            
            # Simple calibration based on R² score
            if r2_score >= 0.8:
                calibration = 'well_calibrated'
                confidence_adjustment = 1.0
            elif r2_score >= 0.6:
                calibration = 'moderately_calibrated'
                confidence_adjustment = 0.8
            else:
                calibration = 'poorly_calibrated'
                confidence_adjustment = 0.6
            
            calibration_metrics[model_name] = {
                'calibration_status': calibration,
                'confidence_adjustment': confidence_adjustment,
                'r2_based_confidence': r2_score
            }
        
        return calibration_metrics
    
    def _save_trained_models(self):
        """Save trained models to disk for persistence."""
        try:
            for resource_type, models in self.trained_models.items():
                model_file = os.path.join(self.model_cache_dir, f"{resource_type}_models.pkl")
                with open(model_file, 'wb') as f:
                    pickle.dump(models, f)
                logger.info(f"Saved {resource_type} models to {model_file}")
        except Exception as e:
            logger.error(f"Failed to save trained models: {e}")
    
    def _load_trained_models(self):
        """Load previously trained models from disk."""
        try:
            for resource_type in ['ec2', 'rds', 'lambda']:
                model_file = os.path.join(self.model_cache_dir, f"{resource_type}_models.pkl")
                if os.path.exists(model_file):
                    with open(model_file, 'rb') as f:
                        self.trained_models[resource_type] = pickle.load(f)
                    logger.info(f"Loaded {resource_type} models from {model_file}")
        except Exception as e:
            logger.error(f"Failed to load trained models: {e}")
    
    def _update_model_metrics(self, validation_results: Dict[str, Any]):
        """Update model metrics with validation results."""
        for resource_type, accuracy in validation_results.get('validation_accuracy', {}).items():
            if resource_type not in self.model_metrics:
                self.model_metrics[resource_type] = {}
            
            self.model_metrics[resource_type].update({
                'last_validated': datetime.utcnow().isoformat(),
                'validation_accuracy': accuracy,
                'validation_sample_count': sum(
                    model_acc.get('sample_count', 0) 
                    for model_acc in accuracy.values() 
                    if isinstance(model_acc, dict)
                )
            })
    
    def _calculate_overall_accuracy(self) -> float:
        """Calculate overall accuracy across all models."""
        if not self.model_metrics:
            return 0.0
        
        total_r2 = 0.0
        model_count = 0
        
        for resource_type, metrics in self.model_metrics.items():
            validation_accuracy = metrics.get('validation_accuracy', {})
            for model_name, accuracy in validation_accuracy.items():
                if isinstance(accuracy, dict) and 'r2_score' in accuracy:
                    total_r2 += accuracy['r2_score']
                    model_count += 1
        
        return total_r2 / model_count if model_count > 0 else 0.0
    
    def _get_model_status(self) -> Dict[str, str]:
        """Get status of all trained models."""
        status = {}
        
        for resource_type in ['ec2', 'rds', 'lambda']:
            if resource_type in self.trained_models:
                model_count = len(self.trained_models[resource_type])
                last_validated = self.model_metrics.get(resource_type, {}).get('last_validated', 'never')
                status[resource_type] = f"{model_count} models trained, last validated: {last_validated}"
            else:
                status[resource_type] = "no models trained"
        
        return status
    
    def _analyze_ec2_ml_rightsizing(self, resource: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Apply ML analysis for EC2 instance right-sizing.
        
        Requirements: 3.2, 3.3 - Generate ML-powered size recommendations with confidence intervals,
                                 estimate cost savings and performance impact
        """
        resource_id = resource.get('resourceId')
        current_instance_type = resource.get('instanceType', '')
        current_cost = resource.get('currentCost', 0)
        
        # Apply multiple ML models for robust prediction
        ml_predictions = self._apply_ml_models_ec2(metrics, current_instance_type)
        
        if not ml_predictions:
            return None
        
        # Determine optimal instance type based on ML predictions
        optimal_config = self._determine_optimal_ec2_config(ml_predictions, current_instance_type)
        
        if not optimal_config or optimal_config['instance_type'] == current_instance_type:
            return None
        
        # Calculate cost savings and performance impact
        cost_analysis = self._calculate_ec2_cost_impact(
            current_instance_type, optimal_config['instance_type'], current_cost
        )
        
        performance_impact = self._assess_ec2_performance_impact(
            metrics, current_instance_type, optimal_config['instance_type']
        )
        
        # Calculate confidence intervals
        confidence_analysis = self._calculate_confidence_intervals(ml_predictions)
        
        return self._create_ml_recommendation(
            resource_id=resource_id,
            resource_type='ec2',
            title=f"ML-powered EC2 right-sizing: {current_instance_type} → {optimal_config['instance_type']}",
            description=f"ML analysis suggests {optimal_config['instance_type']} based on usage patterns",
            current_configuration={
                'instanceType': current_instance_type,
                'monthlyCost': current_cost
            },
            recommended_configuration={
                'instanceType': optimal_config['instance_type'],
                'projectedMonthlyCost': cost_analysis['projected_cost']
            },
            cost_analysis=cost_analysis,
            performance_impact=performance_impact,
            confidence_analysis=confidence_analysis,
            ml_details={
                'modelsUsed': list(ml_predictions.keys()),
                'predictions': ml_predictions,
                'optimalConfig': optimal_config
            },
            resource_data=resource
        )
    
    def _analyze_rds_ml_rightsizing(self, resource: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply ML analysis for RDS instance right-sizing."""
        resource_id = resource.get('resourceId')
        current_instance_class = resource.get('dbInstanceClass', '')
        current_cost = resource.get('currentCost', 0)
        
        # Apply ML models for RDS analysis
        ml_predictions = self._apply_ml_models_rds(metrics, current_instance_class)
        
        if not ml_predictions:
            return None
        
        # Determine optimal RDS configuration
        optimal_config = self._determine_optimal_rds_config(ml_predictions, current_instance_class)
        
        if not optimal_config or optimal_config['instance_class'] == current_instance_class:
            return None
        
        # Calculate cost and performance impact
        cost_analysis = self._calculate_rds_cost_impact(
            current_instance_class, optimal_config['instance_class'], current_cost
        )
        
        performance_impact = self._assess_rds_performance_impact(
            metrics, current_instance_class, optimal_config['instance_class']
        )
        
        confidence_analysis = self._calculate_confidence_intervals(ml_predictions)
        
        return self._create_ml_recommendation(
            resource_id=resource_id,
            resource_type='rds',
            title=f"ML-powered RDS right-sizing: {current_instance_class} → {optimal_config['instance_class']}",
            description=f"ML analysis suggests {optimal_config['instance_class']} based on database usage patterns",
            current_configuration={
                'instanceClass': current_instance_class,
                'monthlyCost': current_cost
            },
            recommended_configuration={
                'instanceClass': optimal_config['instance_class'],
                'projectedMonthlyCost': cost_analysis['projected_cost']
            },
            cost_analysis=cost_analysis,
            performance_impact=performance_impact,
            confidence_analysis=confidence_analysis,
            ml_details={
                'modelsUsed': list(ml_predictions.keys()),
                'predictions': ml_predictions,
                'optimalConfig': optimal_config
            },
            resource_data=resource
        )
    
    def _analyze_lambda_ml_rightsizing(self, resource: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply ML analysis for Lambda function right-sizing."""
        resource_id = resource.get('resourceId')
        current_memory = resource.get('memorySize', 128)
        current_timeout = resource.get('timeout', 3)
        current_cost = resource.get('currentCost', 0)
        
        # Apply ML models for Lambda analysis
        ml_predictions = self._apply_ml_models_lambda(metrics, current_memory, current_timeout)
        
        if not ml_predictions:
            return None
        
        # Determine optimal Lambda configuration
        optimal_config = self._determine_optimal_lambda_config(ml_predictions, current_memory, current_timeout)
        
        if (optimal_config['memory_size'] == current_memory and 
            optimal_config['timeout'] == current_timeout):
            return None
        
        # Calculate cost and performance impact
        cost_analysis = self._calculate_lambda_cost_impact(
            current_memory, optimal_config['memory_size'], current_cost
        )
        
        performance_impact = self._assess_lambda_performance_impact(
            metrics, current_memory, current_timeout, optimal_config
        )
        
        confidence_analysis = self._calculate_confidence_intervals(ml_predictions)
        
        return self._create_ml_recommendation(
            resource_id=resource_id,
            resource_type='lambda',
            title=f"ML-powered Lambda right-sizing: {current_memory}MB → {optimal_config['memory_size']}MB",
            description=f"ML analysis suggests {optimal_config['memory_size']}MB memory, {optimal_config['timeout']}s timeout",
            current_configuration={
                'memorySize': current_memory,
                'timeout': current_timeout,
                'monthlyCost': current_cost
            },
            recommended_configuration={
                'memorySize': optimal_config['memory_size'],
                'timeout': optimal_config['timeout'],
                'projectedMonthlyCost': cost_analysis['projected_cost']
            },
            cost_analysis=cost_analysis,
            performance_impact=performance_impact,
            confidence_analysis=confidence_analysis,
            ml_details={
                'modelsUsed': list(ml_predictions.keys()),
                'predictions': ml_predictions,
                'optimalConfig': optimal_config
            },
            resource_data=resource
        )
    
    def _analyze_ebs_ml_rightsizing(self, resource: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply ML analysis for EBS volume right-sizing."""
        resource_id = resource.get('resourceId')
        current_volume_type = resource.get('volumeType', 'gp2')
        current_size = resource.get('size', 0)
        current_iops = resource.get('iops', 0)
        current_cost = resource.get('currentCost', 0)
        
        # Apply ML models for EBS analysis
        ml_predictions = self._apply_ml_models_ebs(metrics, current_volume_type, current_size)
        
        if not ml_predictions:
            return None
        
        # Determine optimal EBS configuration
        optimal_config = self._determine_optimal_ebs_config(ml_predictions, current_volume_type, current_size)
        
        if (optimal_config['volume_type'] == current_volume_type and 
            optimal_config['size'] == current_size):
            return None
        
        # Calculate cost and performance impact
        cost_analysis = self._calculate_ebs_cost_impact(
            current_volume_type, current_size, optimal_config, current_cost
        )
        
        performance_impact = self._assess_ebs_performance_impact(
            metrics, current_volume_type, optimal_config
        )
        
        confidence_analysis = self._calculate_confidence_intervals(ml_predictions)
        
        return self._create_ml_recommendation(
            resource_id=resource_id,
            resource_type='ebs',
            title=f"ML-powered EBS right-sizing: {current_volume_type} {current_size}GB → {optimal_config['volume_type']} {optimal_config['size']}GB",
            description=f"ML analysis suggests {optimal_config['volume_type']} {optimal_config['size']}GB based on I/O patterns",
            current_configuration={
                'volumeType': current_volume_type,
                'size': current_size,
                'iops': current_iops,
                'monthlyCost': current_cost
            },
            recommended_configuration={
                'volumeType': optimal_config['volume_type'],
                'size': optimal_config['size'],
                'iops': optimal_config.get('iops', 0),
                'projectedMonthlyCost': cost_analysis['projected_cost']
            },
            cost_analysis=cost_analysis,
            performance_impact=performance_impact,
            confidence_analysis=confidence_analysis,
            ml_details={
                'modelsUsed': list(ml_predictions.keys()),
                'predictions': ml_predictions,
                'optimalConfig': optimal_config
            },
            resource_data=resource
        )
    
    def _apply_ml_models_ec2(self, metrics: Dict[str, Any], instance_type: str) -> Dict[str, Any]:
        """
        Apply multiple ML models for EC2 instance analysis.
        
        Returns:
            Dictionary of predictions from different ML models
        """
        predictions = {}
        
        cpu_data = metrics.get('cpu_utilization', [])
        memory_data = metrics.get('memory_utilization', [])
        
        if not cpu_data:
            return predictions
        
        # Use trained models if available
        if 'ec2' in self.trained_models:
            trained_predictions = self._apply_trained_ec2_models(metrics)
            predictions.update(trained_predictions)
        
        # Fallback to statistical methods if no trained models or as additional predictions
        # Linear regression for trend analysis
        try:
            cpu_trend = self._linear_regression_prediction(cpu_data)
            predictions['linear_regression'] = {
                'cpu_trend': cpu_trend,
                'predicted_cpu_avg': cpu_trend['predicted_value'],
                'confidence': cpu_trend['confidence']
            }
        except Exception as e:
            logger.debug(f"Linear regression failed: {e}")
        
        # Moving average for smoothed predictions
        try:
            cpu_ma = self._moving_average_prediction(cpu_data, window=24)  # 24-hour window
            predictions['moving_average'] = {
                'cpu_smoothed': cpu_ma,
                'predicted_cpu_avg': cpu_ma['predicted_value'],
                'confidence': cpu_ma['confidence']
            }
        except Exception as e:
            logger.debug(f"Moving average failed: {e}")
        
        # Seasonal decomposition for pattern recognition
        try:
            if len(cpu_data) >= 168:  # Need at least 1 week of hourly data
                seasonal_analysis = self._seasonal_decomposition(cpu_data)
                predictions['seasonal'] = {
                    'seasonal_pattern': seasonal_analysis,
                    'predicted_cpu_avg': seasonal_analysis['trend_component'],
                    'confidence': seasonal_analysis['confidence']
                }
        except Exception as e:
            logger.debug(f"Seasonal decomposition failed: {e}")
        
        # Percentile-based analysis
        try:
            percentile_analysis = self._percentile_analysis(cpu_data, memory_data)
            predictions['percentile'] = {
                'analysis': percentile_analysis,
                'predicted_cpu_avg': percentile_analysis['cpu_p95'],
                'confidence': percentile_analysis['confidence']
            }
        except Exception as e:
            logger.debug(f"Percentile analysis failed: {e}")
        
        return predictions
    
    def _apply_trained_ec2_models(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Apply trained ML models for EC2 predictions."""
        predictions = {}
        
        if 'ec2' not in self.trained_models:
            return predictions
        
        try:
            # Prepare features for prediction
            cpu_avg = metrics.get('cpu_avg', 0)
            cpu_max = metrics.get('cpu_max', 0)
            memory_avg = metrics.get('memory_avg', 0)
            memory_max = metrics.get('memory_max', 0)
            network_in = metrics.get('network_in', [])
            network_out = metrics.get('network_out', [])
            
            # Calculate network averages
            network_in_avg = np.mean(network_in) if network_in else 0
            network_out_avg = np.mean(network_out) if network_out else 0
            
            feature_vector = np.array([[
                cpu_avg, cpu_max, memory_avg, memory_max,
                network_in_avg, network_out_avg,
                metrics.get('data_points', 0),
                metrics.get('cpu_variance', 0)
            ]])
            
            models = self.trained_models['ec2']
            
            for model_name, model_info in models.items():
                try:
                    model = model_info['model']
                    scaler = model_info['scaler']
                    
                    # Scale features and predict
                    X_scaled = scaler.transform(feature_vector)
                    prediction = model.predict(X_scaled)[0]
                    
                    # Get model confidence from metrics
                    model_metrics = self.model_metrics.get('ec2', {}).get('validation_accuracy', {}).get(model_name, {})
                    confidence = model_metrics.get('r2_score', 0.5) * 100
                    
                    predictions[f'trained_{model_name}'] = {
                        'predicted_cpu_avg': max(0, prediction),
                        'confidence': confidence,
                        'model_type': 'trained_ml'
                    }
                    
                except Exception as e:
                    logger.debug(f"Failed to apply trained {model_name} model: {e}")
            
        except Exception as e:
            logger.debug(f"Failed to apply trained EC2 models: {e}")
        
        return predictions
    
    def _apply_ml_models_rds(self, metrics: Dict[str, Any], instance_class: str) -> Dict[str, Any]:
        """Apply ML models for RDS instance analysis."""
        predictions = {}
        
        cpu_data = metrics.get('cpu_utilization', [])
        memory_data = metrics.get('memory_utilization', [])
        connections_data = metrics.get('connections_history', [])
        
        if not cpu_data:
            return predictions
        
        # Similar ML approaches as EC2 but with RDS-specific considerations
        try:
            cpu_trend = self._linear_regression_prediction(cpu_data)
            predictions['linear_regression'] = {
                'cpu_trend': cpu_trend,
                'predicted_cpu_avg': cpu_trend['predicted_value'],
                'confidence': cpu_trend['confidence']
            }
        except Exception as e:
            logger.debug(f"RDS linear regression failed: {e}")
        
        # Database-specific workload pattern analysis
        try:
            if connections_data:
                workload_pattern = self._analyze_database_workload_pattern(cpu_data, connections_data)
                predictions['workload_pattern'] = {
                    'pattern': workload_pattern,
                    'predicted_cpu_avg': workload_pattern['predicted_cpu'],
                    'confidence': workload_pattern['confidence']
                }
        except Exception as e:
            logger.debug(f"Database workload pattern analysis failed: {e}")
        
        return predictions
    
    def _apply_ml_models_lambda(self, metrics: Dict[str, Any], memory_size: int, timeout: int) -> Dict[str, Any]:
        """Apply ML models for Lambda function analysis."""
        predictions = {}
        
        duration_data = metrics.get('duration_history', [])
        memory_used_data = metrics.get('memory_used_history', [])
        
        if not duration_data:
            return predictions
        
        # Duration-based memory optimization
        try:
            duration_analysis = self._analyze_lambda_duration_patterns(duration_data, timeout)
            predictions['duration_analysis'] = {
                'analysis': duration_analysis,
                'predicted_optimal_timeout': duration_analysis['optimal_timeout'],
                'confidence': duration_analysis['confidence']
            }
        except Exception as e:
            logger.debug(f"Lambda duration analysis failed: {e}")
        
        # Memory utilization optimization
        try:
            if memory_used_data:
                memory_analysis = self._analyze_lambda_memory_patterns(memory_used_data, memory_size)
                predictions['memory_analysis'] = {
                    'analysis': memory_analysis,
                    'predicted_optimal_memory': memory_analysis['optimal_memory'],
                    'confidence': memory_analysis['confidence']
                }
        except Exception as e:
            logger.debug(f"Lambda memory analysis failed: {e}")
        
        return predictions
    
    def _apply_ml_models_ebs(self, metrics: Dict[str, Any], volume_type: str, size: int) -> Dict[str, Any]:
        """Apply ML models for EBS volume analysis."""
        predictions = {}
        
        read_ops_data = metrics.get('disk_read_ops', [])
        write_ops_data = metrics.get('disk_write_ops', [])
        read_bytes_data = metrics.get('disk_read_bytes', [])
        write_bytes_data = metrics.get('disk_write_bytes', [])
        
        if not (read_ops_data or write_ops_data):
            return predictions
        
        # I/O pattern analysis
        try:
            io_analysis = self._analyze_ebs_io_patterns(read_ops_data, write_ops_data, read_bytes_data, write_bytes_data)
            predictions['io_analysis'] = {
                'analysis': io_analysis,
                'predicted_optimal_type': io_analysis['optimal_volume_type'],
                'confidence': io_analysis['confidence']
            }
        except Exception as e:
            logger.debug(f"EBS I/O analysis failed: {e}")
        
        return predictions
    
    def _linear_regression_prediction(self, data: List[float]) -> Dict[str, Any]:
        """Simple linear regression for trend prediction."""
        if len(data) < 10:
            raise ValueError("Insufficient data for linear regression")
        
        x = np.arange(len(data))
        y = np.array(data)
        
        # Calculate linear regression coefficients
        n = len(data)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict next value
        predicted_value = slope * len(data) + intercept
        
        # Calculate R-squared for confidence
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        confidence = max(0, min(100, r_squared * 100))
        
        return {
            'slope': slope,
            'intercept': intercept,
            'predicted_value': max(0, predicted_value),
            'r_squared': r_squared,
            'confidence': confidence
        }
    
    def _moving_average_prediction(self, data: List[float], window: int = 24) -> Dict[str, Any]:
        """Moving average prediction with confidence based on stability."""
        if len(data) < window:
            window = max(3, len(data) // 2)
        
        # Calculate moving averages
        moving_averages = []
        for i in range(window - 1, len(data)):
            ma = np.mean(data[i - window + 1:i + 1])
            moving_averages.append(ma)
        
        if not moving_averages:
            raise ValueError("Cannot calculate moving average")
        
        # Predict next value as average of recent moving averages
        recent_window = min(12, len(moving_averages))
        predicted_value = np.mean(moving_averages[-recent_window:])
        
        # Calculate confidence based on stability of recent moving averages
        if len(moving_averages) >= 2:
            recent_variance = np.var(moving_averages[-recent_window:])
            confidence = max(0, min(100, 100 - (recent_variance * 10)))
        else:
            confidence = 50
        
        return {
            'moving_averages': moving_averages,
            'predicted_value': predicted_value,
            'confidence': confidence,
            'window_size': window
        }
    
    def _seasonal_decomposition(self, data: List[float]) -> Dict[str, Any]:
        """Simple seasonal decomposition for pattern recognition."""
        if len(data) < 168:  # Need at least 1 week of hourly data
            raise ValueError("Insufficient data for seasonal decomposition")
        
        # Assume daily seasonality (24-hour cycle)
        period = 24
        
        # Calculate trend component using moving average
        trend = []
        for i in range(period // 2, len(data) - period // 2):
            trend_value = np.mean(data[i - period // 2:i + period // 2 + 1])
            trend.append(trend_value)
        
        # Calculate seasonal component
        seasonal_pattern = [0] * period
        seasonal_counts = [0] * period
        
        for i, value in enumerate(data):
            if i >= period // 2 and i < len(data) - period // 2:
                trend_index = i - period // 2
                if trend_index < len(trend):
                    detrended = value - trend[trend_index]
                    hour_of_day = i % period
                    seasonal_pattern[hour_of_day] += detrended
                    seasonal_counts[hour_of_day] += 1
        
        # Average seasonal components
        for i in range(period):
            if seasonal_counts[i] > 0:
                seasonal_pattern[i] /= seasonal_counts[i]
        
        # Calculate overall trend
        trend_component = np.mean(trend) if trend else np.mean(data)
        
        # Calculate confidence based on pattern consistency
        if len(trend) > 0:
            trend_variance = np.var(trend)
            confidence = max(0, min(100, 100 - (trend_variance * 5)))
        else:
            confidence = 30
        
        return {
            'trend_component': trend_component,
            'seasonal_pattern': seasonal_pattern,
            'confidence': confidence,
            'period': period
        }
    
    def _percentile_analysis(self, cpu_data: List[float], memory_data: List[float] = None) -> Dict[str, Any]:
        """Percentile-based analysis for resource sizing."""
        if not cpu_data:
            raise ValueError("No CPU data provided")
        
        cpu_percentiles = {
            'p50': np.percentile(cpu_data, 50),
            'p75': np.percentile(cpu_data, 75),
            'p90': np.percentile(cpu_data, 90),
            'p95': np.percentile(cpu_data, 95),
            'p99': np.percentile(cpu_data, 99)
        }
        
        memory_percentiles = {}
        if memory_data:
            memory_percentiles = {
                'p50': np.percentile(memory_data, 50),
                'p75': np.percentile(memory_data, 75),
                'p90': np.percentile(memory_data, 90),
                'p95': np.percentile(memory_data, 95),
                'p99': np.percentile(memory_data, 99)
            }
        
        # Use P95 as the basis for sizing recommendations
        cpu_p95 = cpu_percentiles['p95']
        
        # Calculate confidence based on data distribution
        cpu_variance = np.var(cpu_data)
        confidence = max(0, min(100, 100 - (cpu_variance * 2)))
        
        return {
            'cpu_percentiles': cpu_percentiles,
            'memory_percentiles': memory_percentiles,
            'cpu_p95': cpu_p95,
            'confidence': confidence
        }
    
    def _analyze_database_workload_pattern(self, cpu_data: List[float], connections_data: List[float]) -> Dict[str, Any]:
        """Analyze database-specific workload patterns."""
        if not cpu_data or not connections_data:
            raise ValueError("Insufficient database metrics")
        
        # Correlate CPU usage with connection count
        if len(cpu_data) == len(connections_data):
            correlation = np.corrcoef(cpu_data, connections_data)[0, 1]
        else:
            correlation = 0
        
        # Analyze peak usage patterns
        cpu_avg = np.mean(cpu_data)
        connections_avg = np.mean(connections_data)
        
        # Predict CPU based on connection patterns
        if correlation > 0.5 and connections_avg > 0:
            cpu_per_connection = cpu_avg / connections_avg
            predicted_cpu = cpu_per_connection * connections_avg
        else:
            predicted_cpu = cpu_avg
        
        confidence = max(0, min(100, abs(correlation) * 100))
        
        return {
            'cpu_connection_correlation': correlation,
            'cpu_per_connection': cpu_avg / max(1, connections_avg),
            'predicted_cpu': predicted_cpu,
            'confidence': confidence
        }
    
    def _analyze_lambda_duration_patterns(self, duration_data: List[float], timeout: int) -> Dict[str, Any]:
        """Analyze Lambda duration patterns for timeout optimization."""
        if not duration_data:
            raise ValueError("No duration data provided")
        
        duration_ms = [d for d in duration_data if d > 0]
        if not duration_ms:
            raise ValueError("No valid duration data")
        
        # Calculate duration statistics
        avg_duration = np.mean(duration_ms)
        max_duration = np.max(duration_ms)
        p95_duration = np.percentile(duration_ms, 95)
        
        # Recommend timeout with safety buffer
        safety_buffer = 1.2  # 20% buffer
        optimal_timeout = max(3, int((p95_duration / 1000) * safety_buffer))
        
        # Calculate confidence based on duration consistency
        duration_variance = np.var(duration_ms)
        confidence = max(0, min(100, 100 - (duration_variance / 1000)))
        
        return {
            'avg_duration_ms': avg_duration,
            'max_duration_ms': max_duration,
            'p95_duration_ms': p95_duration,
            'optimal_timeout': optimal_timeout,
            'current_timeout': timeout,
            'confidence': confidence
        }
    
    def _analyze_lambda_memory_patterns(self, memory_used_data: List[float], memory_size: int) -> Dict[str, Any]:
        """Analyze Lambda memory usage patterns for memory optimization."""
        if not memory_used_data:
            raise ValueError("No memory usage data provided")
        
        # Calculate memory statistics
        avg_memory_used = np.mean(memory_used_data)
        max_memory_used = np.max(memory_used_data)
        p95_memory_used = np.percentile(memory_used_data, 95)
        
        # Recommend memory with safety buffer
        safety_buffer = 1.15  # 15% buffer
        optimal_memory = max(128, int(p95_memory_used * safety_buffer))
        
        # Round to valid Lambda memory sizes
        valid_memory_sizes = [128, 192, 256, 320, 384, 448, 512, 576, 640, 704, 768, 832, 896, 960, 1024,
                             1088, 1152, 1216, 1280, 1344, 1408, 1472, 1536, 1600, 1664, 1728, 1792, 1856,
                             1920, 1984, 2048, 2112, 2176, 2240, 2304, 2368, 2432, 2496, 2560, 2624, 2688,
                             2752, 2816, 2880, 2944, 3008]
        
        optimal_memory = min(valid_memory_sizes, key=lambda x: abs(x - optimal_memory))
        
        # Calculate confidence
        memory_variance = np.var(memory_used_data)
        confidence = max(0, min(100, 100 - (memory_variance / 100)))
        
        return {
            'avg_memory_used': avg_memory_used,
            'max_memory_used': max_memory_used,
            'p95_memory_used': p95_memory_used,
            'optimal_memory': optimal_memory,
            'current_memory': memory_size,
            'confidence': confidence
        }
    
    def _analyze_ebs_io_patterns(self, read_ops: List[float], write_ops: List[float], 
                                read_bytes: List[float], write_bytes: List[float]) -> Dict[str, Any]:
        """Analyze EBS I/O patterns for volume type optimization."""
        total_read_ops = sum(read_ops) if read_ops else 0
        total_write_ops = sum(write_ops) if write_ops else 0
        total_read_bytes = sum(read_bytes) if read_bytes else 0
        total_write_bytes = sum(write_bytes) if write_bytes else 0
        
        total_ops = total_read_ops + total_write_ops
        total_bytes = total_read_bytes + total_write_bytes
        
        # Determine optimal volume type based on I/O patterns
        if total_ops == 0:
            optimal_volume_type = 'gp3'  # Default for low I/O
            confidence = 30
        elif total_ops > 16000:  # High IOPS workload
            optimal_volume_type = 'io2'
            confidence = 80
        elif total_ops > 3000:  # Medium IOPS workload
            optimal_volume_type = 'gp3'
            confidence = 70
        else:  # Low IOPS workload
            optimal_volume_type = 'gp3'
            confidence = 60
        
        # Analyze throughput requirements
        avg_throughput_mbps = (total_bytes / len(read_bytes)) / (1024 * 1024) if read_bytes else 0
        
        return {
            'total_read_ops': total_read_ops,
            'total_write_ops': total_write_ops,
            'total_ops': total_ops,
            'avg_throughput_mbps': avg_throughput_mbps,
            'optimal_volume_type': optimal_volume_type,
            'confidence': confidence
        }
    
    def _determine_optimal_ec2_config(self, ml_predictions: Dict[str, Any], current_instance_type: str) -> Optional[Dict[str, Any]]:
        """Determine optimal EC2 configuration based on ML predictions."""
        if not ml_predictions:
            return None
        
        # Aggregate predictions from different models
        cpu_predictions = []
        confidences = []
        
        for model_name, prediction in ml_predictions.items():
            if 'predicted_cpu_avg' in prediction:
                cpu_predictions.append(prediction['predicted_cpu_avg'])
                confidences.append(prediction.get('confidence', 50))
        
        if not cpu_predictions:
            return None
        
        # Weighted average based on confidence
        total_weight = sum(confidences)
        if total_weight > 0:
            weighted_cpu = sum(cpu * conf for cpu, conf in zip(cpu_predictions, confidences)) / total_weight
        else:
            weighted_cpu = np.mean(cpu_predictions)
        
        # Add safety buffer
        safety_buffer = self.ml_thresholds['sizing_parameters']['safety_buffer_percentage'] / 100
        target_cpu = weighted_cpu * (1 + safety_buffer)
        
        # Map to appropriate instance type
        optimal_instance_type = self._map_cpu_to_instance_type(target_cpu, current_instance_type)
        
        return {
            'instance_type': optimal_instance_type,
            'predicted_cpu_utilization': weighted_cpu,
            'target_cpu_with_buffer': target_cpu,
            'confidence': np.mean(confidences)
        }
    
    def _determine_optimal_rds_config(self, ml_predictions: Dict[str, Any], current_instance_class: str) -> Optional[Dict[str, Any]]:
        """Determine optimal RDS configuration based on ML predictions."""
        if not ml_predictions:
            return None
        
        # Similar logic to EC2 but for RDS instance classes
        cpu_predictions = []
        confidences = []
        
        for model_name, prediction in ml_predictions.items():
            if 'predicted_cpu_avg' in prediction:
                cpu_predictions.append(prediction['predicted_cpu_avg'])
                confidences.append(prediction.get('confidence', 50))
        
        if not cpu_predictions:
            return None
        
        total_weight = sum(confidences)
        if total_weight > 0:
            weighted_cpu = sum(cpu * conf for cpu, conf in zip(cpu_predictions, confidences)) / total_weight
        else:
            weighted_cpu = np.mean(cpu_predictions)
        
        # Add safety buffer
        safety_buffer = self.ml_thresholds['sizing_parameters']['safety_buffer_percentage'] / 100
        target_cpu = weighted_cpu * (1 + safety_buffer)
        
        # Map to appropriate RDS instance class
        optimal_instance_class = self._map_cpu_to_rds_instance_class(target_cpu, current_instance_class)
        
        return {
            'instance_class': optimal_instance_class,
            'predicted_cpu_utilization': weighted_cpu,
            'target_cpu_with_buffer': target_cpu,
            'confidence': np.mean(confidences)
        }
    
    def _determine_optimal_lambda_config(self, ml_predictions: Dict[str, Any], current_memory: int, current_timeout: int) -> Dict[str, Any]:
        """Determine optimal Lambda configuration based on ML predictions."""
        optimal_memory = current_memory
        optimal_timeout = current_timeout
        
        # Extract memory recommendations
        if 'memory_analysis' in ml_predictions:
            memory_pred = ml_predictions['memory_analysis']['predicted_optimal_memory']
            if memory_pred and memory_pred != current_memory:
                optimal_memory = memory_pred
        
        # Extract timeout recommendations
        if 'duration_analysis' in ml_predictions:
            timeout_pred = ml_predictions['duration_analysis']['predicted_optimal_timeout']
            if timeout_pred and timeout_pred != current_timeout:
                optimal_timeout = timeout_pred
        
        return {
            'memory_size': optimal_memory,
            'timeout': optimal_timeout
        }
    
    def _determine_optimal_ebs_config(self, ml_predictions: Dict[str, Any], current_volume_type: str, current_size: int) -> Dict[str, Any]:
        """Determine optimal EBS configuration based on ML predictions."""
        optimal_volume_type = current_volume_type
        optimal_size = current_size
        
        # Extract volume type recommendations
        if 'io_analysis' in ml_predictions:
            type_pred = ml_predictions['io_analysis']['predicted_optimal_type']
            if type_pred and type_pred != current_volume_type:
                optimal_volume_type = type_pred
        
        return {
            'volume_type': optimal_volume_type,
            'size': optimal_size
        }
    
    def _map_cpu_to_instance_type(self, target_cpu: float, current_instance_type: str) -> str:
        """Map target CPU utilization to appropriate EC2 instance type."""
        # Simplified mapping - in real implementation, use AWS instance specifications
        instance_cpu_mapping = {
            't3.nano': 5, 't3.micro': 10, 't3.small': 20, 't3.medium': 40,
            't3.large': 80, 't3.xlarge': 160, 't3.2xlarge': 320,
            'm5.large': 80, 'm5.xlarge': 160, 'm5.2xlarge': 320, 'm5.4xlarge': 640,
            'c5.large': 100, 'c5.xlarge': 200, 'c5.2xlarge': 400, 'c5.4xlarge': 800
        }
        
        # Find instance type that can handle target CPU with some headroom
        target_capacity = target_cpu * 1.2  # 20% headroom
        
        suitable_types = [(itype, capacity) for itype, capacity in instance_cpu_mapping.items() 
                         if capacity >= target_capacity]
        
        if suitable_types:
            # Choose the smallest suitable instance type
            return min(suitable_types, key=lambda x: x[1])[0]
        else:
            # If target is too high, return current type
            return current_instance_type
    
    def _map_cpu_to_rds_instance_class(self, target_cpu: float, current_instance_class: str) -> str:
        """Map target CPU utilization to appropriate RDS instance class."""
        # Simplified mapping for RDS instance classes
        rds_cpu_mapping = {
            'db.t3.micro': 10, 'db.t3.small': 20, 'db.t3.medium': 40,
            'db.t3.large': 80, 'db.t3.xlarge': 160, 'db.t3.2xlarge': 320,
            'db.m5.large': 80, 'db.m5.xlarge': 160, 'db.m5.2xlarge': 320,
            'db.r5.large': 80, 'db.r5.xlarge': 160, 'db.r5.2xlarge': 320
        }
        
        target_capacity = target_cpu * 1.2  # 20% headroom
        
        suitable_classes = [(iclass, capacity) for iclass, capacity in rds_cpu_mapping.items() 
                           if capacity >= target_capacity]
        
        if suitable_classes:
            return min(suitable_classes, key=lambda x: x[1])[0]
        else:
            return current_instance_class
    
    def _calculate_ec2_cost_impact(self, current_type: str, recommended_type: str, current_cost: float) -> Dict[str, Any]:
        """Calculate cost impact of EC2 instance type change."""
        # Simplified cost calculation - in real implementation, use AWS Pricing API
        instance_cost_mapping = {
            't3.nano': 3.8, 't3.micro': 7.6, 't3.small': 15.2, 't3.medium': 30.4,
            't3.large': 60.8, 't3.xlarge': 121.6, 't3.2xlarge': 243.2,
            'm5.large': 70.0, 'm5.xlarge': 140.0, 'm5.2xlarge': 280.0,
            'c5.large': 62.0, 'c5.xlarge': 124.0, 'c5.2xlarge': 248.0
        }
        
        current_monthly_cost = instance_cost_mapping.get(current_type, current_cost)
        recommended_monthly_cost = instance_cost_mapping.get(recommended_type, current_cost)
        
        monthly_savings = current_monthly_cost - recommended_monthly_cost
        savings_percentage = (monthly_savings / current_monthly_cost) * 100 if current_monthly_cost > 0 else 0
        
        return {
            'current_cost': current_monthly_cost,
            'projected_cost': recommended_monthly_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'savings_percentage': savings_percentage
        }
    
    def _calculate_rds_cost_impact(self, current_class: str, recommended_class: str, current_cost: float) -> Dict[str, Any]:
        """Calculate cost impact of RDS instance class change."""
        # Simplified RDS cost calculation
        rds_cost_mapping = {
            'db.t3.micro': 12.0, 'db.t3.small': 24.0, 'db.t3.medium': 48.0,
            'db.t3.large': 96.0, 'db.t3.xlarge': 192.0, 'db.t3.2xlarge': 384.0,
            'db.m5.large': 110.0, 'db.m5.xlarge': 220.0, 'db.m5.2xlarge': 440.0
        }
        
        current_monthly_cost = rds_cost_mapping.get(current_class, current_cost)
        recommended_monthly_cost = rds_cost_mapping.get(recommended_class, current_cost)
        
        monthly_savings = current_monthly_cost - recommended_monthly_cost
        savings_percentage = (monthly_savings / current_monthly_cost) * 100 if current_monthly_cost > 0 else 0
        
        return {
            'current_cost': current_monthly_cost,
            'projected_cost': recommended_monthly_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'savings_percentage': savings_percentage
        }
    
    def _calculate_lambda_cost_impact(self, current_memory: int, recommended_memory: int, current_cost: float) -> Dict[str, Any]:
        """Calculate cost impact of Lambda memory change."""
        # Lambda pricing is based on GB-seconds
        # Simplified calculation assuming cost scales linearly with memory
        cost_ratio = recommended_memory / current_memory if current_memory > 0 else 1
        recommended_monthly_cost = current_cost * cost_ratio
        
        monthly_savings = current_cost - recommended_monthly_cost
        savings_percentage = (monthly_savings / current_cost) * 100 if current_cost > 0 else 0
        
        return {
            'current_cost': current_cost,
            'projected_cost': recommended_monthly_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'savings_percentage': savings_percentage
        }
    
    def _calculate_ebs_cost_impact(self, current_type: str, current_size: int, optimal_config: Dict[str, Any], current_cost: float) -> Dict[str, Any]:
        """Calculate cost impact of EBS configuration change."""
        # Simplified EBS cost calculation
        ebs_cost_per_gb = {
            'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125, 'st1': 0.045, 'sc1': 0.025
        }
        
        current_monthly_cost = current_size * ebs_cost_per_gb.get(current_type, 0.10)
        recommended_monthly_cost = optimal_config['size'] * ebs_cost_per_gb.get(optimal_config['volume_type'], 0.10)
        
        monthly_savings = current_monthly_cost - recommended_monthly_cost
        savings_percentage = (monthly_savings / current_monthly_cost) * 100 if current_monthly_cost > 0 else 0
        
        return {
            'current_cost': current_monthly_cost,
            'projected_cost': recommended_monthly_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'savings_percentage': savings_percentage
        }
    
    def _assess_ec2_performance_impact(self, metrics: Dict[str, Any], current_type: str, recommended_type: str) -> Dict[str, Any]:
        """Assess performance impact of EC2 instance type change."""
        # Simplified performance impact assessment
        current_cpu_avg = metrics.get('cpu_avg', 0)
        current_cpu_max = metrics.get('cpu_max', 0)
        
        # Estimate performance impact based on instance type change
        performance_headroom = self.ml_thresholds['performance_impact']['cpu_headroom_percentage']
        
        if recommended_type == current_type:
            impact_level = "NONE"
            impact_description = "No performance impact expected"
        elif self._is_smaller_instance_type(recommended_type, current_type):
            if current_cpu_max > (100 - performance_headroom):
                impact_level = "HIGH"
                impact_description = "Potential performance degradation during peak usage"
            else:
                impact_level = "LOW"
                impact_description = "Minimal performance impact expected"
        else:
            impact_level = "POSITIVE"
            impact_description = "Performance improvement expected"
        
        return {
            'impact_level': impact_level,
            'impact_description': impact_description,
            'current_cpu_avg': current_cpu_avg,
            'current_cpu_max': current_cpu_max,
            'performance_headroom': performance_headroom
        }
    
    def _assess_rds_performance_impact(self, metrics: Dict[str, Any], current_class: str, recommended_class: str) -> Dict[str, Any]:
        """Assess performance impact of RDS instance class change."""
        current_cpu_avg = metrics.get('cpu_avg', 0)
        current_cpu_max = metrics.get('cpu_max', 0)
        
        performance_headroom = self.ml_thresholds['performance_impact']['cpu_headroom_percentage']
        
        if recommended_class == current_class:
            impact_level = "NONE"
            impact_description = "No performance impact expected"
        elif self._is_smaller_rds_instance_class(recommended_class, current_class):
            if current_cpu_max > (100 - performance_headroom):
                impact_level = "HIGH"
                impact_description = "Potential database performance degradation during peak usage"
            else:
                impact_level = "MEDIUM"
                impact_description = "Monitor database performance after change"
        else:
            impact_level = "POSITIVE"
            impact_description = "Database performance improvement expected"
        
        return {
            'impact_level': impact_level,
            'impact_description': impact_description,
            'current_cpu_avg': current_cpu_avg,
            'current_cpu_max': current_cpu_max,
            'performance_headroom': performance_headroom
        }
    
    def _assess_lambda_performance_impact(self, metrics: Dict[str, Any], current_memory: int, current_timeout: int, optimal_config: Dict[str, Any]) -> Dict[str, Any]:
        """Assess performance impact of Lambda configuration change."""
        recommended_memory = optimal_config['memory_size']
        recommended_timeout = optimal_config['timeout']
        
        avg_duration = metrics.get('avg_duration', 0)
        max_duration = metrics.get('max_duration', 0)
        
        impact_factors = []
        
        if recommended_memory < current_memory:
            impact_factors.append("Memory reduction may increase execution time")
        elif recommended_memory > current_memory:
            impact_factors.append("Memory increase will improve execution time")
        
        if recommended_timeout < current_timeout:
            if max_duration > (recommended_timeout * 1000 * 0.8):
                impact_factors.append("Timeout reduction may cause function timeouts")
            else:
                impact_factors.append("Timeout reduction is safe based on usage patterns")
        
        if impact_factors:
            impact_level = "MEDIUM" if any("may cause" in factor for factor in impact_factors) else "LOW"
            impact_description = "; ".join(impact_factors)
        else:
            impact_level = "NONE"
            impact_description = "No significant performance impact expected"
        
        return {
            'impact_level': impact_level,
            'impact_description': impact_description,
            'impact_factors': impact_factors,
            'avg_duration_ms': avg_duration,
            'max_duration_ms': max_duration
        }
    
    def _assess_ebs_performance_impact(self, metrics: Dict[str, Any], current_type: str, optimal_config: Dict[str, Any]) -> Dict[str, Any]:
        """Assess performance impact of EBS configuration change."""
        recommended_type = optimal_config['volume_type']
        
        # EBS performance characteristics
        ebs_performance = {
            'gp2': {'iops': 3000, 'throughput': 125},
            'gp3': {'iops': 3000, 'throughput': 125},
            'io1': {'iops': 64000, 'throughput': 1000},
            'io2': {'iops': 64000, 'throughput': 1000},
            'st1': {'iops': 500, 'throughput': 500},
            'sc1': {'iops': 250, 'throughput': 250}
        }
        
        current_perf = ebs_performance.get(current_type, {'iops': 3000, 'throughput': 125})
        recommended_perf = ebs_performance.get(recommended_type, {'iops': 3000, 'throughput': 125})
        
        if recommended_perf['iops'] < current_perf['iops']:
            impact_level = "MEDIUM"
            impact_description = f"IOPS reduction from {current_perf['iops']} to {recommended_perf['iops']}"
        elif recommended_perf['iops'] > current_perf['iops']:
            impact_level = "POSITIVE"
            impact_description = f"IOPS improvement from {current_perf['iops']} to {recommended_perf['iops']}"
        else:
            impact_level = "NONE"
            impact_description = "No significant performance impact expected"
        
        return {
            'impact_level': impact_level,
            'impact_description': impact_description,
            'current_iops': current_perf['iops'],
            'recommended_iops': recommended_perf['iops'],
            'current_throughput': current_perf['throughput'],
            'recommended_throughput': recommended_perf['throughput']
        }
    
    def _calculate_confidence_intervals(self, ml_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate confidence intervals for ML recommendations.
        
        Requirements: 3.2 - Generate ML-powered size recommendations with confidence intervals
        """
        confidences = []
        predictions = []
        
        for model_name, prediction in ml_predictions.items():
            if 'confidence' in prediction:
                confidences.append(prediction['confidence'])
            if 'predicted_cpu_avg' in prediction:
                predictions.append(prediction['predicted_cpu_avg'])
        
        if not confidences:
            return {
                'overall_confidence': 50.0,
                'confidence_level': ConfidenceLevel.MEDIUM.value,
                'confidence_interval': {'lower': 0, 'upper': 100}
            }
        
        # Calculate overall confidence as weighted average
        overall_confidence = np.mean(confidences)
        
        # Determine confidence level
        thresholds = self.ml_thresholds['confidence_scoring']
        if overall_confidence >= thresholds['high_confidence_threshold']:
            confidence_level = ConfidenceLevel.HIGH.value
        elif overall_confidence >= thresholds['medium_confidence_threshold']:
            confidence_level = ConfidenceLevel.MEDIUM.value
        else:
            confidence_level = ConfidenceLevel.LOW.value
        
        # Calculate confidence interval for predictions
        if predictions:
            pred_mean = np.mean(predictions)
            pred_std = np.std(predictions) if len(predictions) > 1 else pred_mean * 0.1
            
            # 95% confidence interval
            confidence_interval = {
                'lower': max(0, pred_mean - 1.96 * pred_std),
                'upper': pred_mean + 1.96 * pred_std
            }
        else:
            confidence_interval = {'lower': 0, 'upper': 100}
        
        return {
            'overall_confidence': overall_confidence,
            'confidence_level': confidence_level,
            'confidence_interval': confidence_interval,
            'model_confidences': {model: pred.get('confidence', 50) for model, pred in ml_predictions.items()}
        }
    
    def _is_smaller_instance_type(self, type1: str, type2: str) -> bool:
        """Check if type1 is smaller than type2."""
        # Simplified comparison - in real implementation, use AWS instance specifications
        size_order = ['nano', 'micro', 'small', 'medium', 'large', 'xlarge', '2xlarge', '4xlarge', '8xlarge']
        
        def get_size_index(instance_type):
            for i, size in enumerate(size_order):
                if size in instance_type:
                    return i
            return len(size_order)
        
        return get_size_index(type1) < get_size_index(type2)
    
    def _is_smaller_rds_instance_class(self, class1: str, class2: str) -> bool:
        """Check if class1 is smaller than class2."""
        return self._is_smaller_instance_type(class1, class2)
    
    def _prioritize_ml_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize ML recommendations by confidence and savings potential."""
        def priority_score(rec):
            confidence = rec.get('confidenceAnalysis', {}).get('overall_confidence', 50)
            savings = rec.get('costAnalysis', {}).get('monthly_savings', 0)
            
            # Normalize scores (0-100)
            confidence_score = confidence
            savings_score = min(100, (savings / 1000) * 100)  # Normalize to $1000 max
            
            # Weighted priority score
            return (confidence_score * 0.6) + (savings_score * 0.4)
        
        return sorted(recommendations, key=priority_score, reverse=True)
    
    def _create_ml_recommendation(self, resource_id: str, resource_type: str, title: str, 
                                 description: str, current_configuration: Dict[str, Any],
                                 recommended_configuration: Dict[str, Any], cost_analysis: Dict[str, Any],
                                 performance_impact: Dict[str, Any], confidence_analysis: Dict[str, Any],
                                 ml_details: Dict[str, Any], resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a standardized ML recommendation record.
        
        Requirements: 3.3 - Estimate cost savings and performance impact
        """
        # Determine risk level based on performance impact and confidence
        performance_impact_level = performance_impact.get('impact_level', 'MEDIUM')
        confidence_level = confidence_analysis.get('confidence_level', 'MEDIUM')
        
        if performance_impact_level == 'HIGH':
            risk_level = RiskLevel.HIGH.value
        elif performance_impact_level == 'MEDIUM' or confidence_level == 'LOW':
            risk_level = RiskLevel.MEDIUM.value
        else:
            risk_level = RiskLevel.LOW.value
        
        # Determine implementation effort
        if resource_type == 'lambda':
            implementation_effort = "Low"
        elif resource_type in ['ec2', 'rds']:
            implementation_effort = "High"
        else:
            implementation_effort = "Medium"
        
        return {
            'recommendationId': f"ml-{resource_type}-{resource_id}-{int(datetime.utcnow().timestamp())}",
            'resourceId': resource_id,
            'resourceType': resource_type,
            'recommendationType': 'ml_rightsizing',
            'title': title,
            'description': description,
            'currentConfiguration': current_configuration,
            'recommendedConfiguration': recommended_configuration,
            'costAnalysis': cost_analysis,
            'performanceImpact': performance_impact,
            'confidenceAnalysis': confidence_analysis,
            'estimatedMonthlySavings': cost_analysis.get('monthly_savings', 0),
            'estimatedAnnualSavings': cost_analysis.get('annual_savings', 0),
            'savingsPercentage': cost_analysis.get('savings_percentage', 0),
            'confidenceLevel': confidence_analysis.get('confidence_level', 'MEDIUM'),
            'riskLevel': risk_level,
            'implementationEffort': implementation_effort,
            'mlDetails': ml_details,
            'recommendedAction': f"Resize {resource_type} resource based on ML analysis",
            'rollbackCapability': True,
            'validationRequired': True,
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region,
            'resourceData': resource_data
        }
    
    def validate_post_change_performance(self, resource_id: str, resource_type: str, 
                                       pre_change_metrics: Dict[str, Any], 
                                       post_change_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate performance after right-sizing changes and adjust recommendations.
        
        This method implements the learning loop for continuous improvement:
        - Compare pre and post-change performance
        - Validate that changes met expectations
        - Update ML models based on outcomes
        - Generate feedback for future recommendations
        
        Requirements: 3.5 - Monitor post-change and adjust recommendations based on outcomes
        """
        logger.info(f"Validating post-change performance for {resource_type} resource {resource_id}")
        
        validation_results = {
            'resourceId': resource_id,
            'resourceType': resource_type,
            'validationTimestamp': datetime.utcnow().isoformat(),
            'performanceComparison': {},
            'expectationsMet': False,
            'performanceImpact': {},
            'modelFeedback': {},
            'recommendationAdjustments': [],
            'learningOutcomes': []
        }
        
        try:
            # Compare performance metrics
            performance_comparison = self._compare_performance_metrics(
                pre_change_metrics, post_change_metrics, resource_type
            )
            validation_results['performanceComparison'] = performance_comparison
            
            # Validate expectations
            expectations_met = self._validate_performance_expectations(
                performance_comparison, resource_type
            )
            validation_results['expectationsMet'] = expectations_met
            
            # Assess performance impact
            performance_impact = self._assess_actual_performance_impact(
                performance_comparison, resource_type
            )
            validation_results['performanceImpact'] = performance_impact
            
            # Generate model feedback
            model_feedback = self._generate_model_feedback(
                resource_id, resource_type, performance_comparison, expectations_met
            )
            validation_results['modelFeedback'] = model_feedback
            
            # Update ML models with new data
            self._update_models_with_feedback(resource_type, model_feedback)
            
            # Generate recommendation adjustments
            adjustments = self._generate_recommendation_adjustments(
                resource_type, performance_comparison, expectations_met
            )
            validation_results['recommendationAdjustments'] = adjustments
            
            # Extract learning outcomes
            learning_outcomes = self._extract_learning_outcomes(
                resource_type, performance_comparison, expectations_met
            )
            validation_results['learningOutcomes'] = learning_outcomes
            
            logger.info(f"Performance validation completed for {resource_id}. "
                       f"Expectations met: {expectations_met}")
            
        except Exception as e:
            logger.error(f"Error validating post-change performance for {resource_id}: {e}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    def _compare_performance_metrics(self, pre_metrics: Dict[str, Any], 
                                   post_metrics: Dict[str, Any], 
                                   resource_type: str) -> Dict[str, Any]:
        """Compare pre and post-change performance metrics."""
        comparison = {
            'cpu_utilization': {},
            'memory_utilization': {},
            'response_time': {},
            'throughput': {},
            'error_rate': {},
            'cost': {}
        }
        
        # CPU utilization comparison
        pre_cpu = pre_metrics.get('cpu_avg', 0)
        post_cpu = post_metrics.get('cpu_avg', 0)
        comparison['cpu_utilization'] = {
            'pre_change': pre_cpu,
            'post_change': post_cpu,
            'change_percentage': ((post_cpu - pre_cpu) / max(pre_cpu, 1)) * 100,
            'improvement': post_cpu < pre_cpu * 1.1  # Allow 10% increase
        }
        
        # Memory utilization comparison
        pre_memory = pre_metrics.get('memory_avg', 0)
        post_memory = post_metrics.get('memory_avg', 0)
        comparison['memory_utilization'] = {
            'pre_change': pre_memory,
            'post_change': post_memory,
            'change_percentage': ((post_memory - pre_memory) / max(pre_memory, 1)) * 100,
            'improvement': post_memory < pre_memory * 1.1
        }
        
        # Response time comparison (for applicable resources)
        if resource_type in ['lambda', 'rds']:
            pre_response = pre_metrics.get('response_time_avg', 0)
            post_response = post_metrics.get('response_time_avg', 0)
            comparison['response_time'] = {
                'pre_change': pre_response,
                'post_change': post_response,
                'change_percentage': ((post_response - pre_response) / max(pre_response, 1)) * 100,
                'improvement': post_response <= pre_response * 1.05  # Allow 5% increase
            }
        
        # Cost comparison
        pre_cost = pre_metrics.get('cost', 0)
        post_cost = post_metrics.get('cost', 0)
        comparison['cost'] = {
            'pre_change': pre_cost,
            'post_change': post_cost,
            'savings': pre_cost - post_cost,
            'savings_percentage': ((pre_cost - post_cost) / max(pre_cost, 1)) * 100,
            'improvement': post_cost < pre_cost
        }
        
        return comparison
    
    def _validate_performance_expectations(self, performance_comparison: Dict[str, Any], 
                                         resource_type: str) -> bool:
        """Validate if performance changes met expectations."""
        expectations_met = True
        
        # Check CPU utilization expectations
        cpu_improvement = performance_comparison.get('cpu_utilization', {}).get('improvement', False)
        if not cpu_improvement:
            expectations_met = False
        
        # Check memory utilization expectations
        memory_improvement = performance_comparison.get('memory_utilization', {}).get('improvement', False)
        if not memory_improvement:
            expectations_met = False
        
        # Check response time expectations (if applicable)
        if 'response_time' in performance_comparison:
            response_improvement = performance_comparison['response_time'].get('improvement', False)
            if not response_improvement:
                expectations_met = False
        
        # Check cost savings expectations
        cost_savings = performance_comparison.get('cost', {}).get('savings', 0)
        if cost_savings <= 0:
            expectations_met = False
        
        return expectations_met
    
    def _assess_actual_performance_impact(self, performance_comparison: Dict[str, Any], 
                                        resource_type: str) -> Dict[str, Any]:
        """Assess the actual performance impact of the changes."""
        impact_assessment = {
            'overall_impact': 'neutral',
            'cpu_impact': 'neutral',
            'memory_impact': 'neutral',
            'cost_impact': 'neutral',
            'response_time_impact': 'neutral',
            'risk_level': 'low'
        }
        
        # Assess CPU impact
        cpu_change = performance_comparison.get('cpu_utilization', {}).get('change_percentage', 0)
        if cpu_change > 20:
            impact_assessment['cpu_impact'] = 'negative'
            impact_assessment['risk_level'] = 'high'
        elif cpu_change > 10:
            impact_assessment['cpu_impact'] = 'moderate_negative'
            impact_assessment['risk_level'] = 'medium'
        elif cpu_change < -5:
            impact_assessment['cpu_impact'] = 'positive'
        
        # Assess memory impact
        memory_change = performance_comparison.get('memory_utilization', {}).get('change_percentage', 0)
        if memory_change > 15:
            impact_assessment['memory_impact'] = 'negative'
            if impact_assessment['risk_level'] == 'low':
                impact_assessment['risk_level'] = 'medium'
        elif memory_change < -5:
            impact_assessment['memory_impact'] = 'positive'
        
        # Assess cost impact
        cost_savings = performance_comparison.get('cost', {}).get('savings', 0)
        if cost_savings > 0:
            impact_assessment['cost_impact'] = 'positive'
        elif cost_savings < 0:
            impact_assessment['cost_impact'] = 'negative'
        
        # Assess response time impact (if applicable)
        if 'response_time' in performance_comparison:
            response_change = performance_comparison['response_time'].get('change_percentage', 0)
            if response_change > 10:
                impact_assessment['response_time_impact'] = 'negative'
                impact_assessment['risk_level'] = 'high'
            elif response_change < -5:
                impact_assessment['response_time_impact'] = 'positive'
        
        # Determine overall impact
        positive_impacts = sum(1 for impact in impact_assessment.values() 
                             if isinstance(impact, str) and 'positive' in impact)
        negative_impacts = sum(1 for impact in impact_assessment.values() 
                             if isinstance(impact, str) and 'negative' in impact)
        
        if positive_impacts > negative_impacts:
            impact_assessment['overall_impact'] = 'positive'
        elif negative_impacts > positive_impacts:
            impact_assessment['overall_impact'] = 'negative'
        
        return impact_assessment
    
    def _generate_model_feedback(self, resource_id: str, resource_type: str, 
                               performance_comparison: Dict[str, Any], 
                               expectations_met: bool) -> Dict[str, Any]:
        """Generate feedback for ML model improvement."""
        feedback = {
            'resourceId': resource_id,
            'resourceType': resource_type,
            'predictionAccuracy': 'unknown',
            'modelPerformance': {},
            'adjustmentNeeded': False,
            'feedbackType': 'validation',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Assess prediction accuracy
        if expectations_met:
            feedback['predictionAccuracy'] = 'good'
            feedback['modelPerformance']['accuracy_score'] = 0.8
        else:
            feedback['predictionAccuracy'] = 'poor'
            feedback['modelPerformance']['accuracy_score'] = 0.3
            feedback['adjustmentNeeded'] = True
        
        # Analyze specific prediction errors
        cpu_change = performance_comparison.get('cpu_utilization', {}).get('change_percentage', 0)
        cost_savings = performance_comparison.get('cost', {}).get('savings', 0)
        
        feedback['modelPerformance']['cpu_prediction_error'] = abs(cpu_change)
        feedback['modelPerformance']['cost_prediction_error'] = abs(cost_savings)
        
        # Generate specific feedback for model adjustment
        if feedback['adjustmentNeeded']:
            feedback['adjustmentRecommendations'] = []
            
            if abs(cpu_change) > 15:
                feedback['adjustmentRecommendations'].append(
                    "Improve CPU utilization prediction accuracy"
                )
            
            if cost_savings <= 0:
                feedback['adjustmentRecommendations'].append(
                    "Recalibrate cost savings estimation"
                )
            
            if 'response_time' in performance_comparison:
                response_change = performance_comparison['response_time'].get('change_percentage', 0)
                if abs(response_change) > 10:
                    feedback['adjustmentRecommendations'].append(
                        "Improve response time impact prediction"
                    )
        
        return feedback
    
    def _update_models_with_feedback(self, resource_type: str, feedback: Dict[str, Any]):
        """Update ML models based on validation feedback."""
        if not feedback.get('adjustmentNeeded', False):
            return
        
        try:
            # Update model metrics with feedback
            if resource_type not in self.model_metrics:
                self.model_metrics[resource_type] = {}
            
            # Track prediction accuracy over time
            accuracy_history = self.model_metrics[resource_type].get('accuracy_history', [])
            accuracy_history.append({
                'timestamp': feedback['timestamp'],
                'accuracy_score': feedback['modelPerformance']['accuracy_score'],
                'resource_id': feedback['resourceId']
            })
            
            # Keep only recent history (last 100 validations)
            if len(accuracy_history) > 100:
                accuracy_history = accuracy_history[-100:]
            
            self.model_metrics[resource_type]['accuracy_history'] = accuracy_history
            
            # Calculate rolling accuracy
            recent_scores = [entry['accuracy_score'] for entry in accuracy_history[-20:]]
            rolling_accuracy = np.mean(recent_scores) if recent_scores else 0.5
            
            self.model_metrics[resource_type]['rolling_accuracy'] = rolling_accuracy
            self.model_metrics[resource_type]['last_feedback'] = feedback['timestamp']
            
            # Trigger model retraining if accuracy drops significantly
            if rolling_accuracy < 0.6:
                logger.warning(f"Model accuracy for {resource_type} dropped to {rolling_accuracy:.2f}. "
                             "Consider retraining with more data.")
                self.model_metrics[resource_type]['retraining_recommended'] = True
            
        except Exception as e:
            logger.error(f"Error updating models with feedback: {e}")
    
    def _generate_recommendation_adjustments(self, resource_type: str, 
                                           performance_comparison: Dict[str, Any], 
                                           expectations_met: bool) -> List[str]:
        """Generate adjustments for future recommendations."""
        adjustments = []
        
        if not expectations_met:
            # CPU utilization adjustments
            cpu_change = performance_comparison.get('cpu_utilization', {}).get('change_percentage', 0)
            if cpu_change > 15:
                adjustments.append(
                    f"Increase safety buffer for {resource_type} CPU predictions by 5%"
                )
            
            # Memory utilization adjustments
            memory_change = performance_comparison.get('memory_utilization', {}).get('change_percentage', 0)
            if memory_change > 10:
                adjustments.append(
                    f"Increase safety buffer for {resource_type} memory predictions by 3%"
                )
            
            # Cost savings adjustments
            cost_savings = performance_comparison.get('cost', {}).get('savings', 0)
            if cost_savings <= 0:
                adjustments.append(
                    f"Reduce cost savings estimates for {resource_type} by 20%"
                )
            
            # Response time adjustments
            if 'response_time' in performance_comparison:
                response_change = performance_comparison['response_time'].get('change_percentage', 0)
                if response_change > 10:
                    adjustments.append(
                        f"Add response time penalty factor for {resource_type} recommendations"
                    )
        
        # General adjustments based on resource type
        if resource_type == 'ec2' and not expectations_met:
            adjustments.append("Consider instance family constraints in EC2 recommendations")
        elif resource_type == 'rds' and not expectations_met:
            adjustments.append("Account for database connection overhead in RDS sizing")
        elif resource_type == 'lambda' and not expectations_met:
            adjustments.append("Improve Lambda cold start impact estimation")
        
        return adjustments
    
    def _extract_learning_outcomes(self, resource_type: str, 
                                 performance_comparison: Dict[str, Any], 
                                 expectations_met: bool) -> List[str]:
        """Extract learning outcomes from validation results."""
        outcomes = []
        
        if expectations_met:
            outcomes.append(f"ML model for {resource_type} performed well - maintain current approach")
            
            # Identify successful patterns
            cpu_improvement = performance_comparison.get('cpu_utilization', {}).get('improvement', False)
            cost_savings = performance_comparison.get('cost', {}).get('savings', 0)
            
            if cpu_improvement and cost_savings > 0:
                outcomes.append(f"Successful optimization pattern identified for {resource_type}")
        else:
            outcomes.append(f"ML model for {resource_type} needs improvement")
            
            # Identify failure patterns
            cpu_change = performance_comparison.get('cpu_utilization', {}).get('change_percentage', 0)
            if cpu_change > 20:
                outcomes.append(f"CPU utilization predictions for {resource_type} are too aggressive")
            
            cost_savings = performance_comparison.get('cost', {}).get('savings', 0)
            if cost_savings <= 0:
                outcomes.append(f"Cost savings calculations for {resource_type} are overestimated")
        
        # Resource-specific learning outcomes
        if resource_type == 'ec2':
            outcomes.append("EC2 right-sizing requires careful consideration of burst capacity")
        elif resource_type == 'rds':
            outcomes.append("RDS optimization must account for connection pooling effects")
        elif resource_type == 'lambda':
            outcomes.append("Lambda memory optimization significantly impacts execution time")
        
        return outcomes
    
    def get_ml_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the ML right-sizing engine."""
        return {
            'engine_status': 'active',
            'initialized_region': self.region,
            'trained_models': list(self.trained_models.keys()),
            'model_count': len(self.trained_models),
            'model_metrics': self.model_metrics,
            'cache_status': {
                'model_cache_dir': self.model_cache_dir,
                'historical_data_cache_size': len(self.historical_data_cache),
                'trend_detection_cache_size': len(self.trend_detection_cache)
            },
            'thresholds': self.ml_thresholds,
            'last_updated': datetime.utcnow().isoformat()
        }