#!/usr/bin/env python3
"""
AI Guardian Security and Performance Testing CLI

This script provides a command-line interface for running security and performance tests
on the AI Guardian application.
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.security_testing import security_tester
from app.performance_testing import performance_tester

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def save_results(results: dict, output_file: str = None):
    """Save test results to a file."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_results_{timestamp}.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Failed to save results: {e}")

def print_security_summary(results: dict):
    """Print a summary of security test results."""
    print("\n" + "="*50)
    print("SECURITY TEST SUMMARY")
    print("="*50)
    
    overall_status = results.get('overall_status', 'unknown')
    print(f"Overall Status: {overall_status.upper()}")
    
    # Bandit scan results
    bandit = results.get('bandit_scan', {})
    if bandit.get('status') == 'success':
        print("✅ Bandit Security Scan: PASSED")
    elif bandit.get('status') == 'warning':
        issues = bandit.get('issues', {})
        if isinstance(issues, dict):
            results_data = issues.get('results', [])
            print(f"⚠️  Bandit Security Scan: {len(results_data)} issues found")
        else:
            print("⚠️  Bandit Security Scan: Issues detected")
    else:
        print("❌ Bandit Security Scan: FAILED")
        print(f"   Error: {bandit.get('message', 'Unknown error')}")
    
    # Dependency vulnerabilities
    deps = results.get('dependency_vulnerabilities', {})
    for lang, result in deps.items():
        if result.get('status') == 'success':
            print(f"✅ {lang.title()} Dependencies: SECURE")
        elif result.get('status') == 'warning':
            vulns = result.get('vulnerabilities', [])
            if isinstance(vulns, list):
                print(f"⚠️  {lang.title()} Dependencies: {len(vulns)} vulnerabilities")
            else:
                print(f"⚠️  {lang.title()} Dependencies: Vulnerabilities detected")
        else:
            print(f"❌ {lang.title()} Dependencies: CHECK FAILED")
    
    # Secrets check
    secrets = results.get('secrets_check', {})
    if secrets.get('status') == 'success':
        print("✅ Secret Detection: NO SECRETS FOUND")
    else:
        issues = secrets.get('issues', [])
        print(f"⚠️  Secret Detection: {len(issues)} potential secrets found")
    
    # Environment validation
    env = results.get('environment_validation', {})
    if env.get('status') == 'success':
        print("✅ Environment Configuration: SECURE")
    else:
        issues = env.get('issues', [])
        print(f"⚠️  Environment Configuration: {len(issues)} issues found")
    
    print()

def print_performance_summary(results: dict):
    """Print a summary of performance test results."""
    print("\n" + "="*50)
    print("PERFORMANCE TEST SUMMARY")
    print("="*50)
    
    for endpoint, data in results.items():
        if data.get('type') == 'performance_test':
            result = data.get('result')
            if result:
                print(f"\n📊 {endpoint}")
                print(f"   Total Requests: {result.total_requests}")
                print(f"   Success Rate: {result.successful_requests/result.total_requests*100:.1f}%")
                print(f"   Avg Response Time: {result.average_response_time*1000:.2f}ms")
                print(f"   Requests/Second: {result.requests_per_second:.2f}")
                if result.errors:
                    print(f"   Errors: {len(result.errors)}")
            else:
                print(f"\n❌ {endpoint}: {data.get('error', 'Test failed')}")
        
        elif data.get('type') == 'stress_test':
            result = data.get('result')
            if result:
                print(f"\n🔥 {endpoint} (Stress Test)")
                print(f"   Duration: {result['duration_seconds']}s")
                print(f"   Total Requests: {result['total_requests']}")
                print(f"   Success Rate: {result['success_rate']*100:.1f}%")
                print(f"   Peak RPS: {result['peak_rps']:.2f}")
                print(f"   Avg Response Time: {result['average_response_time']*1000:.2f}ms")
            else:
                print(f"\n❌ {endpoint}: {data.get('error', 'Stress test failed')}")
    
    print()

async def run_security_tests(args):
    """Run security tests."""
    print("Running security tests...")
    results = security_tester.run_all_security_checks()
    
    if args.output:
        save_results(results, args.output)
    
    if not args.quiet:
        print_security_summary(results)
    
    return results

async def run_performance_tests(args):
    """Run performance tests."""
    print("Running performance tests...")
    
    # Override base URL if provided
    if args.url:
        performance_tester.base_url = args.url.rstrip('/')
    
    results = await performance_tester.run_comprehensive_performance_test()
    
    if args.output:
        save_results(results, args.output)
    
    if not args.quiet:
        print_performance_summary(results)
    
    return results

async def run_all_tests(args):
    """Run both security and performance tests."""
    print("Running comprehensive test suite...")
    
    security_results = await run_security_tests(args)
    performance_results = await run_performance_tests(args)
    
    combined_results = {
        'timestamp': datetime.now().isoformat(),
        'security': security_results,
        'performance': performance_results
    }
    
    if args.output:
        save_results(combined_results, args.output)
    
    return combined_results

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Guardian Security and Performance Testing CLI"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Test commands')
    
    # Security tests
    security_parser = subparsers.add_parser('security', help='Run security tests')
    security_parser.add_argument(
        '--output', '-o', 
        help='Output file for results (JSON format)'
    )
    security_parser.add_argument(
        '--quiet', '-q', 
        action='store_true',
        help='Suppress output except errors'
    )
    security_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Performance tests
    perf_parser = subparsers.add_parser('performance', help='Run performance tests')
    perf_parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL for API tests (default: http://localhost:8000)'
    )
    perf_parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    perf_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output except errors'
    )
    perf_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # All tests
    all_parser = subparsers.add_parser('all', help='Run all tests')
    all_parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL for API tests (default: http://localhost:8000)'
    )
    all_parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    all_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output except errors'
    )
    all_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    setup_logging(getattr(args, 'verbose', False))
    
    try:
        if args.command == 'security':
            asyncio.run(run_security_tests(args))
        elif args.command == 'performance':
            asyncio.run(run_performance_tests(args))
        elif args.command == 'all':
            asyncio.run(run_all_tests(args))
        
        return 0
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Test failed with error: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())