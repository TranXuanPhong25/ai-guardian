"""
Performance testing framework for AI Guardian.
"""
import asyncio
import time
import statistics
import concurrent.futures
from typing import Dict, List, Any, Callable
import aiohttp
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PerformanceResult:
    """Results from performance testing."""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    requests_per_second: float
    errors: List[str]

class PerformanceTester:
    """Performance testing framework for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        
    async def test_endpoint_performance(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        data: Dict = None,
        num_requests: int = 100,
        concurrent_requests: int = 10,
        timeout: int = 30
    ) -> PerformanceResult:
        """
        Test performance of a specific endpoint.
        
        Args:
            endpoint: API endpoint to test
            method: HTTP method
            headers: Request headers
            data: Request data for POST/PUT
            num_requests: Total number of requests to make
            concurrent_requests: Number of concurrent requests
            timeout: Request timeout in seconds
        """
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = []
        successful_requests = 0
        
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def make_request():
                async with semaphore:
                    request_start = time.time()
                    try:
                        async with session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            json=data
                        ) as response:
                            await response.text()  # Read response body
                            request_time = time.time() - request_start
                            response_times.append(request_time)
                            
                            if response.status < 400:
                                nonlocal successful_requests
                                successful_requests += 1
                            else:
                                errors.append(f"HTTP {response.status}: {response.reason}")
                                
                    except Exception as e:
                        request_time = time.time() - request_start
                        response_times.append(request_time)
                        errors.append(str(e))
            
            # Execute requests
            tasks = [make_request() for _ in range(num_requests)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            percentile_95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_time
        else:
            avg_time = median_time = min_time = max_time = percentile_95 = 0
        
        rps = num_requests / total_time if total_time > 0 else 0
        
        return PerformanceResult(
            endpoint=endpoint,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=num_requests - successful_requests,
            average_response_time=avg_time,
            median_response_time=median_time,
            min_response_time=min_time,
            max_response_time=max_time,
            percentile_95=percentile_95,
            requests_per_second=rps,
            errors=list(set(errors))  # Remove duplicates
        )
    
    async def stress_test_endpoint(
        self,
        endpoint: str,
        duration_seconds: int = 60,
        concurrent_requests: int = 50,
        ramp_up_seconds: int = 10
    ) -> Dict[str, Any]:
        """
        Perform stress testing on an endpoint.
        
        Args:
            endpoint: API endpoint to test
            duration_seconds: How long to run the test
            concurrent_requests: Peak number of concurrent requests
            ramp_up_seconds: Time to reach peak concurrency
        """
        url = f"{self.base_url}{endpoint}"
        results = []
        start_time = time.time()
        
        logger.info(f"Starting stress test: {endpoint} for {duration_seconds}s")
        
        async with aiohttp.ClientSession() as session:
            
            async def worker():
                """Worker coroutine that makes requests continuously."""
                local_results = []
                while time.time() - start_time < duration_seconds:
                    request_start = time.time()
                    try:
                        async with session.get(url) as response:
                            await response.text()
                            request_time = time.time() - request_start
                            local_results.append({
                                'timestamp': request_start,
                                'response_time': request_time,
                                'status': response.status,
                                'success': response.status < 400
                            })
                    except Exception as e:
                        request_time = time.time() - request_start
                        local_results.append({
                            'timestamp': request_start,
                            'response_time': request_time,
                            'status': 0,
                            'success': False,
                            'error': str(e)
                        })
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.01)
                
                return local_results
            
            # Ramp up workers gradually
            workers = []
            for i in range(concurrent_requests):
                workers.append(asyncio.create_task(worker()))
                if ramp_up_seconds > 0:
                    await asyncio.sleep(ramp_up_seconds / concurrent_requests)
            
            # Wait for all workers to complete
            worker_results = await asyncio.gather(*workers)
            
            # Flatten results
            for worker_result in worker_results:
                results.extend(worker_result)
        
        # Analyze results
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = total_requests - successful_requests
        
        response_times = [r['response_time'] for r in results]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        median_response_time = statistics.median(response_times) if response_times else 0
        
        # Calculate RPS over time intervals
        interval_size = 10  # 10-second intervals
        rps_over_time = []
        
        for i in range(0, int(duration_seconds), interval_size):
            interval_start = start_time + i
            interval_end = interval_start + interval_size
            
            interval_requests = [
                r for r in results 
                if interval_start <= r['timestamp'] < interval_end
            ]
            
            rps = len(interval_requests) / interval_size
            rps_over_time.append({
                'interval_start': i,
                'requests_per_second': rps,
                'successful_requests': sum(1 for r in interval_requests if r['success'])
            })
        
        return {
            'endpoint': endpoint,
            'duration_seconds': duration_seconds,
            'concurrent_requests': concurrent_requests,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'average_response_time': avg_response_time,
            'median_response_time': median_response_time,
            'rps_over_time': rps_over_time,
            'peak_rps': max(interval['requests_per_second'] for interval in rps_over_time) if rps_over_time else 0
        }
    
    async def run_comprehensive_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance tests on all endpoints."""
        logger.info("Starting comprehensive performance tests")
        
        test_endpoints = [
            {"endpoint": "/health", "method": "GET"},
            {"endpoint": "/health/detailed", "method": "GET"},
            {"endpoint": "/metrics", "method": "GET"},
        ]
        
        results = {}
        
        # Basic performance tests
        for test_config in test_endpoints:
            try:
                result = await self.test_endpoint_performance(
                    endpoint=test_config["endpoint"],
                    method=test_config["method"],
                    num_requests=50,
                    concurrent_requests=5
                )
                results[test_config["endpoint"]] = {
                    'type': 'performance_test',
                    'result': result
                }
                logger.info(f"Completed performance test for {test_config['endpoint']}")
            except Exception as e:
                logger.error(f"Performance test failed for {test_config['endpoint']}: {e}")
                results[test_config["endpoint"]] = {
                    'type': 'performance_test',
                    'error': str(e)
                }
        
        # Light stress test on health endpoint
        try:
            stress_result = await self.stress_test_endpoint(
                endpoint="/health",
                duration_seconds=30,
                concurrent_requests=10,
                ramp_up_seconds=5
            )
            results["/health_stress"] = {
                'type': 'stress_test',
                'result': stress_result
            }
            logger.info("Completed stress test for /health endpoint")
        except Exception as e:
            logger.error(f"Stress test failed: {e}")
            results["/health_stress"] = {
                'type': 'stress_test',
                'error': str(e)
            }
        
        return results

# Global performance tester instance
performance_tester = PerformanceTester()