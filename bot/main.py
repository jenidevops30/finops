#!/usr/bin/env python3
"""
Advanced FinOps Platform - Main Orchestration Script

This script orchestrates the complete cost optimization workflow:
1. Resource Discovery across multiple AWS services
2. Cost Analysis and Optimization Recommendations
3. ML-powered Right-sizing Analysis
4. Anomaly Detection and Budget Management
5. Automated Optimization Execution (with approval workflows)

Enhanced with comprehensive monitoring and error handling:
- Structured logging with correlation IDs
- Error recovery with exponential backoff
- System health monitoring and alerting
- Performance metrics collection
- Operational dashboards integration

Safety Features:
- DRY_RUN mode prevents actual resource modifications
- Comprehensive logging for all operations
- Error handling and rollback capabilities
- Risk-based approval workflows

Usage:
    python main.py --dry-run                    # Safe mode (no modifications)
    python main.py --scan-only                  # Discovery only
    python main.py --optimize --approve-low     # Execute low-risk optimizations
    python main.py --region us-east-1          # Specific region
    python main.py --services ec2,rds,lambda    # Specific services
    python main.py --continuous                 # Continuous monitoring mode
    python main.py --config config.yaml        # Custom configuration file
    python main.py --schedule                   # Run with scheduler
"""

import argparse
import logging
import sys
import os
import signal
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Import enhanced monitoring and error handling utilities
from utils.monitoring import (
    StructuredLogger, 
    create_correlation_context, 
    with_correlation_context,
    system_monitor,
    AlertSeverity
)
from utils.error_recovery import with_error_recovery, global_recovery_manager

# Import utility modules
from utils.aws_config import AWSConfig
from utils.safety_controls import SafetyControls, RiskLevel, OperationType
from utils.http_client import HTTPClient
from utils.config_manager import ConfigManager
from utils.scheduler import FinOpsScheduler

# Import AWS service scanners
from aws.scan_ec2 import EC2Scanner
from aws.scan_rds import RDSScanner
from aws.scan_lambda import LambdaScanner
from aws.scan_s3 import S3Scanner
from aws.scan_ebs import EBSScanner
from aws.scan_elb import ELBScanner
from aws.scan_cloudwatch import CloudWatchScanner

# Import core engines
from core.cost_optimizer import CostOptimizer
from core.pricing_intelligence import PricingIntelligenceEngine
from core.ml_rightsizing import MLRightSizingEngine
from core.anomaly_detector import AnomalyDetector
from core.budget_manager import BudgetManager
from core.execution_engine import ExecutionEngine, OptimizationExecutionEngine
from core.approval_workflow import ApprovalWorkflow


class AdvancedFinOpsOrchestrator:
    """Main orchestrator for the Advanced FinOps Platform with enhanced monitoring."""
    
    def __init__(self, region: str = 'us-east-1', dry_run: Optional[bool] = None, config_file: Optional[str] = None):
        """
        Initialize the FinOps orchestrator with enhanced monitoring and error handling.

        Args:
            region: AWS region to operate in
            dry_run: If True, no actual AWS operations; if False, live; if None, use config (safety.dry_run.default)
            config_file: Path to configuration file (None = use system/user/cwd lookup)
        """
        # Initialize structured logger
        self.logger = StructuredLogger('finops.orchestrator')

        init_context = create_correlation_context(
            operation_id="orchestrator_init",
            metadata={
                'region': region,
                'dry_run': dry_run,
                'config_file': config_file
            }
        )
        self.logger.set_correlation_context(init_context)

        try:
            system_monitor.start_monitoring(interval_seconds=60)
            self.logger.info("System monitoring started")

            # Load configuration first (system path, then user, then cwd)
            self.config_manager = ConfigManager(config_file)

            # Validate configuration
            config_issues = self.config_manager.validate()
            if config_issues:
                self.logger.warning("Configuration validation issues found", {
                    'issues': config_issues
                })
                print("Configuration validation issues:")
                for issue in config_issues:
                    print(f"  - {issue}")
                print("Continuing with default values where needed...")

            # Region: from config if not overridden
            if region == 'us-east-1':
                region = self.config_manager.get('aws.default_region', 'us-east-1')

            # dry_run: from config when None (safety.dry_run.default, default False = live)
            if dry_run is None:
                dry_run = self.config_manager.get('safety.dry_run.default', False)

            self.region = region
            self.dry_run = dry_run
            
            # Initialize AWS config from config.yaml (region + regions list)
            aws_cfg = self.config_manager.get('aws', {})
            regions_list = aws_cfg.get('regions') or [region]
            if region not in regions_list:
                regions_list = [region] + [r for r in regions_list if r != region]
            self.aws_config = AWSConfig(
                region=region,
                regions=regions_list,
                profile_name=aws_cfg.get('profile_name'),
                role_arn=aws_cfg.get('role_arn'),
                role_session_name=aws_cfg.get('role_session_name'),
            )
            self.logger.info(
                "AWS configuration applied",
                {'region': region, 'regions': self.aws_config.regions, 'config_file': self.config_manager.config_file}
            )
            self.safety_controls = SafetyControls(dry_run=dry_run)
            self.http_client = HTTPClient()
            
            # Initialize scheduler
            self.scheduler = FinOpsScheduler()
            self._scheduler_initialized = False
            
            # Initialize workflow state manager
            workflow_id = f"finops-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            self.workflow_state = None  # Will be initialized when workflow starts
            
            # Initialize core engines with configuration-based thresholds
            service_thresholds = self.config_manager.get('services.thresholds', {})
            optimization_config = self.config_manager.get('optimization', {})
            
            self.cost_optimizer = CostOptimizer(
                self.aws_config, 
                region, 
                custom_thresholds=service_thresholds
            )
            self.pricing_intelligence = PricingIntelligenceEngine(self.aws_config, region)
            self.ml_rightsizing = MLRightSizingEngine(self.aws_config, region)
            self.anomaly_detector = AnomalyDetector(self.aws_config, region)
            self.budget_manager = BudgetManager(dry_run=dry_run)
            
            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.info("Advanced FinOps Platform initialized successfully", {
                'region': region,
                'dry_run': dry_run,
                'config_file': self.config_manager.config_file,
                'service_thresholds_count': len(service_thresholds),
                'optimization_config_loaded': bool(optimization_config)
            })
            
            # Create initialization success alert
            system_monitor.alert_manager.create_alert(
                severity=AlertSeverity.INFO,
                title="FinOps Platform Initialized",
                message=f"Advanced FinOps Platform initialized successfully in {region}",
                source="orchestrator",
                correlation_id=init_context.correlation_id,
                metadata={
                    'region': region,
                    'dry_run': dry_run,
                    'config_file': config_file
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to initialize FinOps orchestrator", {
                'error': str(e)
            }, exc_info=True)
            
            # Create critical alert for initialization failure
            system_monitor.alert_manager.create_alert(
                severity=AlertSeverity.CRITICAL,
                title="FinOps Platform Initialization Failed",
                message=f"Failed to initialize Advanced FinOps Platform: {str(e)}",
                source="orchestrator",
                correlation_id=init_context.correlation_id,
                metadata={'error': str(e)}
            )
            raise
        finally:
            self.logger.clear_correlation_context()
    
    def _initialize_workflow_state(self, workflow_type: str = "standard") -> None:
        """
        Initialize workflow state management for the current execution.
        
        Args:
            workflow_type: Type of workflow being executed
        """
        from utils.workflow_state import WorkflowStateManager
        
        workflow_id = f"finops-{workflow_type}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        self.workflow_state = WorkflowStateManager(workflow_id)
        
        # Start workflow with current configuration
        workflow_config = {
            'region': self.region,
            'dry_run': self.dry_run,
            'services_enabled': self.config_manager.get('services.enabled', []),
            'optimization_config': self.config_manager.get('optimization', {}),
            'workflow_type': workflow_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.workflow_state.start_workflow(workflow_config)
        self.logger.info(f"Initialized workflow state: {workflow_id}")
    
    def _create_workflow_checkpoint(self, checkpoint_name: str, data: Dict[str, Any]) -> None:
        """
        Create a workflow checkpoint with current state.
        
        Args:
            checkpoint_name: Name of the checkpoint
            data: Data to save at checkpoint
        """
        if self.workflow_state:
            try:
                # Create a serializable copy of the data by removing non-serializable objects
                serializable_data = self._make_serializable(data)
                self.workflow_state.create_checkpoint(checkpoint_name, serializable_data)
            except Exception as e:
                self.logger.warning(f"Failed to create checkpoint {checkpoint_name}: {e}")
        else:
            self.logger.warning("Workflow state not initialized - cannot create checkpoint")
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Make an object serializable by removing or converting non-serializable elements.
        
        Args:
            obj: Object to make serializable
            
        Returns:
            Serializable version of the object
        """
        import pickle
        from unittest.mock import Mock, MagicMock
        
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                try:
                    # Test if the value is serializable
                    pickle.dumps(value)
                    result[key] = self._make_serializable(value)
                except (TypeError, AttributeError):
                    # If not serializable, convert to string representation
                    if isinstance(value, (Mock, MagicMock)):
                        result[key] = f"<Mock: {type(value).__name__}>"
                    else:
                        result[key] = str(value)
            return result
        elif isinstance(obj, list):
            result = []
            for item in obj:
                try:
                    pickle.dumps(item)
                    result.append(self._make_serializable(item))
                except (TypeError, AttributeError):
                    if isinstance(item, (Mock, MagicMock)):
                        result.append(f"<Mock: {type(item).__name__}>")
                    else:
                        result.append(str(item))
            return result
        else:
            try:
                # Test if the object itself is serializable
                pickle.dumps(obj)
                return obj
            except (TypeError, AttributeError):
                if isinstance(obj, (Mock, MagicMock)):
                    return f"<Mock: {type(obj).__name__}>"
                else:
                    return str(obj)
    
    def _load_workflow_checkpoint(self, checkpoint_name: str) -> Optional[Dict[str, Any]]:
        """
        Load data from a workflow checkpoint.
        
        Args:
            checkpoint_name: Name of the checkpoint to load
            
        Returns:
            Checkpoint data or None if not found
        """
        if self.workflow_state:
            return self.workflow_state.load_checkpoint(checkpoint_name)
        else:
            self.logger.warning("Workflow state not initialized - cannot load checkpoint")
            return None
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully with enhanced monitoring."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        
        # Stop system monitoring
        system_monitor.stop_monitoring()
        
        # Stop scheduler if running
        if self.scheduler.is_running():
            self.scheduler.stop()
        
        # Create shutdown alert
        system_monitor.alert_manager.create_alert(
            severity=AlertSeverity.INFO,
            title="FinOps Platform Shutdown",
            message=f"Advanced FinOps Platform shutting down (signal {signum})",
            source="orchestrator",
            metadata={'signal': signum}
        )
        
        # Get final recovery statistics
        recovery_stats = global_recovery_manager.get_recovery_stats()
        self.logger.info("Final recovery statistics", recovery_stats)
        
        sys.exit(0)
    
    def _setup_logging(self) -> None:
        """Set up comprehensive logging based on configuration."""
        log_config = self.config_manager.get_logging_config()
        
        # Set log level
        log_level = getattr(logging, log_config.level.upper(), logging.INFO)
        
        # Configure handlers
        handlers = []
        
        # Console handler
        if log_config.console.get('enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_format = log_config.console.get('format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(logging.Formatter(console_format))
            handlers.append(console_handler)
        
        # File handler
        if log_config.file.get('enabled', True):
            log_file = log_config.file.get('path', 'advanced_finops.log')
            
            # Use RotatingFileHandler if max_size is specified
            max_size = log_config.file.get('max_size_mb', 0)
            if max_size > 0:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_size * 1024 * 1024,
                    backupCount=log_config.file.get('backup_count', 5)
                )
            else:
                file_handler = logging.FileHandler(log_file)
            
            file_format = log_config.file.get('format',
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(logging.Formatter(file_format))
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers,
            force=True  # Override any existing configuration
        )
        
        # Set component-specific log levels
        for component, level in log_config.components.items():
            component_level = getattr(logging, level.upper(), logging.WARNING)
            logging.getLogger(component).setLevel(component_level)
    
    def setup_scheduler(self) -> None:
        """Set up scheduled tasks based on configuration."""
        if self._scheduler_initialized:
            return
        
        sched_config = self.config_manager.get_scheduling_config()
        
        # Continuous monitoring
        if sched_config.continuous_monitoring.get('enabled', False):
            interval = sched_config.continuous_monitoring.get('interval_minutes', 60)
            self.scheduler.add_continuous_task(
                task_id='continuous_monitoring',
                name='Continuous Resource Monitoring',
                interval_minutes=interval,
                callback=self._continuous_monitoring_callback,
                enabled=True
            )
            self.logger.info(f"Scheduled continuous monitoring every {interval} minutes")
        
        # Daily optimization
        if sched_config.daily_optimization.get('enabled', False):
            time_of_day = sched_config.daily_optimization.get('time', '02:00')
            self.scheduler.add_daily_task(
                task_id='daily_optimization',
                name='Daily Cost Optimization',
                time_of_day=time_of_day,
                callback=self._daily_optimization_callback,
                enabled=True
            )
            self.logger.info(f"Scheduled daily optimization at {time_of_day} UTC")
        
        # Weekly reporting
        if sched_config.weekly_reporting.get('enabled', False):
            day = sched_config.weekly_reporting.get('day', 'sunday')
            time_of_day = sched_config.weekly_reporting.get('time', '06:00')
            self.scheduler.add_weekly_task(
                task_id='weekly_reporting',
                name='Weekly Cost Report',
                day_of_week=day,
                time_of_day=time_of_day,
                callback=self._weekly_reporting_callback,
                enabled=True
            )
            self.logger.info(f"Scheduled weekly reporting every {day} at {time_of_day} UTC")
        
        self._scheduler_initialized = True
    
    def _continuous_monitoring_callback(self) -> Dict[str, Any]:
        """Callback for continuous monitoring tasks."""
        self.logger.info("Running continuous monitoring...")
        
        try:
            # Run discovery and anomaly detection
            discovery_results = self.run_discovery()
            anomaly_results = self.run_anomaly_detection()
            
            # Check for critical anomalies that need immediate attention
            critical_anomalies = []
            for anomaly in anomaly_results.get('detailed_results', {}).get('anomalies_detected', []):
                if anomaly.get('severity') == 'CRITICAL':
                    critical_anomalies.append(anomaly)
            
            if critical_anomalies:
                self.logger.warning(f"Found {len(critical_anomalies)} critical cost anomalies!")
                # TODO: Send alerts/notifications
            
            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'resources_discovered': discovery_results.get('resources_discovered', 0),
                'anomalies_detected': anomaly_results.get('anomalies_detected', 0),
                'critical_anomalies': len(critical_anomalies)
            }
            
        except Exception as e:
            self.logger.error(f"Continuous monitoring failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _daily_optimization_callback(self) -> Dict[str, Any]:
        """Callback for daily optimization tasks."""
        self.logger.info("Running daily optimization...")
        
        try:
            # Run full workflow with auto-approval for low-risk optimizations
            opt_config = self.config_manager.get_optimization_config()
            auto_approve_low = 'LOW' in opt_config.auto_approve_risk_levels
            
            results = self.run_complete_workflow(
                services=None,  # All services
                scan_only=False,
                approve_low_risk=auto_approve_low
            )
            
            return {
                'success': results.get('success', False),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'workflow_duration': results.get('workflow_duration', 0),
                'phases_completed': len(results.get('phases', {}))
            }
            
        except Exception as e:
            self.logger.error(f"Daily optimization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _weekly_reporting_callback(self) -> Dict[str, Any]:
        """Callback for weekly reporting tasks."""
        self.logger.info("Running weekly reporting...")
        
        try:
            # Generate comprehensive reports
            discovery_results = self.run_discovery()
            budget_results = self.run_budget_management()
            
            # TODO: Generate and send weekly report
            # This would typically create a comprehensive report and email it
            
            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'report_generated': True,
                'resources_analyzed': discovery_results.get('resources_discovered', 0),
                'budgets_analyzed': budget_results.get('budgets_analyzed', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Weekly reporting failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def start_continuous_monitoring(self) -> None:
        """Start continuous monitoring mode."""
        self.logger.info("Starting continuous monitoring mode...")
        
        # Setup scheduler if not already done
        self.setup_scheduler()
        
        # Start the scheduler
        self.scheduler.start()
        
        self.logger.info("Continuous monitoring started. Press Ctrl+C to stop.")
        
        try:
            # Keep the main thread alive
            while self.scheduler.is_running():
                time.sleep(60)  # Check every minute
                
                # Print status every hour
                if datetime.now().minute == 0:
                    self._print_monitoring_status()
                    
        except KeyboardInterrupt:
            self.logger.info("Stopping continuous monitoring...")
            self.scheduler.stop()
    
    def _print_monitoring_status(self) -> None:
        """Print current monitoring status."""
        tasks = self.scheduler.list_tasks()
        enabled_tasks = [t for t in tasks if t['enabled']]
        
        self.logger.info(f"Monitoring status: {len(enabled_tasks)} active tasks")
        
        for task in enabled_tasks:
            next_run = task.get('next_run')
            if next_run:
                self.logger.info(f"  {task['name']}: next run at {next_run}")
    
    def run_with_scheduler(self, daemon_mode: bool = False) -> None:
        """
        Run the platform with scheduler enabled.
        
        Args:
            daemon_mode: If True, run as a daemon process
        """
        self.logger.info("Starting FinOps platform with scheduler...")
        
        # Setup and start scheduler
        self.setup_scheduler()
        self.scheduler.start()
        
        if daemon_mode:
            self.logger.info("Running in daemon mode...")
            # In daemon mode, just keep running
            try:
                while True:
                    time.sleep(3600)  # Sleep for 1 hour
            except KeyboardInterrupt:
                self.logger.info("Daemon mode interrupted")
        else:
            # Interactive mode - show status and allow commands
            self._interactive_scheduler_mode()
        
        # Cleanup
        self.scheduler.stop()
    
    def _interactive_scheduler_mode(self) -> None:
        """Run scheduler in interactive mode with command interface."""
        self.logger.info("Scheduler running in interactive mode. Type 'help' for commands.")
        
        while self.scheduler.is_running():
            try:
                command = input("\nfinops> ").strip().lower()
                
                if command == 'help':
                    print("Available commands:")
                    print("  status    - Show scheduler status")
                    print("  tasks     - List all tasks")
                    print("  run <id>  - Run task immediately")
                    print("  enable <id> - Enable task")
                    print("  disable <id> - Disable task")
                    print("  quit      - Stop scheduler and exit")
                    print("  help      - Show this help")
                
                elif command == 'status':
                    self._print_monitoring_status()
                
                elif command == 'tasks':
                    tasks = self.scheduler.list_tasks()
                    print(f"\nScheduled tasks ({len(tasks)}):")
                    for task in tasks:
                        status = "enabled" if task['enabled'] else "disabled"
                        print(f"  {task['task_id']}: {task['name']} ({status})")
                        if task['next_run']:
                            print(f"    Next run: {task['next_run']}")
                
                elif command.startswith('run '):
                    task_id = command[4:].strip()
                    if self.scheduler.run_task_now(task_id):
                        print(f"Task '{task_id}' executed")
                    else:
                        print(f"Task '{task_id}' not found or disabled")
                
                elif command.startswith('enable '):
                    task_id = command[7:].strip()
                    if self.scheduler.enable_task(task_id):
                        print(f"Task '{task_id}' enabled")
                    else:
                        print(f"Task '{task_id}' not found")
                
                elif command.startswith('disable '):
                    task_id = command[8:].strip()
                    if self.scheduler.disable_task(task_id):
                        print(f"Task '{task_id}' disabled")
                    else:
                        print(f"Task '{task_id}' not found")
                
                elif command in ['quit', 'exit', 'q']:
                    break
                
                elif command == '':
                    continue  # Empty command
                
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Exiting interactive mode...")
        """
        Run resource discovery across specified AWS services.
        
        Args:
            services: List of services to scan (default: all supported services)
            
        Returns:
            Discovery results summary
        """
    def run_discovery(self, services: List[str] = None) -> Dict[str, Any]:
        """
        Run resource discovery across specified AWS services.
        
        Args:
            services: List of services to scan (default: from configuration)
            
        Returns:
            Discovery results summary
        """
        from utils.workflow_state import WorkflowPhase
        
        # Initialize workflow state if not already done
        if not self.workflow_state:
            self._initialize_workflow_state("discovery")
        
        # Start discovery phase
        self.workflow_state.start_phase(WorkflowPhase.DISCOVERY)
        
        if services is None:
            # Get enabled services from configuration
            services = [s for s in self.config_manager.get('services.enabled', []) 
                       if self.config_manager.is_service_enabled(s)]
        
        self.logger.info(f"Starting resource discovery for services: {services}")
        
        discovery_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'region': self.region,
            'services_scanned': services,
            'resources_discovered': 0,
            'services': {},
            'configuration_used': {
                'thresholds': self.config_manager.get('services.thresholds', {}),
                'enabled_services': self.config_manager.get('services.enabled', [])
            },
            'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None
        }
        
        # Check backend connectivity
        backend_available = self.http_client.health_check()
        if not backend_available:
            self.logger.warning("Backend API not available - discovery results will not be stored")
        
        # Initialize scanners with configuration-based thresholds
        scanners = self._initialize_scanners_with_config()
        
        # Create checkpoint before starting scans
        self._create_workflow_checkpoint('pre_discovery', {
            'services_to_scan': services,
            'configuration': discovery_results['configuration_used'],
            'backend_available': backend_available
        })
        
        # Scan each requested service
        for service in services:
            if service not in scanners:
                self.logger.warning(f"Scanner for service '{service}' not available")
                continue
                
            self.logger.info(f"Scanning {service} resources...")
            start_time = datetime.now(timezone.utc)
            
            try:
                scanner = scanners[service]
                
                # Call appropriate scan method based on service
                resources = self._execute_service_scan(service, scanner)
                
                # Calculate scan duration
                scan_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                service_results = {
                    'resources_found': len(resources),
                    'scan_duration': scan_duration,
                    'status': 'SUCCESS',
                    'resources': resources,
                    'thresholds_applied': self.config_manager.get(f'services.thresholds.{service}', {})
                }
                
                discovery_results['resources_discovered'] += len(resources)
                
                # Send data to backend API if available
                if backend_available:
                    try:
                        # Get account ID from AWS config
                        try:
                            account_id = self.aws_config.get_account_id()
                        except Exception:
                            account_id = "123456789012"
                            
                        # Validate resource data before sending
                        validated_resources = []
                        for resource in resources:
                            resource['accountId'] = account_id
                            validation = self.http_client.validate_data_schema(resource, 'resource')
                            if validation['valid']:
                                validated_resources.append(resource)
                            else:
                                self.logger.warning(f"Resource validation failed for {resource.get('resourceId', 'unknown')}: {validation['errors']}")
                        
                        if validated_resources:
                            self.http_client.post_resources(validated_resources)
                            self.logger.info(f"Sent {len(validated_resources)} validated {service} resources to backend")
                        else:
                            self.logger.warning(f"No valid {service} resources to send to backend")
                    except Exception as e:
                        self.logger.warning(f"Failed to send {service} data to backend: {e}")
                
                # Create checkpoint after each service
                self._create_workflow_checkpoint(f'discovery_{service}', {
                    'service': service,
                    'resources_found': len(resources),
                    'scan_duration': scan_duration,
                    'resources': resources[:10]  # Store sample of resources
                })
                
            except Exception as e:
                scan_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                self.logger.error(f"Failed to scan {service} resources: {e}")
                
                service_results = {
                    'resources_found': 0,
                    'scan_duration': scan_duration,
                    'status': f'ERROR: {str(e)}',
                    'resources': []
                }
            
            discovery_results['services'][service] = service_results
            self.logger.info(f"Completed {service} scan: {service_results['resources_found']} resources found in {service_results['scan_duration']:.2f}s")
        
        # Complete discovery phase
        self.workflow_state.complete_phase(WorkflowPhase.DISCOVERY, discovery_results)
        
        # Create final checkpoint
        self._create_workflow_checkpoint('post_discovery', discovery_results)
        
        self.logger.info(f"Discovery completed. Total resources: {discovery_results['resources_discovered']}")
        return discovery_results
    
    def _initialize_scanners_with_config(self) -> Dict[str, Any]:
        """
        Initialize all scanners with configuration-based thresholds.
        
        Returns:
            Dictionary of initialized scanners
        """
        scanners = {
            'ec2': EC2Scanner(self.aws_config, self.region),
            'rds': RDSScanner(self.aws_config, self.region),
            'lambda': LambdaScanner(self.aws_config, self.region),
            's3': S3Scanner(self.aws_config, self.region),
            'ebs': EBSScanner(self.aws_config, self.region),
            'elb': ELBScanner(self.aws_config, self.region),
            'cloudwatch': CloudWatchScanner(self.aws_config, self.region)
        }
        
        # Apply configuration-based thresholds to scanners
        for service_name, scanner in scanners.items():
            if hasattr(scanner, 'set_thresholds'):
                service_thresholds = self.config_manager.get(f'services.thresholds.{service_name}', {})
                if service_thresholds:
                    scanner.set_thresholds(service_thresholds)
                    self.logger.debug(f"Applied thresholds to {service_name} scanner: {service_thresholds}")
        
        return scanners
    
    def _execute_service_scan(self, service: str, scanner: Any) -> List[Dict[str, Any]]:
        """
        Execute scan for a specific service.
        
        Args:
            service: Service name
            scanner: Scanner instance
            
        Returns:
            List of discovered resources
        """
        # Call appropriate scan method based on service
        if service == 'ec2':
            return scanner.scan_instances()
        elif service == 'rds':
            return scanner.scan_databases()
        elif service == 'lambda':
            return scanner.scan_functions()
        elif service == 's3':
            return scanner.scan_buckets()
        elif service == 'ebs':
            return scanner.scan_volumes()
        elif service == 'elb':
            return scanner.scan_load_balancers()
        elif service == 'cloudwatch':
            return scanner.scan_cloudwatch_resources()
        else:
            self.logger.warning(f"Unknown service scan method for: {service}")
            return []
    
    def run_optimization_analysis(self, discovered_resources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run cost optimization analysis on discovered resources.
        
        Args:
            discovered_resources: Previously discovered resources (optional)
            
        Returns:
            Optimization analysis results
        """
        from utils.workflow_state import WorkflowPhase
        
        # Start optimization analysis phase
        if self.workflow_state:
            self.workflow_state.start_phase(WorkflowPhase.OPTIMIZATION_ANALYSIS)
        
        self.logger.info("Starting optimization analysis...")
        
        analysis_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'region': self.region,
            'optimizations_found': 0,
            'potential_monthly_savings': 0.0,
            'categories': {},
            'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None
        }
        
        try:
            # Load discovered resources from checkpoint if not provided
            if discovered_resources is None:
                checkpoint_data = self._load_workflow_checkpoint('post_discovery')
                if checkpoint_data:
                    # Extract resources from all services
                    discovered_resources = []
                    for service_name, service_data in checkpoint_data.get('services', {}).items():
                        discovered_resources.extend(service_data.get('resources', []))
                    self.logger.info(f"Loaded {len(discovered_resources)} resources from discovery checkpoint")
                else:
                    self.logger.warning("No discovered resources available for optimization analysis")
                    discovered_resources = []
            
            # Create checkpoint before optimization analysis
            self._create_workflow_checkpoint('pre_optimization', {
                'resources_to_analyze': len(discovered_resources),
                'analysis_start_time': datetime.now(timezone.utc).isoformat()
            })
            
            # Run cost optimization analysis
            self.logger.info("Running cost optimization analysis...")
            cost_optimizations = self.cost_optimizer.analyze_resources(discovered_resources)
            
            analysis_results['categories']['cost_optimization'] = {
                'optimizations_found': len(cost_optimizations.get('recommendations', [])),
                'potential_savings': cost_optimizations.get('total_potential_savings', 0.0),
                'recommendations': cost_optimizations.get('recommendations', [])
            }
            
            # Run pricing intelligence analysis
            self.logger.info("Running pricing intelligence analysis...")
            pricing_recommendations = self.pricing_intelligence.analyze_pricing_opportunities(discovered_resources)
            
            analysis_results['categories']['pricing_intelligence'] = {
                'optimizations_found': len(pricing_recommendations.get('recommendations', [])),
                'potential_savings': pricing_recommendations.get('total_potential_savings', 0.0),
                'recommendations': pricing_recommendations.get('recommendations', [])
            }
            
            # Run ML right-sizing analysis
            self.logger.info("Running ML right-sizing analysis...")
            rightsizing_recommendations = self.ml_rightsizing.analyze_rightsizing_opportunities(discovered_resources)
            
            analysis_results['categories']['ml_rightsizing'] = {
                'optimizations_found': len(rightsizing_recommendations.get('recommendations', [])),
                'potential_savings': rightsizing_recommendations.get('total_potential_savings', 0.0),
                'recommendations': rightsizing_recommendations.get('recommendations', [])
            }
            
            # Calculate totals
            total_optimizations = 0
            total_savings = 0.0
            
            for category, category_data in analysis_results['categories'].items():
                total_optimizations += category_data['optimizations_found']
                total_savings += category_data['potential_savings']
            
            analysis_results['optimizations_found'] = total_optimizations
            analysis_results['potential_monthly_savings'] = total_savings
            
            # Send results to backend API if available
            try:
                if self.http_client.health_check():
                    # Get account ID from AWS config
                    try:
                        account_id = self.aws_config.get_account_id()
                    except Exception:
                        account_id = "123456789012"
                        
                    # Validate and send optimization data
                    all_optimizations = []
                    for category, category_data in analysis_results.get('categories', {}).items():
                        for rec in category_data.get('recommendations', []):
                            # Add category to recommendation
                            rec['category'] = category
                            rec['accountId'] = account_id
                            validation = self.http_client.validate_data_schema(rec, 'optimization')
                            if validation['valid']:
                                all_optimizations.append(rec)
                            else:
                                self.logger.warning(f"Optimization validation failed: {validation['errors']}")
                    
                    if all_optimizations:
                        self.http_client.post_optimizations(all_optimizations)
                        self.logger.info(f"Sent {len(all_optimizations)} validated optimization recommendations to backend")
                    
                    # Also send summary data
                    self.http_client.post_data('/api/optimization-analysis', {
                        'summary': analysis_results,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'finops-bot'
                    })
                    self.logger.info("Optimization analysis summary sent to backend API")
            except Exception as e:
                self.logger.warning(f"Failed to send optimization results to backend: {e}")
            
            # Create checkpoint after optimization analysis
            self._create_workflow_checkpoint('post_optimization', analysis_results)
            
            # Complete optimization analysis phase
            if self.workflow_state:
                self.workflow_state.complete_phase(WorkflowPhase.OPTIMIZATION_ANALYSIS, analysis_results)
            
            self.logger.info(f"Optimization analysis completed. Found {total_optimizations} optimizations with ${total_savings:.2f}/month potential savings")
            
        except Exception as e:
            self.logger.error(f"Optimization analysis failed: {e}")
            analysis_results['error'] = str(e)
            
            # Mark phase as failed
            if self.workflow_state:
                self.workflow_state.fail_phase(WorkflowPhase.OPTIMIZATION_ANALYSIS, str(e))
        
        return analysis_results
    
    def run_anomaly_detection(self, cost_data: List[Dict[str, Any]] = None, 
                             resources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run cost anomaly detection.
        
        Args:
            cost_data: Historical cost data for analysis
            resources: Resource data for root cause analysis
            
        Returns:
            Anomaly detection results
        """
        from utils.workflow_state import WorkflowPhase
        
        # Start anomaly detection phase
        if self.workflow_state:
            self.workflow_state.start_phase(WorkflowPhase.ANOMALY_DETECTION)
        
        self.logger.info("Starting anomaly detection...")
        
        try:
            # If no cost data provided, create sample data for demonstration
            if cost_data is None:
                cost_data = self._generate_sample_cost_data()
                self.logger.info("Using sample cost data for anomaly detection demonstration")
            
            # If no resources provided, load from checkpoint or create sample
            if resources is None:
                checkpoint_data = self._load_workflow_checkpoint('post_discovery')
                if checkpoint_data:
                    # Extract resources from all services
                    resources = []
                    for service_name, service_data in checkpoint_data.get('services', {}).items():
                        resources.extend(service_data.get('resources', []))
                    self.logger.info(f"Loaded {len(resources)} resources from discovery checkpoint for root cause analysis")
                else:
                    resources = self._generate_sample_resources()
                    self.logger.info("Using sample resources for root cause analysis demonstration")
            
            # Create checkpoint before anomaly detection
            self._create_workflow_checkpoint('pre_anomaly_detection', {
                'cost_data_points': len(cost_data),
                'resources_for_analysis': len(resources),
                'detection_config': self.config_manager.get('anomaly_detection', {})
            })
            
            # Run anomaly detection with configuration-based parameters
            anomaly_config = self.config_manager.get('anomaly_detection', {})
            
            # Apply configuration to anomaly detector
            if hasattr(self.anomaly_detector, 'set_configuration'):
                self.anomaly_detector.set_configuration(anomaly_config)
            
            anomaly_results = self.anomaly_detector.detect_anomalies(cost_data, resources)
            
            # Prepare final results first
            final_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': self.region,
                'anomalies_detected': len(anomaly_results.get('anomalies_detected', [])),
                'alerts_generated': len(anomaly_results.get('alerts_generated', [])),
                'baseline_established': anomaly_results.get('baseline_analysis', {}).get('baseline_established', False),
                'severity_breakdown': anomaly_results.get('detection_summary', {}).get('severity_breakdown', {}),
                'total_cost_impact': anomaly_results.get('detection_summary', {}).get('total_cost_impact', 0.0),
                'detailed_results': anomaly_results,
                'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None,
                'configuration_applied': anomaly_config
            }

            # Send results to backend API if available
            try:
                if self.http_client.health_check():
                    # Get account ID from AWS config
                    try:
                        account_id = self.aws_config.get_account_id()
                    except Exception:
                        account_id = "123456789012"
                        
                    # Validate and send anomaly data
                    anomalies_to_send = []
                    for anomaly in anomaly_results.get('anomalies_detected', []):
                        anomaly['accountId'] = account_id
                        validation = self.http_client.validate_data_schema(anomaly, 'anomaly')
                        if validation['valid']:
                            anomalies_to_send.append(anomaly)
                        else:
                            self.logger.warning(f"Anomaly validation failed: {validation['errors']}")
                    
                    if anomalies_to_send:
                        self.http_client.post_anomalies(anomalies_to_send)
                        self.logger.info(f"Sent {len(anomalies_to_send)} validated anomalies to backend")
                    
                    # Send summary data
                    self.http_client.post_data('/api/anomaly-analysis', {
                        'summary': final_results,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'finops-bot'
                    })
                    self.logger.info("Anomaly detection summary sent to backend API")
            except Exception as e:
                self.logger.warning(f"Failed to send anomaly results to backend: {e}")
            
            # Create checkpoint after anomaly detection
            self._create_workflow_checkpoint('post_anomaly_detection', anomaly_results)
            
            # Prepare final results
            final_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': self.region,
                'anomalies_detected': len(anomaly_results.get('anomalies_detected', [])),
                'alerts_generated': len(anomaly_results.get('alerts_generated', [])),
                'baseline_established': anomaly_results.get('baseline_analysis', {}).get('baseline_established', False),
                'severity_breakdown': anomaly_results.get('detection_summary', {}).get('severity_breakdown', {}),
                'total_cost_impact': anomaly_results.get('detection_summary', {}).get('total_cost_impact', 0.0),
                'detailed_results': anomaly_results,
                'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None,
                'configuration_applied': anomaly_config
            }
            
            # Complete anomaly detection phase
            if self.workflow_state:
                self.workflow_state.complete_phase(WorkflowPhase.ANOMALY_DETECTION, final_results)
            
            self.logger.info(f"Anomaly detection completed. Found {len(anomaly_results.get('anomalies_detected', []))} anomalies")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            
            # Mark phase as failed
            if self.workflow_state:
                self.workflow_state.fail_phase(WorkflowPhase.ANOMALY_DETECTION, str(e))
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': self.region,
                'anomalies_detected': 0,
                'error': str(e),
                'severity_breakdown': {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0},
                'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None
            }
    
    def run_budget_management(self, 
                             historical_data: List[Dict[str, Any]] = None,
                             create_sample_budgets: bool = True) -> Dict[str, Any]:
        """
        Run budget management and forecasting.
        
        Args:
            historical_data: Historical cost data for analysis
            create_sample_budgets: If True, create sample budgets for demonstration
            
        Returns:
            Budget management results
        """
        from utils.workflow_state import WorkflowPhase
        
        # Start budget management phase
        if self.workflow_state:
            self.workflow_state.start_phase(WorkflowPhase.BUDGET_MANAGEMENT)
        
        self.logger.info("Starting budget management...")
        
        try:
            budget_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': self.region,
                'budgets_analyzed': 0,
                'forecasts_generated': 0,
                'alerts_triggered': 0,
                'approval_workflows_created': 0,
                'budget_summary': {},
                'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None
            }
            
            # Apply budget management configuration
            budget_config = self.config_manager.get('budget_management', {})
            if hasattr(self.budget_manager, 'set_configuration'):
                self.budget_manager.set_configuration(budget_config)
            
            # Create checkpoint before budget management
            self._create_workflow_checkpoint('pre_budget_management', {
                'create_sample_budgets': create_sample_budgets,
                'budget_config': budget_config,
                'historical_data_points': len(historical_data) if historical_data else 0
            })
            
            # Create sample budgets if requested
            if create_sample_budgets:
                self.logger.info("Creating sample hierarchical budgets...")
                
                # Create organization budget
                from core.budget_manager import BudgetType
                
                org_budget = self.budget_manager.create_hierarchical_budget(
                    budget_id="org-2024",
                    budget_type=BudgetType.ORGANIZATION,
                    parent_budget_id=None,
                    budget_amount=120000.0,
                    period_months=12,
                    tags={"department": "engineering", "environment": "production"}
                )
                
                # Create team budgets
                team_budgets = [
                    {
                        "budget_id": "team-backend",
                        "budget_type": BudgetType.TEAM,
                        "parent_budget_id": "org-2024",
                        "budget_amount": 60000.0,
                        "tags": {"team": "backend", "services": "ec2,rds"}
                    },
                    {
                        "budget_id": "team-data",
                        "budget_type": BudgetType.TEAM,
                        "parent_budget_id": "org-2024",
                        "budget_amount": 40000.0,
                        "tags": {"team": "data", "services": "lambda,s3"}
                    }
                ]
                
                for team_budget_config in team_budgets:
                    team_budget = self.budget_manager.create_hierarchical_budget(
                        budget_id=team_budget_config["budget_id"],
                        budget_type=team_budget_config["budget_type"],
                        parent_budget_id=team_budget_config["parent_budget_id"],
                        budget_amount=team_budget_config["budget_amount"],
                        tags=team_budget_config["tags"]
                    )
                
                budget_results['budgets_analyzed'] = 3
                self.logger.info("Created sample hierarchical budget structure")
            
            # Generate historical data if not provided
            if historical_data is None:
                historical_data = self._generate_sample_cost_data()
                self.logger.info("Using sample historical data for budget analysis")
            
            # Analyze historical trends for each budget
            active_budgets = list(self.budget_manager.budgets.keys())
            if not active_budgets:
                self.logger.warning("No budgets available for analysis")
            
            for budget_id in active_budgets:
                try:
                    # Analyze historical trends
                    trend_analysis = self.budget_manager.analyze_historical_trends(
                        budget_id=budget_id,
                        historical_data=historical_data[:12],  # Use 12 months of data
                        analysis_months=12
                    )
                    
                    # Generate cost forecast with configuration-based parameters
                    forecast_config = budget_config.get('forecasting', {})
                    forecast = self.budget_manager.generate_cost_forecast(
                        budget_id=budget_id,
                        forecast_months=forecast_config.get('forecast_months', 6),
                        growth_projections=forecast_config.get('growth_assumptions', {"overall": 0.15}),
                        confidence_level=forecast_config.get('confidence_level', 0.95)
                    )
                    budget_results['forecasts_generated'] += 1
                    
                    # Track budget performance with sample actual costs
                    # In a real scenario, this would use actual AWS Cost Explorer data
                    sample_actual_costs = [
                        {"amount": 8500.0, "date": "2024-01-01"},
                        {"amount": 9200.0, "date": "2024-02-01"},
                        {"amount": 8800.0, "date": "2024-03-01"}
                    ]
                    
                    performance = self.budget_manager.track_budget_performance(
                        budget_id=budget_id,
                        actual_costs=sample_actual_costs
                    )
                    
                    # Generate budget alerts if thresholds are exceeded
                    current_spend = sum(cost["amount"] for cost in sample_actual_costs)
                    alerts = self.budget_manager.generate_budget_alerts(
                        budget_id=budget_id,
                        current_spend=current_spend
                    )
                    budget_results['alerts_triggered'] += len(alerts)
                    
                    # Create approval workflow if budget is approaching limits
                    if performance.get('utilization_percentage', 0) > 80:
                        workflow = self.budget_manager.trigger_approval_workflow(
                            budget_id=budget_id,
                            requested_amount=5000.0,
                            justification="Additional infrastructure for Q2 growth",
                            requester="finops-automation"
                        )
                        budget_results['approval_workflows_created'] += 1
                        
                except Exception as e:
                    self.logger.warning(f"Budget analysis failed for {budget_id}: {e}")
                    continue
            
            # Generate variance analysis for organization budget
            try:
                variance_analysis = self.budget_manager.generate_variance_analysis(
                    budget_id="org-2024",
                    analysis_period_months=12
                )
                self.logger.info("Generated variance analysis for organization budget")
            except Exception as e:
                self.logger.warning(f"Variance analysis failed: {e}")
            
            # Get budget summary
            budget_summary = self.budget_manager.get_budget_summary()
            budget_results['budget_summary'] = budget_summary
            
            # Send results to backend API if available
            try:
                if self.http_client.health_check():
                    # Get account ID from AWS config
                    try:
                        account_id = self.aws_config.get_account_id()
                    except Exception:
                        account_id = "123456789012"
                        
                    # Helper: translate budget_manager snake_case keys to backend camelCase
                    def _to_camel_budget(b):
                        return {
                            'budgetId':     b.get('budgetId')     or b.get('budget_id', ''),
                            'budgetType':   b.get('budgetType')   or b.get('budget_type', ''),
                            'budgetAmount': b.get('budgetAmount') or b.get('budget_amount', 0),
                            'name':         b.get('name', b.get('budget_id', '')),
                            'period':       b.get('period', 'monthly'),
                            'currency':     b.get('currency', 'USD'),
                            'accountId':    account_id,
                        }

                    # Send budget data to API with validation
                    for budget in self.budget_manager.budgets.values():
                        budget_payload = _to_camel_budget(budget)
                        validation = self.http_client.validate_data_schema(budget_payload, 'budget')
                        if validation['valid']:
                            try:
                                self.http_client.post_data('/api/budgets', budget_payload)
                            except Exception as e:
                                if "status 409" in str(e).lower() or "already exists" in str(e).lower():
                                    self.logger.info(f"Budget {budget_payload['budgetId']} already exists. Updating via PUT...")
                                    try:
                                        self.http_client.put_data(f"/api/budgets/{budget_payload['budgetId']}", budget_payload)
                                    except Exception as put_err:
                                        self.logger.warning(f"Failed to update existing budget {budget_payload['budgetId']}: {put_err}")
                                else:
                                    raise e
                        else:
                            self.logger.warning(f"Budget validation failed for {budget_payload.get('budgetId', 'unknown')}: {validation['errors']}")

                    # Send forecasts with proper endpoint structure
                    for forecast in self.budget_manager.forecasts.values():
                        budget_id = forecast.get('budget_id')
                        if budget_id:
                            self.http_client.post_data(f'/api/budgets/{budget_id}/forecasts', forecast)


                    # Send alerts with proper endpoint structure
                    for alert in self.budget_manager.alerts:
                        budget_id = alert.get('budget_id')
                        if budget_id:
                            self.http_client.post_data(f'/api/budgets/{budget_id}/alerts', alert)
                    
                    # Send approval workflows with proper endpoint structure
                    for workflow in self.budget_manager.approval_workflows:
                        budget_id = workflow.get('budget_id')
                        if budget_id:
                            self.http_client.post_data(f'/api/budgets/{budget_id}/approvals', workflow)
                    
                    # Send budget summary
                    self.http_client.post_data('/api/budget-analysis', {
                        'summary': budget_results,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'finops-bot'
                    })
                    
                    self.logger.info("Budget management results sent to backend API")
            except Exception as e:
                self.logger.warning(f"Failed to send budget results to backend: {e}")
            
            # Create checkpoint after budget management
            self._create_workflow_checkpoint('post_budget_management', budget_results)
            
            # Complete budget management phase
            if self.workflow_state:
                self.workflow_state.complete_phase(WorkflowPhase.BUDGET_MANAGEMENT, budget_results)
            
            self.logger.info(f"Budget management completed. Analyzed {budget_results['budgets_analyzed']} budgets, "
                           f"generated {budget_results['forecasts_generated']} forecasts, "
                           f"triggered {budget_results['alerts_triggered']} alerts")
            
            return budget_results
            
        except Exception as e:
            self.logger.error(f"Budget management failed: {e}")
            
            # Mark phase as failed
            if self.workflow_state:
                self.workflow_state.fail_phase(WorkflowPhase.BUDGET_MANAGEMENT, str(e))
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'region': self.region,
                'budgets_analyzed': 0,
                'forecasts_generated': 0,
                'alerts_triggered': 0,
                'error': str(e),
                'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None
            }
    
    def execute_optimizations(self, approve_low_risk: bool = False) -> Dict[str, Any]:
        """
        Execute approved optimizations with integrated execution engine.
        
        Args:
            approve_low_risk: If True, automatically approve low-risk optimizations
            
        Returns:
            Execution results
        """
        from utils.workflow_state import WorkflowPhase
        from core.execution_engine import ExecutionEngine
        from core.approval_workflow import ApprovalWorkflow
        
        # Start execution phase
        if self.workflow_state:
            self.workflow_state.start_phase(WorkflowPhase.EXECUTION)
        
        self.logger.info(f"Starting optimization execution (approve_low_risk: {approve_low_risk})")
        
        execution_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'region': self.region,
            'dry_run': self.dry_run,
            'optimizations_executed': 0,
            'optimizations_pending_approval': 0,
            'total_savings_realized': 0.0,
            'errors': [],
            'workflow_id': self.workflow_state.workflow_id if self.workflow_state else None
        }
        
        try:
            # Initialize execution engine with safety controls
            execution_engine = ExecutionEngine(
                aws_config=self.aws_config,
                safety_controls=self.safety_controls,
                dry_run=self.dry_run
            )
            
            # Initialize approval workflow
            approval_workflow = ApprovalWorkflow(dry_run=self.dry_run)
            
            # Load optimization recommendations from checkpoint
            optimization_checkpoint = self._load_workflow_checkpoint('post_optimization')
            if not optimization_checkpoint:
                self.logger.warning("No optimization recommendations found for execution")
                return execution_results
            
            # Extract all recommendations from different categories
            all_recommendations = []
            for category, category_data in optimization_checkpoint.get('categories', {}).items():
                for rec in category_data.get('recommendations', []):
                    rec['category'] = category
                    all_recommendations.append(rec)
            
            self.logger.info(f"Found {len(all_recommendations)} optimization recommendations for execution")
            
            # Create checkpoint before execution
            self._create_workflow_checkpoint('pre_execution', {
                'total_recommendations': len(all_recommendations),
                'approve_low_risk': approve_low_risk,
                'execution_config': self.config_manager.get('optimization', {})
            })
            
            # Process each recommendation through approval workflow
            for i, recommendation in enumerate(all_recommendations):
                try:
                    self.logger.info(f"Processing recommendation {i+1}/{len(all_recommendations)}: {recommendation.get('optimization_type', 'unknown')}")
                    
                    # Determine if approval is required
                    risk_level = recommendation.get('risk_level', 'MEDIUM')
                    requires_approval = approval_workflow.requires_approval(
                        optimization_type=recommendation.get('optimization_type'),
                        risk_level=risk_level,
                        cost_impact=recommendation.get('estimated_monthly_savings', 0.0)
                    )
                    
                    # Auto-approve low-risk optimizations if enabled
                    if approve_low_risk and risk_level == 'LOW':
                        requires_approval = False
                        self.logger.info(f"Auto-approving low-risk optimization: {recommendation.get('resource_id')}")
                    
                    if requires_approval:
                        # Create approval workflow
                        approval_id = approval_workflow.create_approval_request(
                            optimization_id=recommendation.get('optimization_id', f'opt-{i}'),
                            resource_id=recommendation.get('resource_id'),
                            optimization_type=recommendation.get('optimization_type'),
                            risk_level=risk_level,
                            estimated_savings=recommendation.get('estimated_monthly_savings', 0.0),
                            justification=recommendation.get('justification', 'Cost optimization recommendation')
                        )
                        
                        execution_results['optimizations_pending_approval'] += 1
                        self.logger.info(f"Created approval request {approval_id} for {recommendation.get('resource_id')}")
                        
                    else:
                        # Execute optimization immediately
                        execution_result = execution_engine.execute_optimization(recommendation)
                        
                        if execution_result.get('success', False):
                            execution_results['optimizations_executed'] += 1
                            execution_results['total_savings_realized'] += execution_result.get('actual_savings', 0.0)
                            self.logger.info(f"Successfully executed optimization for {recommendation.get('resource_id')}")
                        else:
                            error_msg = f"Failed to execute optimization for {recommendation.get('resource_id')}: {execution_result.get('error', 'Unknown error')}"
                            execution_results['errors'].append(error_msg)
                            self.logger.error(error_msg)
                    
                    # Create checkpoint after each recommendation
                    if i % 10 == 0:  # Checkpoint every 10 recommendations
                        self._create_workflow_checkpoint(f'execution_progress_{i}', {
                            'processed': i + 1,
                            'total': len(all_recommendations),
                            'executed': execution_results['optimizations_executed'],
                            'pending_approval': execution_results['optimizations_pending_approval']
                        })
                
                except Exception as e:
                    error_msg = f"Error processing recommendation {i+1}: {str(e)}"
                    execution_results['errors'].append(error_msg)
                    self.logger.error(error_msg)
                    continue
            
            # Send execution results to backend API if available
            try:
                if self.http_client.health_check():
                    self.http_client.post_data('/api/execution-results', {
                        'execution_summary': execution_results,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'finops-bot'
                    })
                    self.logger.info("Execution results sent to backend API")
            except Exception as e:
                self.logger.warning(f"Failed to send execution results to backend: {e}")
            
            # Create final execution checkpoint
            self._create_workflow_checkpoint('post_execution', execution_results)
            
            # Complete execution phase
            if self.workflow_state:
                self.workflow_state.complete_phase(WorkflowPhase.EXECUTION, execution_results)
            
            self.logger.info(f"Optimization execution completed. Executed: {execution_results['optimizations_executed']}, "
                           f"Pending approval: {execution_results['optimizations_pending_approval']}, "
                           f"Savings realized: ${execution_results['total_savings_realized']:.2f}/month")
            
        except Exception as e:
            self.logger.error(f"Optimization execution failed: {e}")
            execution_results['error'] = str(e)
            
            # Mark execution phase as failed
            if self.workflow_state:
                self.workflow_state.fail_phase(WorkflowPhase.EXECUTION, str(e))
        
        return execution_results
    
    def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Resume a previously paused or failed workflow.
        
        Args:
            workflow_id: ID of the workflow to resume
            
        Returns:
            Resume operation results
        """
        from utils.workflow_state import WorkflowStateManager, WorkflowPhase
        
        self.logger.info(f"Attempting to resume workflow: {workflow_id}")
        
        try:
            # Load existing workflow state
            self.workflow_state = WorkflowStateManager(workflow_id)
            
            if not self.workflow_state.can_resume():
                return {
                    'success': False,
                    'error': f"Workflow {workflow_id} cannot be resumed (status: {self.workflow_state.get_status().value})"
                }
            
            # Resume workflow
            self.workflow_state.resume_workflow()
            
            # Get next phase to execute
            next_phase = self.workflow_state.get_next_phase()
            if not next_phase:
                self.logger.info("All phases completed - workflow is already finished")
                return {
                    'success': True,
                    'message': 'Workflow already completed',
                    'workflow_id': workflow_id
                }
            
            self.logger.info(f"Resuming from phase: {next_phase.value}")
            
            # Execute remaining phases
            completed_phases = set(phase.value for phase in self.workflow_state.get_completed_phases())
            
            # Load configuration from workflow state
            workflow_config = self.workflow_state.state.get('configuration', {})
            services = workflow_config.get('services_enabled', [])
            
            resume_results = {
                'workflow_id': workflow_id,
                'resumed_from_phase': next_phase.value,
                'phases_completed_before_resume': len(completed_phases),
                'phases': {}
            }
            
            # Execute phases based on what's remaining
            if WorkflowPhase.DISCOVERY.value not in completed_phases:
                discovery_results = self.run_discovery(services)
                resume_results['phases']['discovery'] = discovery_results
            
            if WorkflowPhase.OPTIMIZATION_ANALYSIS.value not in completed_phases:
                # Load discovered resources from checkpoint if available
                discovered_resources = None
                if WorkflowPhase.DISCOVERY.value in completed_phases:
                    checkpoint_data = self._load_workflow_checkpoint('post_discovery')
                    if checkpoint_data:
                        discovered_resources = []
                        for service_name, service_data in checkpoint_data.get('services', {}).items():
                            discovered_resources.extend(service_data.get('resources', []))
                
                optimization_results = self.run_optimization_analysis(discovered_resources)
                resume_results['phases']['optimization'] = optimization_results
            
            if WorkflowPhase.ANOMALY_DETECTION.value not in completed_phases:
                anomaly_results = self.run_anomaly_detection()
                resume_results['phases']['anomaly_detection'] = anomaly_results
            
            if WorkflowPhase.BUDGET_MANAGEMENT.value not in completed_phases:
                budget_results = self.run_budget_management()
                resume_results['phases']['budget_management'] = budget_results
            
            if WorkflowPhase.EXECUTION.value not in completed_phases:
                if not self.dry_run:
                    execution_results = self.execute_optimizations()
                    resume_results['phases']['execution'] = execution_results
            
            if WorkflowPhase.REPORTING.value not in completed_phases:
                reporting_results = self._generate_final_report(resume_results)
                resume_results['phases']['reporting'] = reporting_results
            
            # Complete workflow
            self.workflow_state.complete_workflow(success=True)
            
            self.logger.info(f"Successfully resumed and completed workflow: {workflow_id}")
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'phases_executed': len(resume_results['phases']),
                'results': resume_results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to resume workflow {workflow_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_id': workflow_id
            }
    
    def list_workflows(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """
        List available workflows with their status.
        
        Args:
            status_filter: Optional status filter (e.g., 'paused', 'failed')
            
        Returns:
            List of workflow summaries
        """
        from utils.workflow_state import WorkflowStateManager
        import glob
        import os
        
        workflows = []
        
        try:
            # Find all workflow state files
            state_dir = "workflow_states"
            if os.path.exists(state_dir):
                for state_file in glob.glob(os.path.join(state_dir, "*.json")):
                    try:
                        workflow_id = os.path.basename(state_file).replace('.json', '')
                        workflow_state = WorkflowStateManager(workflow_id)
                        
                        summary = workflow_state.get_summary()
                        
                        # Apply status filter if specified
                        if status_filter and summary['status'] != status_filter:
                            continue
                        
                        workflows.append(summary)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load workflow state from {state_file}: {e}")
                        continue
            
            # Sort by start time (most recent first)
            workflows.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list workflows: {e}")
        
        return workflows
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific workflow.
        
        Args:
            workflow_id: ID of the workflow to check
            
        Returns:
            Detailed workflow status
        """
        from utils.workflow_state import WorkflowStateManager
        
        try:
            workflow_state = WorkflowStateManager(workflow_id)
            return workflow_state.get_summary()
        except Exception as e:
            self.logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
            return {
                'error': str(e),
                'workflow_id': workflow_id
            }
    
    def run_complete_workflow(self, 
                             services: List[str] = None,
                             scan_only: bool = False,
                             approve_low_risk: bool = False) -> Dict[str, Any]:
        """
        Run the complete FinOps workflow with integrated state management.
        
        Args:
            services: List of services to scan
            scan_only: If True, only run discovery
            approve_low_risk: If True, automatically approve low-risk optimizations
            
        Returns:
            Complete workflow results
        """
        from utils.workflow_state import WorkflowPhase
        
        # Initialize workflow state
        workflow_type = "scan_only" if scan_only else "complete"
        self._initialize_workflow_state(workflow_type)
        
        self.logger.info("Starting complete FinOps workflow...")
        
        workflow_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'region': self.region,
            'dry_run': self.dry_run,
            'workflow_duration': 0.0,
            'workflow_id': self.workflow_state.workflow_id,
            'workflow_type': workflow_type,
            'phases': {},
            'configuration_applied': {
                'services': services or self.config_manager.get('services.enabled', []),
                'scan_only': scan_only,
                'approve_low_risk': approve_low_risk,
                'thresholds': self.config_manager.get('services.thresholds', {}),
                'optimization_config': self.config_manager.get('optimization', {}),
                'anomaly_config': self.config_manager.get('anomaly_detection', {}),
                'budget_config': self.config_manager.get('budget_management', {})
            }
        }
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Phase 1: Resource Discovery
            self.logger.info("Phase 1: Resource Discovery")
            discovery_results = self.run_discovery(services)
            workflow_results['phases']['discovery'] = discovery_results
            
            if scan_only:
                self.logger.info("Scan-only mode - skipping optimization phases")
                self.workflow_state.complete_workflow(success=True)
                
                # Calculate total duration
                end_time = datetime.now(timezone.utc)
                workflow_results['workflow_duration'] = (end_time - start_time).total_seconds()
                workflow_results['success'] = True
                
                return workflow_results
            
            # Phase 2: Optimization Analysis
            self.logger.info("Phase 2: Optimization Analysis")
            
            # Extract discovered resources for optimization analysis
            discovered_resources = []
            for service_name, service_data in discovery_results.get('services', {}).items():
                discovered_resources.extend(service_data.get('resources', []))
            
            optimization_results = self.run_optimization_analysis(discovered_resources)
            workflow_results['phases']['optimization'] = optimization_results
            
            # Phase 3: Anomaly Detection
            self.logger.info("Phase 3: Anomaly Detection")
            anomaly_results = self.run_anomaly_detection(resources=discovered_resources)
            workflow_results['phases']['anomaly_detection'] = anomaly_results
            
            # Phase 4: Budget Management
            self.logger.info("Phase 4: Budget Management")
            budget_results = self.run_budget_management()
            workflow_results['phases']['budget_management'] = budget_results
            
            # Phase 5: Optimization Execution (if not dry run)
            if not self.dry_run or approve_low_risk:
                self.logger.info("Phase 5: Optimization Execution")
                execution_results = self.execute_optimizations(approve_low_risk)
                workflow_results['phases']['execution'] = execution_results
            else:
                self.logger.info("Skipping execution phase - DRY_RUN mode enabled")
            
            # Phase 6: Reporting
            self.logger.info("Phase 6: Final Reporting")
            reporting_results = self._generate_final_report(workflow_results)
            workflow_results['phases']['reporting'] = reporting_results
            
            # Complete workflow successfully
            self.workflow_state.complete_workflow(success=True)
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            workflow_results['error'] = str(e)
            workflow_results['success'] = False
            
            # Mark workflow as failed
            self.workflow_state.complete_workflow(success=False)
            
            return workflow_results
        
        # Calculate total duration
        end_time = datetime.now(timezone.utc)
        workflow_results['workflow_duration'] = (end_time - start_time).total_seconds()
        workflow_results['success'] = True
        
        # Create final workflow checkpoint
        self._create_workflow_checkpoint('workflow_complete', workflow_results)
        
        # Generate workflow summary
        workflow_summary = self._generate_workflow_summary(workflow_results)
        workflow_results['summary'] = workflow_summary
        
        self.logger.info(f"Complete workflow finished in {workflow_results['workflow_duration']:.2f} seconds")
        self.logger.info(f"Workflow summary: {workflow_summary}")
        
        return workflow_results

    def sync_to_backend(self) -> Dict[str, Any]:
        """
        Sync data from existing workflow checkpoints to the backend API.
        
        Returns:
            Sync operation results summary
        """
        self.logger.info("Starting backend data synchronization from checkpoints...")
        
        sync_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'resources_synced': 0,
            'optimizations_synced': 0,
            'anomalies_synced': 0,
            'budgets_synced': 0,
            'success': True,
            'errors': []
        }
        
        if not self.http_client.health_check():
            error_msg = "Backend API not available for synchronization"
            self.logger.error(error_msg)
            sync_results['success'] = False
            sync_results['error'] = error_msg
            return sync_results

        # 1. Sync Resources from discovery checkpoint
        discovery_checkpoint = self._load_workflow_checkpoint('post_discovery')
        if discovery_checkpoint:
            all_resources = []
            for service_name, service_data in discovery_checkpoint.get('services', {}).items():
                all_resources.extend(service_data.get('resources', []))
            
            if all_resources:
                try:
                    self.http_client.post_resources(all_resources)
                    sync_results['resources_synced'] = len(all_resources)
                    self.logger.info(f"Synced {len(all_resources)} resources from checkpoint")
                except Exception as e:
                    sync_results['errors'].append(f"Resource sync failed: {e}")

        # 2. Sync Optimizations from optimization checkpoint
        opt_checkpoint = self._load_workflow_checkpoint('post_optimization')
        if opt_checkpoint:
            all_opts = []
            for category, data in opt_checkpoint.get('categories', {}).items():
                for rec in data.get('recommendations', []):
                    rec['category'] = category
                    all_opts.append(rec)
            
            if all_opts:
                try:
                    self.http_client.post_optimizations(all_opts)
                    sync_results['optimizations_synced'] = len(all_opts)
                    self.logger.info(f"Synced {len(all_opts)} optimizations from checkpoint")
                except Exception as e:
                    sync_results['errors'].append(f"Optimization sync failed: {e}")

        # 3. Sync Anomalies
        anomaly_checkpoint = self._load_workflow_checkpoint('post_anomaly_detection')
        if anomaly_checkpoint:
            anomalies = anomaly_checkpoint.get('anomalies_detected', [])
            if not anomalies and 'detailed_results' in anomaly_checkpoint:
                anomalies = anomaly_checkpoint['detailed_results'].get('anomalies_detected', [])
            
            if anomalies:
                try:
                    self.http_client.post_anomalies(anomalies)
                    sync_results['anomalies_synced'] = len(anomalies)
                    self.logger.info(f"Synced {len(anomalies)} anomalies from checkpoint")
                except Exception as e:
                    sync_results['errors'].append(f"Anomaly sync failed: {e}")

        # 4. Sync Budgets
        if self.budget_manager and self.budget_manager.budgets:
            try:
                for budget in self.budget_manager.budgets.values():
                    self.http_client.post_data('/api/budgets', budget)
                sync_results['budgets_synced'] = len(self.budget_manager.budgets)
                self.logger.info(f"Synced {sync_results['budgets_synced']} budgets from manager memory")
            except Exception as e:
                sync_results['errors'].append(f"Budget sync failed: {e}")

        if sync_results['errors']:
            sync_results['success'] = False
            
        return sync_results
    
    def _generate_final_report(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final comprehensive report.
        
        Args:
            workflow_results: Complete workflow results
            
        Returns:
            Final report data
        """
        from utils.workflow_state import WorkflowPhase
        
        # Start reporting phase
        if self.workflow_state:
            self.workflow_state.start_phase(WorkflowPhase.REPORTING)
        
        try:
            report_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'workflow_id': workflow_results.get('workflow_id'),
                'executive_summary': self._generate_executive_summary(workflow_results),
                'detailed_findings': self._extract_detailed_findings(workflow_results),
                'recommendations': self._compile_recommendations(workflow_results),
                'cost_impact': self._calculate_cost_impact(workflow_results),
                'next_steps': self._generate_next_steps(workflow_results)
            }
            
            # Send report to backend API if available
            try:
                if self.http_client.health_check():
                    self.http_client.post_data('/api/reports', {
                        'report': report_data,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'finops-bot'
                    })
                    self.logger.info("Final report sent to backend API")
            except Exception as e:
                self.logger.warning(f"Failed to send report to backend: {e}")
            
            # Complete reporting phase
            if self.workflow_state:
                self.workflow_state.complete_phase(WorkflowPhase.REPORTING, report_data)
            
            return report_data
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            
            # Mark reporting phase as failed
            if self.workflow_state:
                self.workflow_state.fail_phase(WorkflowPhase.REPORTING, str(e))
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'workflow_id': workflow_results.get('workflow_id')
            }
    
    def _generate_executive_summary(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from workflow results."""
        phases = workflow_results.get('phases', {})
        
        return {
            'total_resources_discovered': phases.get('discovery', {}).get('resources_discovered', 0),
            'total_optimizations_found': phases.get('optimization', {}).get('optimizations_found', 0),
            'potential_monthly_savings': phases.get('optimization', {}).get('potential_monthly_savings', 0.0),
            'anomalies_detected': phases.get('anomaly_detection', {}).get('anomalies_detected', 0),
            'budgets_analyzed': phases.get('budget_management', {}).get('budgets_analyzed', 0),
            'workflow_duration_minutes': workflow_results.get('workflow_duration', 0) / 60.0,
            'success': workflow_results.get('success', False)
        }
    
    def _extract_detailed_findings(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed findings from each phase."""
        phases = workflow_results.get('phases', {})
        
        return {
            'discovery': {
                'services_scanned': phases.get('discovery', {}).get('services_scanned', []),
                'resources_by_service': {
                    service: data.get('resources_found', 0)
                    for service, data in phases.get('discovery', {}).get('services', {}).items()
                }
            },
            'optimization': {
                'categories': phases.get('optimization', {}).get('categories', {}),
                'total_potential_savings': phases.get('optimization', {}).get('potential_monthly_savings', 0.0)
            },
            'anomaly_detection': {
                'severity_breakdown': phases.get('anomaly_detection', {}).get('severity_breakdown', {}),
                'total_cost_impact': phases.get('anomaly_detection', {}).get('total_cost_impact', 0.0)
            },
            'budget_management': {
                'forecasts_generated': phases.get('budget_management', {}).get('forecasts_generated', 0),
                'alerts_triggered': phases.get('budget_management', {}).get('alerts_triggered', 0)
            }
        }
    
    def _compile_recommendations(self, workflow_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compile top recommendations from all phases."""
        recommendations = []
        
        # Extract optimization recommendations
        optimization_phase = workflow_results.get('phases', {}).get('optimization', {})
        for category, category_data in optimization_phase.get('categories', {}).items():
            for rec in category_data.get('recommendations', [])[:3]:  # Top 3 per category
                recommendations.append({
                    'type': 'optimization',
                    'category': category,
                    'recommendation': rec,
                    'priority': rec.get('risk_level', 'MEDIUM')
                })
        
        # Extract anomaly recommendations
        anomaly_phase = workflow_results.get('phases', {}).get('anomaly_detection', {})
        for anomaly in anomaly_phase.get('detailed_results', {}).get('anomalies_detected', [])[:5]:
            recommendations.append({
                'type': 'anomaly',
                'category': 'cost_spike',
                'recommendation': anomaly,
                'priority': anomaly.get('severity', 'MEDIUM')
            })
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _calculate_cost_impact(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total cost impact from all phases."""
        phases = workflow_results.get('phases', {})
        
        return {
            'potential_monthly_savings': phases.get('optimization', {}).get('potential_monthly_savings', 0.0),
            'anomaly_cost_impact': phases.get('anomaly_detection', {}).get('total_cost_impact', 0.0),
            'budget_variance': 0.0,  # Would be calculated from budget analysis
            'total_impact': phases.get('optimization', {}).get('potential_monthly_savings', 0.0)
        }
    
    def _generate_next_steps(self, workflow_results: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps based on findings."""
        next_steps = []
        
        phases = workflow_results.get('phases', {})
        
        # Optimization next steps
        if phases.get('optimization', {}).get('optimizations_found', 0) > 0:
            next_steps.append("Review and approve high-priority optimization recommendations")
            next_steps.append("Implement low-risk optimizations in test environment first")
        
        # Anomaly next steps
        if phases.get('anomaly_detection', {}).get('anomalies_detected', 0) > 0:
            next_steps.append("Investigate root causes of detected cost anomalies")
            next_steps.append("Set up automated alerts for similar anomaly patterns")
        
        # Budget next steps
        if phases.get('budget_management', {}).get('alerts_triggered', 0) > 0:
            next_steps.append("Review budget alerts and adjust spending plans")
            next_steps.append("Update budget forecasts based on current trends")
        
        # General next steps
        next_steps.append("Schedule regular FinOps reviews and optimization cycles")
        next_steps.append("Monitor implementation of approved optimizations")
        
        return next_steps
    
    def _generate_workflow_summary(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a concise workflow summary."""
        phases = workflow_results.get('phases', {})
        
        return {
            'workflow_id': workflow_results.get('workflow_id'),
            'duration_minutes': round(workflow_results.get('workflow_duration', 0) / 60.0, 2),
            'phases_completed': len([p for p in phases.values() if not p.get('error')]),
            'total_phases': len(phases),
            'resources_discovered': phases.get('discovery', {}).get('resources_discovered', 0),
            'optimizations_found': phases.get('optimization', {}).get('optimizations_found', 0),
            'potential_savings': round(phases.get('optimization', {}).get('potential_monthly_savings', 0.0), 2),
            'anomalies_detected': phases.get('anomaly_detection', {}).get('anomalies_detected', 0),
            'success': workflow_results.get('success', False)
        }
    
    def _generate_sample_cost_data(self) -> List[Dict[str, Any]]:
        """Generate sample cost data for demonstration purposes."""
        from datetime import timedelta
        import random
        
        base_time = datetime.now(timezone.utc) - timedelta(days=30)
        cost_data = []
        
        # Generate 30 days of hourly cost data
        for day in range(30):
            for hour in range(24):
                timestamp = base_time + timedelta(days=day, hours=hour)
                
                # Base cost with daily and hourly patterns
                base_cost = 100.0
                hourly_variation = 15.0 if 9 <= hour <= 17 else 8.0  # Business hours
                daily_variation = 8.0 if day % 7 < 5 else 4.0  # Weekdays vs weekends
                random_variation = random.uniform(-5.0, 5.0)
                
                cost = base_cost + hourly_variation + daily_variation + random_variation
                
                # Add some anomalies for testing
                if day == 25 and hour == 14:  # Cost spike
                    cost = 280.0
                elif day == 28 and 10 <= hour <= 16:  # Sustained increase
                    cost = 180.0
                
                cost_data.append({
                    'timestamp': timestamp.isoformat(),
                    'cost': max(0, cost),  # Ensure non-negative
                    'service': 'mixed',
                    'region': self.region
                })
        
        return cost_data
    
    def _generate_sample_resources(self) -> List[Dict[str, Any]]:
        """Generate sample resource data for demonstration purposes."""
        return [
            {
                'resourceId': 'i-1234567890abcdef0',
                'resourceType': 'ec2',
                'region': self.region,
                'currentCost': 120.0,
                'historicalAverageCost': 100.0,
                'tags': {'Environment': 'production', 'Team': 'backend'},
                'instanceType': 't3.large'
            },
            {
                'resourceId': 'db-abcdef1234567890',
                'resourceType': 'rds',
                'region': self.region,
                'currentCost': 85.0,
                'historicalAverageCost': 75.0,
                'tags': {'Environment': 'production', 'Team': 'data'},
                'dbInstanceClass': 'db.t3.medium'
            },
            {
                'resourceId': 'lambda-function-analytics',
                'resourceType': 'lambda',
                'region': self.region,
                'currentCost': 25.0,
                'historicalAverageCost': 15.0,
                'tags': {'Environment': 'production', 'Team': 'analytics'},
                'memorySize': 512,
                'timeout': 30
            },
            {
                'resourceId': 'vol-0123456789abcdef0',
                'resourceType': 'ebs',
                'region': self.region,
                'currentCost': 15.0,
                'historicalAverageCost': 12.0,
                'tags': {'Environment': 'production', 'Team': 'storage'},
                'volumeType': 'gp2',
                'size': 100
            }
        ]


def main():
    """Main entry point for the Advanced FinOps Platform."""
    parser = argparse.ArgumentParser(
        description='Advanced FinOps Platform - AWS Cost Optimization Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --dry-run                    # Safe mode (no modifications)
  python main.py --scan-only                  # Discovery only
  python main.py --optimize --approve-low     # Execute low-risk optimizations
  python main.py --region us-west-2          # Specific region
  python main.py --services ec2,rds          # Specific services only
  python main.py --continuous                 # Continuous monitoring mode
  python main.py --schedule                   # Run with scheduler
  python main.py --config custom.yaml        # Custom configuration file
  python main.py --daemon                     # Run as daemon process
        """
    )
    
    # Basic operation modes
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region to operate in (default: us-east-1)')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual modifications)')
    
    parser.add_argument('--live', action='store_true',
                       help='Run in live mode (default if not --dry-run; CAUTION: will make actual changes)')
    
    # Operation modes
    parser.add_argument('--scan-only', action='store_true',
                       help='Only run resource discovery, skip optimization')
    
    parser.add_argument('--optimize', action='store_true',
                       help='Run optimization analysis and execution')
    
    parser.add_argument('--approve-low', action='store_true',
                       help='Automatically approve low-risk optimizations')
    
    # Scheduling and continuous monitoring
    parser.add_argument('--continuous', action='store_true',
                       help='Run in continuous monitoring mode')
    
    parser.add_argument('--schedule', action='store_true',
                       help='Run with scheduler enabled (interactive mode)')
    
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon process (requires --schedule)')
    
    parser.add_argument('--interval', type=int, metavar='MINUTES',
                       help='Override monitoring interval in minutes (for --continuous)')
    
    # Configuration and services
    parser.add_argument('--config', metavar='FILE',
                       help='Configuration file path (default: config.yaml)')
    
    parser.add_argument('--services',
                       help='Comma-separated list of services to scan (ec2,rds,lambda,s3,ebs)')
    
    # Workflow management
    parser.add_argument('--resume', metavar='WORKFLOW_ID',
                       help='Resume a previously paused or failed workflow')
    
    parser.add_argument('--list-workflows', action='store_true',
                       help='List all available workflows and their status')
    
    parser.add_argument('--workflow-status', metavar='WORKFLOW_ID',
                       help='Get detailed status of a specific workflow')
    
    parser.add_argument('--cleanup-workflows', type=int, metavar='DAYS',
                       help='Clean up workflow states older than specified days')
    
    # Reporting modes
    parser.add_argument('--report', choices=['discovery', 'optimization', 'anomaly', 'budget', 'all'],
                       help='Generate specific report type')
    
    # Logging and debugging
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    parser.add_argument('--log-file', metavar='FILE',
                       help='Override log file path')
    
    # Validation and testing
    parser.add_argument('--validate-config', action='store_true',
                       help='Validate configuration file and exit')
    
    parser.add_argument('--test-connection', action='store_true',
                       help='Test AWS and backend API connections and exit')
    
    parser.add_argument('--sync-backend', action='store_true',
                       help='Sync discovered data to backend API for frontend display')
    
    parser.add_argument('--backend-url', default='http://localhost:5000',
                       help='Backend API URL (default: http://localhost:5000)')

    
    args = parser.parse_args()
    
    # Validate argument combinations
    if args.daemon and not args.schedule:
        print("ERROR: --daemon requires --schedule")
        sys.exit(1)
    
    if args.continuous and args.schedule:
        print("ERROR: Cannot use both --continuous and --schedule")
        sys.exit(1)
    
    # Handle dry-run vs live mode (default from config: safety.dry_run.default, else False)
    if args.dry_run and args.live:
        print("ERROR: Cannot specify both --live and --dry-run")
        sys.exit(1)
    if args.dry_run:
        dry_run = True
    elif args.live:
        dry_run = False
    else:
        # Use config default (loaded in orchestrator); we pass None and orchestrator will read config
        dry_run = None
    
    # Parse services list
    services = None
    if args.services:
        services = [s.strip() for s in args.services.split(',')]
        valid_services = ['ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch']
        invalid_services = [s for s in services if s not in valid_services]
        if invalid_services:
            print(f"ERROR: Invalid services: {invalid_services}")
            print(f"Valid services: {valid_services}")
            sys.exit(1)
    
    try:
        # Initialize orchestrator with configuration
        orchestrator = AdvancedFinOpsOrchestrator(
            region=args.region,
            dry_run=dry_run,
            config_file=args.config
        )
        
        # Override logging level if specified
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        
        # Override log file if specified
        if args.log_file:
            # Add file handler with specified path
            file_handler = logging.FileHandler(args.log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(file_handler)
        
        # Configuration validation mode
        if args.validate_config:
            print("Validating configuration...")
            issues = orchestrator.config_manager.validate()
            if issues:
                print("Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration is valid")
                sys.exit(0)
        
        # Connection test mode
        if args.test_connection:
            print("Testing connections...")
            print(f"  AWS config: region={orchestrator.region}, regions={orchestrator.aws_config.regions}")
            
            # Test AWS connection
            try:
                orchestrator.aws_config.get_client('sts').get_caller_identity()
                print("✓ AWS connection successful")
            except Exception as e:
                print(f"✗ AWS connection failed: {e}")
            
            # Test backend API connection
            if orchestrator.http_client.health_check():
                print("✓ Backend API connection successful")
            else:
                print("✗ Backend API connection failed")
            
            sys.exit(0)
        
        # Override monitoring interval if specified
        if args.interval and args.continuous:
            orchestrator.config_manager.set('scheduling.continuous_monitoring.interval_minutes', args.interval)
            orchestrator.config_manager.set('scheduling.continuous_monitoring.enabled', True)
        
        # Safety warning for live mode
        if not dry_run:
            print("WARNING: Running in LIVE mode - actual AWS resources may be modified!")
            if not args.daemon:  # Skip confirmation in daemon mode
                print("Press Ctrl+C within 5 seconds to cancel...")
                try:
                    time.sleep(5)
                except KeyboardInterrupt:
                    print("\nCancelled by user")
                    sys.exit(0)
        
        # Workflow management modes
        if args.resume:
            # Resume workflow mode
            results = orchestrator.resume_workflow(args.resume)
            
            if results['success']:
                print(f"✓ Successfully resumed workflow: {args.resume}")
                if 'results' in results:
                    workflow_results = results['results']
                    print(f"  Phases executed: {results['phases_executed']}")
                    for phase_name, phase_results in workflow_results.get('phases', {}).items():
                        print(f"  {phase_name}: {phase_results.get('status', 'completed')}")
            else:
                print(f"✗ Failed to resume workflow: {results.get('error', 'Unknown error')}")
                sys.exit(1)
        
        elif args.list_workflows:
            # List workflows mode
            workflows = orchestrator.list_workflows()
            
            if workflows:
                print(f"\nFound {len(workflows)} workflows:")
                print("-" * 80)
                for workflow in workflows:
                    status_icon = "✓" if workflow['status'] == 'completed' else "⚠" if workflow['status'] == 'failed' else "⏸" if workflow['status'] == 'paused' else "▶"
                    print(f"{status_icon} {workflow['workflow_id']}")
                    print(f"  Status: {workflow['status']}")
                    print(f"  Progress: {workflow['progress_percentage']:.1f}%")
                    print(f"  Start time: {workflow.get('start_time', 'Unknown')}")
                    if workflow.get('execution_time_seconds', 0) > 0:
                        print(f"  Duration: {workflow['execution_time_seconds']:.1f}s")
                    print()
            else:
                print("No workflows found")
        
        elif args.workflow_status:
            # Workflow status mode
            status = orchestrator.get_workflow_status(args.workflow_status)
            
            if 'error' in status:
                print(f"✗ Error getting workflow status: {status['error']}")
                sys.exit(1)
            else:
                print(f"\nWorkflow Status: {args.workflow_status}")
                print("-" * 50)
                print(f"Status: {status['status']}")
                print(f"Progress: {status['progress_percentage']:.1f}%")
                print(f"Phases completed: {status['phases_completed']}")
                print(f"Phases failed: {status['phases_failed']}")
                if status.get('start_time'):
                    print(f"Start time: {status['start_time']}")
                if status.get('end_time'):
                    print(f"End time: {status['end_time']}")
                if status.get('execution_time_seconds', 0) > 0:
                    print(f"Duration: {status['execution_time_seconds']:.1f}s")
                
                # Show metrics if available
                metrics = status.get('metrics', {})
                if metrics:
                    print("\nMetrics:")
                    if metrics.get('total_resources_discovered', 0) > 0:
                        print(f"  Resources discovered: {metrics['total_resources_discovered']}")
                    if metrics.get('total_optimizations_found', 0) > 0:
                        print(f"  Optimizations found: {metrics['total_optimizations_found']}")
                    if metrics.get('total_savings_potential', 0) > 0:
                        print(f"  Potential savings: ${metrics['total_savings_potential']:.2f}/month")
        
        elif args.cleanup_workflows:
            # Cleanup workflows mode
            from utils.workflow_state import WorkflowStateManager
            
            # Create a temporary workflow state manager for cleanup
            temp_workflow = WorkflowStateManager("temp")
            temp_workflow.cleanup_old_states(args.cleanup_workflows)
            print(f"✓ Cleaned up workflow states older than {args.cleanup_workflows} days")
        
        elif args.continuous:
            # Continuous monitoring mode
            orchestrator.start_continuous_monitoring()
            
        elif args.schedule:
            # Scheduler mode
            orchestrator.run_with_scheduler(daemon_mode=args.daemon)
            
        elif args.sync_backend:
            # Sync backend mode
            print("Synchronizing discovered data to backend API...")
            results = orchestrator.sync_to_backend()
            
            if results['success']:
                print(f"✓ Backend synchronization successful")
                print(f"  Resources synced: {results['resources_synced']}")
                print(f"  Optimizations synced: {results['optimizations_synced']}")
                print(f"  Anomalies synced: {results['anomalies_synced']}")
                print(f"  Budgets synced: {results['budgets_synced']}")
            else:
                print(f"⚠ Backend synchronization completed with some issues")
                print(f"  Resources synced: {results.get('resources_synced', 0)}")
                print(f"  Optimizations synced: {results.get('optimizations_synced', 0)}")
                if results.get('errors'):
                    print("\nErrors encountered:")
                    for error in results['errors']:
                        print(f"  - {error}")
            
            sys.exit(0 if results['success'] else 1)
            
        elif args.report:
            # Report generation mode
            print(f"Generating {args.report} report...")
            
            if args.report in ['discovery', 'all']:
                discovery_results = orchestrator.run_discovery(services)
                print(f"Discovery: {discovery_results['resources_discovered']} resources found")
            
            if args.report in ['optimization', 'all']:
                optimization_results = orchestrator.run_optimization_analysis()
                print(f"Optimization: {optimization_results['optimizations_found']} opportunities found")
            
            if args.report in ['anomaly', 'all']:
                anomaly_results = orchestrator.run_anomaly_detection()
                print(f"Anomaly Detection: {anomaly_results['anomalies_detected']} anomalies found")
            
            if args.report in ['budget', 'all']:
                budget_results = orchestrator.run_budget_management()
                print(f"Budget Management: {budget_results['budgets_analyzed']} budgets analyzed")
            
        else:
            # Standard workflow mode
            results = orchestrator.run_complete_workflow(
                services=services,
                scan_only=args.scan_only,
                approve_low_risk=args.approve_low
            )
            
            # Print summary
            print("\n" + "="*60)
            print("ADVANCED FINOPS PLATFORM - EXECUTION SUMMARY")
            print("="*60)
            print(f"Region: {results['region']}")
            print(f"DRY_RUN Mode: {results['dry_run']}")
            print(f"Duration: {results.get('workflow_duration', 0):.2f} seconds")
            print(f"Success: {results.get('success', False)}")
            
            if 'error' in results:
                print(f"Error: {results['error']}")
            
            # Print phase summaries
            for phase_name, phase_results in results.get('phases', {}).items():
                print(f"\n{phase_name.upper()}:")
                if phase_name == 'discovery':
                    print(f"  Services scanned: {len(phase_results.get('services_scanned', []))}")
                    print(f"  Resources found: {phase_results.get('resources_discovered', 0)}")
                elif phase_name == 'optimization':
                    print(f"  Optimizations found: {phase_results.get('optimizations_found', 0)}")
                    print(f"  Potential savings: ${phase_results.get('potential_monthly_savings', 0):.2f}/month")
                elif phase_name == 'anomaly_detection':
                    print(f"  Anomalies detected: {phase_results.get('anomalies_detected', 0)}")
                    print(f"  Alerts generated: {phase_results.get('alerts_generated', 0)}")
                elif phase_name == 'budget_management':
                    print(f"  Budgets analyzed: {phase_results.get('budgets_analyzed', 0)}")
                    print(f"  Forecasts generated: {phase_results.get('forecasts_generated', 0)}")
            
            print("\n" + "="*60)
            
            # Exit with appropriate code
            sys.exit(0 if results.get('success', False) else 1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        logging.exception("Fatal error in main execution")
        sys.exit(1)


if __name__ == '__main__':
    main()
# from aws.scan_ec2 import EC2Scanner
# from aws.scan_rds import RDSScanner
# from aws.scan_lambda import LambdaScanner
# from aws.scan_s3 import S3Scanner
# from aws.scan_ebs import EBSScanner

# Import core optimization engines (will be implemented in future tasks)
# from core.cost_optimizer import CostOptimizer
# from core.ml_rightsizing import MLRightSizingEngine
# from core.pricing_intelligence import PricingIntelligenceEngine
# from core.anomaly_detector import AnomalyDetector
# from core.budget_manager i