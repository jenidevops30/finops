#!/usr/bin/env python3
"""
Seed Data Script for Advanced FinOps Platform

Populates the backend API with rich, realistic mock data across resources,
optimizations, anomalies, budgets, and savings. This makes the dashboard
fully populated and interactive immediately upon backend start.
"""

import requests
import datetime
import sys
import time

BACKEND_URL = "http://localhost:5000"

def check_backend():
    print(f"🔌 Checking backend health at {BACKEND_URL}/health...")
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if res.status_code == 200:
            print("✅ Backend is online and healthy.\n")
            return True
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        print("   Please ensure the backend server is running on port 5000.")
        return False
    return False

def seed_resources():
    print("📦 Seeding resources...")
    resources = [
        {
            'resourceId': 'i-09f19374bd8a12e34',
            'resourceType': 'ec2',
            'region': 'us-east-1',
            'accountId': '123456789012',
            'state': 'running',
            'serviceType': 'ec2',
            'currentCost': 245.50,
            'tags': {'Name': 'Prod-AppServer-01', 'Environment': 'Production', 'Team': 'Backend'},
            'utilizationMetrics': {'cpuUtilization': 4.2, 'memoryUtilization': 12.5}
        },
        {
            'resourceId': 'db-prod-replica-mysql',
            'resourceType': 'rds',
            'region': 'us-east-1',
            'accountId': '987654321098',
            'state': 'available',
            'serviceType': 'rds',
            'currentCost': 412.00,
            'tags': {'Name': 'DB-Replica-01', 'Environment': 'Production', 'Team': 'Data'},
            'utilizationMetrics': {'cpuUtilization': 2.1, 'connectionUtilization': 5.0}
        },
        {
            'resourceId': 'jeni-portfolio',
            'resourceType': 's3',
            'region': 'ap-south-1',
            'accountId': '123456789012',
            'state': 'active',
            'serviceType': 's3',
            'currentCost': 89.20,
            'tags': {'Name': 'Jeni-Portfolio', 'Environment': 'DevOps'},
            'utilizationMetrics': {'storageSizeGB': 3450, 'objectCount': 125000}
        },
        {
            'resourceId': 'vol-08fa8e82b7cf167a',
            'resourceType': 'ebs',
            'region': 'us-west-2',
            'accountId': '987654321098',
            'state': 'unattached',
            'serviceType': 'ebs',
            'currentCost': 45.00,
            'tags': {'Name': 'Orphaned-DataVolume', 'Environment': 'Staging'},
            'utilizationMetrics': {'iops': 0, 'throughput': 0}
        },
        {
            'resourceId': 'lambda-cleanup-logs',
            'resourceType': 'lambda',
            'region': 'us-east-1',
            'accountId': '123456789012',
            'state': 'active',
            'serviceType': 'lambda',
            'currentCost': 15.80,
            'tags': {'Name': 'LogCleanupService', 'Environment': 'Production'},
            'utilizationMetrics': {'invocations': 450, 'durationEfficiency': 45.0}
        }
    ]
    
    # Post resources one by one
    success = 0
    for resource in resources:
        try:
            res = requests.post(f"{BACKEND_URL}/api/resources", json=resource, timeout=5)
            if res.status_code in [200, 201]:
                success += 1
            else:
                print(f"   ⚠️  Failed to seed resource {resource['resourceId']}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"   ❌ Error seeding resource {resource['resourceId']}: {e}")
            
    print(f"   ✅ Successfully seeded {success}/{len(resources)} resources.")

def seed_optimizations():
    print("💡 Seeding optimizations...")
    opts = [
        {
            'optimizationId': 'ec2-i-09f19374bd8a12e34-rightsizing',
            'resourceId': 'i-09f19374bd8a12e34',
            'resourceType': 'ec2',
            'optimizationType': 'rightsizing',
            'title': 'Right-size underutilized AppServer',
            'description': 'Instance CPU is under 5%. Recommend changing instance type from m5.xlarge to t3.medium.',
            'currentCost': 245.50,
            'projectedCost': 61.38,
            'estimatedSavings': 184.12,
            'riskLevel': 'LOW',
            'confidenceScore': 90,
            'implementationEffort': 'Low',
            'recommendedAction': 'Modify EC2 instance type using AWS Console or CLI.',
            'status': 'pending',
            'region': 'us-east-1',
            'accountId': '123456789012',
            'resourceData': {}
        },
        {
            'optimizationId': 'ebs-vol-08fa8e82b7cf167a-cleanup',
            'resourceId': 'vol-08fa8e82b7cf167a',
            'resourceType': 'ebs',
            'optimizationType': 'cleanup',
            'title': 'Delete unattached EBS volume',
            'description': 'EBS volume vol-08fa8e82b7cf167a has been unattached/idle for over 30 days.',
            'currentCost': 45.00,
            'projectedCost': 0.0,
            'estimatedSavings': 45.00,
            'riskLevel': 'LOW',
            'confidenceScore': 95,
            'implementationEffort': 'Low',
            'recommendedAction': 'Create snapshot for safety and delete the volume.',
            'status': 'approved',
            'region': 'us-west-2',
            'accountId': '987654321098',
            'resourceData': {}
        },
        {
            'optimizationId': 'rds-db-prod-replica-mysql-cleanup',
            'resourceId': 'db-prod-replica-mysql',
            'resourceType': 'rds',
            'optimizationType': 'cleanup',
            'title': 'Delete idle MySQL replica database',
            'description': 'Database replica has had 0 connections for 14 days.',
            'currentCost': 412.00,
            'projectedCost': 0.0,
            'estimatedSavings': 412.00,
            'riskLevel': 'MEDIUM',
            'confidenceScore': 85,
            'implementationEffort': 'Medium',
            'recommendedAction': 'Delete database replica after creating a final snapshot.',
            'status': 'pending',
            'region': 'us-east-1',
            'accountId': '987654321098',
            'resourceData': {}
        }
    ]
    
    success = 0
    for opt in opts:
        try:
            res = requests.post(f"{BACKEND_URL}/api/optimizations", json=opt, timeout=5)
            if res.status_code in [200, 201]:
                success += 1
            else:
                print(f"   ⚠️  Failed to seed opt {opt['optimizationId']}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"   ❌ Error seeding opt {opt['optimizationId']}: {e}")
            
    print(f"   ✅ Successfully seeded {success}/{len(opts)} optimizations.")

def seed_anomalies():
    print("🚨 Seeding anomalies...")
    anomalies = [
        {
            'anomalyId': 'anomaly-us-east-1-1',
            'timestamp': (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
            'anomalyType': 'cost_spike',
            'severity': 'CRITICAL',
            'actualCost': 380.00,
            'expectedCost': 120.00,
            'deviationPercentage': 216.67,
            'baselineModel': 'seasonal_decomposition',
            'region': 'us-east-1',
            'accountId': '123456789012',
            'detectedAt': datetime.datetime.now().isoformat(),
            'dataPoint': {'service': 'ec2', 'region': 'us-east-1'}
        },
        {
            'anomalyId': 'anomaly-ap-south-1-2',
            'timestamp': (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
            'anomalyType': 'cost_trend',
            'severity': 'HIGH',
            'actualCost': 140.00,
            'expectedCost': 40.00,
            'deviationPercentage': 250.00,
            'baselineModel': 'simple_moving_average',
            'region': 'ap-south-1',
            'accountId': '123456789012',
            'detectedAt': datetime.datetime.now().isoformat(),
            'dataPoint': {'service': 's3', 'region': 'ap-south-1'}
        }
    ]
    
    try:
        res = requests.post(f"{BACKEND_URL}/api/anomalies/batch", json={'anomalies': anomalies}, timeout=5)
        if res.status_code in [200, 201]:
            print(f"   ✅ Successfully seeded {len(anomalies)} anomalies.")
        else:
            # Fallback to individual POST
            success = 0
            for anom in anomalies:
                res_ind = requests.post(f"{BACKEND_URL}/api/anomalies", json=anom, timeout=5)
                if res_ind.status_code in [200, 201]:
                    success += 1
            print(f"   ✅ Successfully seeded {success}/{len(anomalies)} anomalies (fallback).")
    except Exception as e:
        print(f"   ❌ Error seeding anomalies: {e}")

def seed_budgets():
    print("📅 Seeding budgets...")
    budgets = [
        {
            'budgetId': 'org-2024',
            'budgetType': 'organization',
            'budgetAmount': 1000000,
            'name': 'org-2024',
            'period': 'monthly',
            'currency': 'USD',
            'accountId': '123456789012'
        },
        {
            'budgetId': 'team-backend',
            'budgetType': 'department',
            'budgetAmount': 40000,
            'name': 'team-backend',
            'period': 'monthly',
            'currency': 'USD',
            'accountId': '123456789012'
        },
        {
            'budgetId': 'team-data',
            'budgetType': 'department',
            'budgetAmount': 60000,
            'name': 'team-data',
            'period': 'monthly',
            'currency': 'USD',
            'accountId': '987654321098'
        }
    ]
    
    success = 0
    for budget in budgets:
        try:
            # Try to POST first
            res = requests.post(f"{BACKEND_URL}/api/budgets", json=budget, timeout=5)
            if res.status_code in [200, 201]:
                success += 1
            elif res.status_code == 409:
                # If budget already exists, PUT it
                res_put = requests.put(f"{BACKEND_URL}/api/budgets/{budget['budgetId']}", json=budget, timeout=5)
                if res_put.status_code == 200:
                    success += 1
            else:
                print(f"   ⚠️  Failed to seed budget {budget['budgetId']}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"   ❌ Error seeding budget {budget['budgetId']}: {e}")
            
    print(f"   ✅ Successfully seeded {success}/{len(budgets)} budgets.")

def seed_savings():
    print("💰 Seeding savings records...")
    now = datetime.datetime.now()
    savings_records = [
        {
            'optimizationId': 'ec2-i-09f19374bd8a12e34-rightsizing',
            'savingsAmount': 184.12,
            'serviceType': 'EC2',
            'region': 'us-east-1',
            'accountId': '123456789012',
            'optimizationType': 'rightsizing',
            'previousCost': 245.50,
            'newCost': 61.38,
            'savingsPercentage': 75.0,
            'achievedAt': (now - datetime.timedelta(days=4)).isoformat(),
            'validatedAt': now.isoformat(),
            'annualizedSavings': 184.12 * 12,
            'currency': 'USD',
            'tags': {'Team': 'Backend'}
        },
        {
            'optimizationId': 'ebs-vol-08fa8e82b7cf167a-cleanup',
            'savingsAmount': 45.00,
            'serviceType': 'EBS',
            'region': 'us-west-2',
            'accountId': '987654321098',
            'optimizationType': 'cleanup',
            'previousCost': 45.00,
            'newCost': 0.0,
            'savingsPercentage': 100.0,
            'achievedAt': (now - datetime.timedelta(days=2)).isoformat(),
            'validatedAt': now.isoformat(),
            'annualizedSavings': 45.00 * 12,
            'currency': 'USD',
            'tags': {'Team': 'Staging'}
        },
        {
            'optimizationId': 's3-cleanup-jeni-portfolio-archive',
            'savingsAmount': 62.40,
            'serviceType': 'S3',
            'region': 'ap-south-1',
            'accountId': '123456789012',
            'optimizationType': 'cleanup',
            'previousCost': 89.20,
            'newCost': 26.80,
            'savingsPercentage': 70.0,
            'achievedAt': (now - datetime.timedelta(days=10)).isoformat(),
            'validatedAt': now.isoformat(),
            'annualizedSavings': 62.40 * 12,
            'currency': 'USD',
            'tags': {'Team': 'DevOps'}
        },
        {
            'optimizationId': 'lambda-memory-rightsizing-01',
            'savingsAmount': 12.80,
            'serviceType': 'Lambda',
            'region': 'us-east-1',
            'accountId': '123456789012',
            'optimizationType': 'rightsizing',
            'previousCost': 15.80,
            'newCost': 3.00,
            'savingsPercentage': 81.0,
            'achievedAt': (now - datetime.timedelta(days=1)).isoformat(),
            'validatedAt': now.isoformat(),
            'annualizedSavings': 12.80 * 12,
            'currency': 'USD',
            'tags': {'Team': 'Backend'}
        }
    ]
    
    success = 0
    for record in savings_records:
        try:
            res = requests.post(f"{BACKEND_URL}/api/savings", json=record, timeout=5)
            if res.status_code in [200, 201]:
                success += 1
            else:
                print(f"   ⚠️  Failed to seed savings record: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"   ❌ Error seeding savings record: {e}")
            
    print(f"   ✅ Successfully seeded {success}/{len(savings_records)} savings records.")

def seed_targets():
    print("🎯 Seeding savings targets...")
    now = datetime.datetime.now()
    targets = [
        {
            'targetId': 'target-q1-2024',
            'name': 'Q1 2024 Cost Savings Target',
            'targetAmount': 5000.00,
            'currentAmount': 304.32,
            'startDate': now.isoformat(),
            'endDate': (now + datetime.timedelta(days=90)).isoformat(),
            'description': 'Targeting 15% reduction in EC2 and EBS costs by right-sizing and deleting orphan resources.'
        }
    ]
    
    success = 0
    for target in targets:
        try:
            res = requests.post(f"{BACKEND_URL}/api/savings/targets", json=target, timeout=5)
            if res.status_code in [200, 201]:
                success += 1
            else:
                print(f"   ⚠️  Failed to seed target: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"   ❌ Error seeding target: {e}")
            
    print(f"   ✅ Successfully seeded {success}/{len(targets)} savings targets.")

def main():
    print("=" * 60)
    print("Advanced FinOps Platform Data Seeder")
    print("=" * 60)
    print()
    
    if not check_backend():
        sys.exit(1)
        
    seed_resources()
    seed_optimizations()
    seed_anomalies()
    seed_budgets()
    seed_savings()
    seed_targets()
    
    print("\n🎉 Seeding complete! Check your frontend dashboard to see the populated data.")
    print("   👉 Dashboard: http://localhost:3000")
    print("   👉 Savings tab: http://localhost:3000/savings")
    print("=" * 60)

if __name__ == '__main__':
    main()
