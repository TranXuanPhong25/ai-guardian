#!/usr/bin/env python3
"""
Performance Analyzer - Comprehensive tool to identify weak performance points in AI Guardian
"""

import asyncio
import time
import json
import statistics
import gc
import tracemalloc
import psutil
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from faker import Faker
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    operation_name: str
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    throughput: float  # operations per second
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_usage_percent: float
    iterations: int
    errors: int
    success_rate: float
    
class PerformanceAnalyzer:
    """
    Comprehensive performance analyzer for AI Guardian services
    """
    
    def __init__(self):
        self.faker = Faker(['en_US'])
        self.logger = logging.getLogger(__name__)
        self.results = {}
        
        # Performance thresholds for identifying weak points
        self.thresholds = {
            'pii_detection_min_throughput': 100,  # operations/second
            'masking_min_throughput': 50,         # operations/second
            'database_max_latency': 100,          # milliseconds
            'memory_max_per_operation': 10,       # MB
            'cpu_max_usage': 80,                  # percent
            'max_error_rate': 5                   # percent
        }
    
    async def analyze_pii_detection_performance(self, sample_sizes: List[int] = [100, 500, 1000]) -> Dict[str, PerformanceMetrics]:
        """Analyze PII detection performance across different sample sizes"""
        print("🔍 Analyzing PII Detection Performance...")
        
        try:
            from app.services.notification_service import NotificationService
            service = NotificationService()
        except ImportError:
            print("❌ Cannot import NotificationService - skipping PII detection analysis")
            return {}
        
        results = {}
        
        for sample_size in sample_sizes:
            print(f"  Testing with {sample_size} samples...")
            
            # Generate test data
            test_data = self._generate_mixed_pii_data(sample_size)
            
            # Performance tracking
            times = []
            memory_usage = []
            errors = 0
            
            # Start memory tracking
            tracemalloc.start()
            process = psutil.Process(os.getpid())
            cpu_percent_start = process.cpu_percent()
            
            start_time = time.time()
            
            for i, text in enumerate(test_data):
                iteration_start = time.time()
                
                try:
                    # Measure memory before operation
                    memory_before = process.memory_info().rss / 1024 / 1024  # MB
                    
                    # Perform PII detection
                    detected = await service.detect_pii(text)
                    
                    # Measure memory after operation
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_usage.append(memory_after - memory_before)
                    
                    iteration_time = time.time() - iteration_start
                    times.append(iteration_time)
                    
                    if i % 100 == 0:
                        print(f"    Processed {i+1}/{sample_size} samples...")
                    
                except Exception as e:
                    errors += 1
                    self.logger.error(f"Error in PII detection: {e}")
            
            total_time = time.time() - start_time
            cpu_percent_end = process.cpu_percent()
            
            # Stop memory tracking
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Calculate metrics
            metrics = PerformanceMetrics(
                operation_name=f"pii_detection_{sample_size}_samples",
                total_time=total_time,
                average_time=statistics.mean(times) if times else 0,
                min_time=min(times) if times else 0,
                max_time=max(times) if times else 0,
                throughput=sample_size / total_time if total_time > 0 else 0,
                memory_peak_mb=peak / 1024 / 1024,
                memory_avg_mb=statistics.mean(memory_usage) if memory_usage else 0,
                cpu_usage_percent=(cpu_percent_end + cpu_percent_start) / 2,
                iterations=sample_size,
                errors=errors,
                success_rate=((sample_size - errors) / sample_size) * 100 if sample_size > 0 else 0
            )
            
            results[f"pii_detection_{sample_size}"] = metrics
            print(f"    Throughput: {metrics.throughput:.1f} ops/sec")
            print(f"    Error rate: {100 - metrics.success_rate:.1f}%")
        
        return results
    
    async def analyze_masking_performance(self, sample_sizes: List[int] = [50, 200, 500]) -> Dict[str, PerformanceMetrics]:
        """Analyze PII masking performance"""
        print("🎭 Analyzing PII Masking Performance...")
        
        try:
            from app.services.masking_service import PIIMaskerService
            # Skip masking test due to database dependency
            print("  ⚠️ Skipping masking analysis due to database dependency")
            return {}
        except ImportError:
            print("❌ Cannot import PIIMaskerService - skipping masking analysis")
            return {}
    
    def analyze_memory_patterns(self, test_data_sizes: List[int] = [100, 1000, 5000]) -> Dict[str, Any]:
        """Analyze memory usage patterns"""
        print("💾 Analyzing Memory Usage Patterns...")
        
        results = {}
        
        for size in test_data_sizes:
            print(f"  Testing memory with {size} data points...")
            
            # Generate test data of various sizes
            test_data = self._generate_mixed_pii_data(size)
            
            # Track memory before
            gc.collect()  # Force garbage collection
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Start memory tracking
            tracemalloc.start()
            
            # Simulate processing the data
            processed_data = []
            for text in test_data:
                # Simulate some processing
                processed_data.append(text.upper() + " PROCESSED")
            
            # Get peak memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = memory_after - memory_before
            
            results[f"memory_test_{size}"] = {
                'data_size': size,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_growth_mb': memory_growth,
                'peak_memory_mb': peak / 1024 / 1024,
                'memory_per_item_kb': (memory_growth * 1024) / size if size > 0 else 0
            }
            
            # Clean up
            del processed_data
            del test_data
            gc.collect()
        
        return results
    
    def analyze_batch_processing_efficiency(self, batch_sizes: List[int] = [10, 50, 100, 500]) -> Dict[str, Any]:
        """Analyze efficiency of different batch sizes"""
        print("📦 Analyzing Batch Processing Efficiency...")
        
        total_items = 1000
        results = {}
        
        for batch_size in batch_sizes:
            print(f"  Testing batch size: {batch_size}")
            
            # Generate test data
            test_data = self._generate_mixed_pii_data(total_items)
            
            start_time = time.time()
            processed_items = 0
            batches_processed = 0
            
            # Process in batches
            for i in range(0, len(test_data), batch_size):
                batch = test_data[i:i + batch_size]
                
                # Simulate batch processing
                batch_start = time.time()
                processed_batch = [text.upper() for text in batch]
                batch_time = time.time() - batch_start
                
                processed_items += len(batch)
                batches_processed += 1
            
            total_time = time.time() - start_time
            
            results[f"batch_size_{batch_size}"] = {
                'batch_size': batch_size,
                'total_items': total_items,
                'batches_processed': batches_processed,
                'total_time': total_time,
                'throughput': total_items / total_time,
                'time_per_batch': total_time / batches_processed if batches_processed > 0 else 0,
                'items_per_second': processed_items / total_time if total_time > 0 else 0
            }
        
        return results
    
    def _generate_mixed_pii_data(self, count: int) -> List[str]:
        """Generate mixed PII test data"""
        data = []
        templates = [
            "Patient {name} was admitted on {date}",
            "Contact {name} at {email} or {phone}",
            "SSN: {ssn} for patient {name}",
            "Credit card {cc} belongs to {name}",
            "Employee {name} works at {org}",
            "Call {name} at {phone} for urgent matters",
            "Email {email} for {name} is active",
            "Patient ID {ssn} - {name} - DOB: {date}",
            "Address: {address} for {name}",
            "Doctor {name} specializes in cardiology"
        ]
        
        for i in range(count):
            template = self.faker.random.choice(templates)
            text = template.format(
                name=self.faker.name(),
                email=self.faker.email(),
                phone=self.faker.phone_number(),
                ssn=self.faker.ssn(),
                cc=self.faker.credit_card_number(),
                org=self.faker.company(),
                date=self.faker.date(),
                address=self.faker.address().replace('\n', ', ')
            )
            data.append(text)
        
        return data
    
    def identify_performance_bottlenecks(self, results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify specific performance bottlenecks based on results"""
        print("🚨 Identifying Performance Bottlenecks...")
        
        bottlenecks = {
            'critical': [],
            'warning': [],
            'optimization_opportunities': []
        }
        
        # Analyze PII detection performance
        for key, metrics in results.get('pii_detection', {}).items():
            if isinstance(metrics, PerformanceMetrics):
                if metrics.throughput < self.thresholds['pii_detection_min_throughput']:
                    bottlenecks['critical'].append(
                        f"PII Detection Throughput: {metrics.throughput:.1f} ops/sec "
                        f"(threshold: {self.thresholds['pii_detection_min_throughput']} ops/sec)"
                    )
                
                if metrics.success_rate < (100 - self.thresholds['max_error_rate']):
                    bottlenecks['critical'].append(
                        f"PII Detection Error Rate: {100 - metrics.success_rate:.1f}% "
                        f"(threshold: {self.thresholds['max_error_rate']}%)"
                    )
                
                if metrics.memory_avg_mb > self.thresholds['memory_max_per_operation']:
                    bottlenecks['warning'].append(
                        f"High Memory Usage in PII Detection: {metrics.memory_avg_mb:.1f} MB per operation "
                        f"(threshold: {self.thresholds['memory_max_per_operation']} MB)"
                    )
        
        # Analyze memory patterns
        memory_results = results.get('memory_analysis', {})
        for key, memory_data in memory_results.items():
            if memory_data.get('memory_per_item_kb', 0) > 50:  # 50KB per item threshold
                bottlenecks['warning'].append(
                    f"High Memory per Item: {memory_data['memory_per_item_kb']:.1f} KB per item in {key}"
                )
        
        # Analyze batch processing
        batch_results = results.get('batch_analysis', {})
        if batch_results:
            best_throughput = max(
                data.get('throughput', 0) for data in batch_results.values()
            )
            
            for key, data in batch_results.items():
                throughput = data.get('throughput', 0)
                if throughput < best_throughput * 0.8:  # 20% less than best
                    bottlenecks['optimization_opportunities'].append(
                        f"Suboptimal Batch Size: {key} - {throughput:.1f} items/sec "
                        f"(best: {best_throughput:.1f} items/sec)"
                    )
        
        return bottlenecks
    
    def generate_optimization_recommendations(self, bottlenecks: Dict[str, List[str]]) -> List[str]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Critical issues
        if bottlenecks['critical']:
            recommendations.append("🚨 CRITICAL OPTIMIZATIONS NEEDED:")
            for issue in bottlenecks['critical']:
                if "PII Detection Throughput" in issue:
                    recommendations.extend([
                        "  • Implement batch processing for PII detection",
                        "  • Add caching for frequently detected patterns",
                        "  • Consider parallel processing for large datasets",
                        "  • Optimize Presidio analyzer configuration"
                    ])
                elif "Error Rate" in issue:
                    recommendations.extend([
                        "  • Add retry mechanisms for failed operations",
                        "  • Improve error handling and logging",
                        "  • Validate input data before processing"
                    ])
        
        # Warning issues
        if bottlenecks['warning']:
            recommendations.append("\n⚠️ PERFORMANCE WARNINGS:")
            for issue in bottlenecks['warning']:
                if "Memory Usage" in issue:
                    recommendations.extend([
                        "  • Implement streaming processing for large datasets",
                        "  • Add memory-efficient data structures",
                        "  • Implement garbage collection optimization",
                        "  • Consider memory pooling for frequent operations"
                    ])
        
        # Optimization opportunities
        if bottlenecks['optimization_opportunities']:
            recommendations.append("\n💡 OPTIMIZATION OPPORTUNITIES:")
            for issue in bottlenecks['optimization_opportunities']:
                if "Batch Size" in issue:
                    recommendations.extend([
                        "  • Implement dynamic batch sizing based on system load",
                        "  • Add batch size auto-tuning",
                        "  • Consider adaptive batching strategies"
                    ])
        
        # General recommendations
        recommendations.extend([
            "\n🔧 GENERAL RECOMMENDATIONS:",
            "  • Implement connection pooling for database operations",
            "  • Add async/await optimization for I/O operations",
            "  • Implement Redis caching for frequent lookups",
            "  • Add performance monitoring and alerting",
            "  • Consider using FastAPI background tasks for heavy operations",
            "  • Implement rate limiting to prevent resource exhaustion"
        ])
        
        return recommendations
    
    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive performance analysis"""
        print("🚀 Starting Comprehensive Performance Analysis...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all analyses
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'python_version': sys.version
            }
        }
        
        # PII Detection Analysis
        try:
            pii_results = await self.analyze_pii_detection_performance()
            all_results['pii_detection'] = pii_results
        except Exception as e:
            print(f"❌ PII Detection analysis failed: {e}")
            all_results['pii_detection'] = {}
        
        # Memory Analysis
        try:
            memory_results = self.analyze_memory_patterns()
            all_results['memory_analysis'] = memory_results
        except Exception as e:
            print(f"❌ Memory analysis failed: {e}")
            all_results['memory_analysis'] = {}
        
        # Batch Processing Analysis
        try:
            batch_results = self.analyze_batch_processing_efficiency()
            all_results['batch_analysis'] = batch_results
        except Exception as e:
            print(f"❌ Batch processing analysis failed: {e}")
            all_results['batch_analysis'] = {}
        
        # Identify bottlenecks
        bottlenecks = self.identify_performance_bottlenecks(all_results)
        all_results['bottlenecks'] = bottlenecks
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(bottlenecks)
        all_results['recommendations'] = recommendations
        
        total_time = time.time() - start_time
        all_results['analysis_duration'] = total_time
        
        # Print summary
        print(f"\n{'='*60}")
        print("📊 PERFORMANCE ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Analysis completed in {total_time:.1f} seconds")
        
        # Print bottlenecks
        if bottlenecks['critical']:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(bottlenecks['critical'])}):")
            for issue in bottlenecks['critical']:
                print(f"  • {issue}")
        
        if bottlenecks['warning']:
            print(f"\n⚠️ WARNINGS ({len(bottlenecks['warning'])}):")
            for issue in bottlenecks['warning']:
                print(f"  • {issue}")
        
        if bottlenecks['optimization_opportunities']:
            print(f"\n💡 OPTIMIZATION OPPORTUNITIES ({len(bottlenecks['optimization_opportunities'])}):")
            for issue in bottlenecks['optimization_opportunities']:
                print(f"  • {issue}")
        
        # Print recommendations
        print(f"\n📋 RECOMMENDATIONS:")
        for rec in recommendations:
            print(rec)
        
        return all_results
    
    def save_results(self, results: Dict[str, Any], filename: Optional[str] = None):
        """Save analysis results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_analysis_{timestamp}.json"
        
        # Convert PerformanceMetrics objects to dict for JSON serialization
        def convert_metrics(obj):
            if isinstance(obj, PerformanceMetrics):
                return asdict(obj)
            elif isinstance(obj, dict):
                return {k: convert_metrics(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_metrics(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_metrics(results)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

async def main():
    """Main function to run performance analysis"""
    analyzer = PerformanceAnalyzer()
    
    try:
        results = await analyzer.run_comprehensive_analysis()
        analyzer.save_results(results)
        
        print(f"\n{'='*60}")
        print("✅ Performance analysis completed successfully!")
        print("Review the saved JSON file for detailed metrics.")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())