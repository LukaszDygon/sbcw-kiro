"""
Performance and load testing for SoftBankCashWire backend
Tests system performance under concurrent load with 500+ users
"""
import asyncio
import aiohttp
import time
import statistics
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Any
import json
import random
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:5000"
CONCURRENT_USERS = 500
TEST_DURATION = 60  # seconds
PERFORMANCE_THRESHOLDS = {
    'response_time_p95': 2.0,  # 95th percentile response time in seconds
    'response_time_avg': 0.1,  # Average response time in seconds
    'error_rate': 0.01,  # Maximum 1% error rate
    'throughput_min': 100,  # Minimum requests per second
}

class PerformanceMetrics:
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()
    
    def add_response(self, response_time: float, success: bool):
        with self.lock:
            self.response_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            total_requests = len(self.response_times)
            if total_requests == 0:
                return {}
            
            duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 1
            
            return {
                'total_requests': total_requests,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'error_rate': self.error_count / total_requests,
                'avg_response_time': statistics.mean(self.response_times),
                'p50_response_time': statistics.median(self.response_times),
                'p95_response_time': statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
                'p99_response_time': statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times),
                'min_response_time': min(self.response_times),
                'max_response_time': max(self.response_times),
                'throughput': total_requests / duration,
                'duration': duration
            }

class LoadTestUser:
    def __init__(self, user_id: int, base_url: str):
        self.user_id = user_id
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        
    async def authenticate(self) -> bool:
        """Authenticate user and get token"""
        try:
            async with aiohttp.ClientSession() as session:
                # Mock authentication for load testing
                auth_data = {
                    'email': f'loadtest{self.user_id}@softbank.com',
                    'password': 'loadtest123'
                }
                
                async with session.post(f'{self.base_url}/api/auth/login', json=auth_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.auth_token = data.get('access_token')
                        return True
                    return False
        except Exception:
            return False
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> tuple[bool, float]:
        """Make authenticated request and return success status and response time"""
        start_time = time.time()
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
            
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    async with session.get(f'{self.base_url}{endpoint}', headers=headers) as response:
                        success = 200 <= response.status < 400
                        response_time = time.time() - start_time
                        return success, response_time
                elif method.upper() == 'POST':
                    async with session.post(f'{self.base_url}{endpoint}', json=data, headers=headers) as response:
                        success = 200 <= response.status < 400
                        response_time = time.time() - start_time
                        return success, response_time
                        
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time
    
    async def simulate_user_session(self, metrics: PerformanceMetrics, duration: int):
        """Simulate a user session with various operations"""
        if not await self.authenticate():
            return
        
        end_time = time.time() + duration
        
        # Define user actions with weights
        actions = [
            ('GET', '/api/accounts/balance', None, 0.3),
            ('GET', '/api/transactions/recent', None, 0.2),
            ('GET', '/api/events/active', None, 0.15),
            ('GET', '/api/money-requests/pending', None, 0.1),
            ('POST', '/api/transactions/send', {
                'recipient_email': f'recipient{random.randint(1, 100)}@softbank.com',
                'amount': f'{random.uniform(1, 100):.2f}',
                'note': f'Load test transaction {random.randint(1, 1000)}'
            }, 0.1),
            ('POST', '/api/money-requests/create', {
                'recipient_email': f'recipient{random.randint(1, 100)}@softbank.com',
                'amount': f'{random.uniform(1, 50):.2f}',
                'note': f'Load test request {random.randint(1, 1000)}'
            }, 0.05),
            ('POST', '/api/events/create', {
                'name': f'Load Test Event {random.randint(1, 1000)}',
                'description': 'Load testing event',
                'target_amount': f'{random.uniform(100, 500):.2f}'
            }, 0.05),
            ('GET', '/api/reporting/personal', None, 0.05)
        ]
        
        while time.time() < end_time:
            # Select random action based on weights
            rand = random.random()
            cumulative_weight = 0
            
            for method, endpoint, data, weight in actions:
                cumulative_weight += weight
                if rand <= cumulative_weight:
                    success, response_time = await self.make_request(method, endpoint, data)
                    metrics.add_response(response_time, success)
                    break
            
            # Random delay between requests (0.1 to 2 seconds)
            await asyncio.sleep(random.uniform(0.1, 2.0))

async def run_load_test(concurrent_users: int, duration: int) -> PerformanceMetrics:
    """Run load test with specified number of concurrent users"""
    metrics = PerformanceMetrics()
    metrics.start_time = time.time()
    
    # Create user tasks
    tasks = []
    for i in range(concurrent_users):
        user = LoadTestUser(i, BASE_URL)
        task = asyncio.create_task(user.simulate_user_session(metrics, duration))
        tasks.append(task)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    metrics.end_time = time.time()
    return metrics

def run_concurrent_transaction_test() -> Dict[str, Any]:
    """Test concurrent transaction processing"""
    import requests
    import threading
    from queue import Queue
    
    results = Queue()
    
    def send_transaction(user_id: int):
        try:
            # Mock authentication
            auth_response = requests.post(f'{BASE_URL}/api/auth/login', json={
                'email': f'user{user_id}@softbank.com',
                'password': 'test123'
            })
            
            if auth_response.status_code != 200:
                results.put({'success': False, 'error': 'Auth failed'})
                return
            
            token = auth_response.json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            
            # Send transaction
            start_time = time.time()
            response = requests.post(f'{BASE_URL}/api/transactions/send', 
                json={
                    'recipient_email': f'recipient{user_id % 10}@softbank.com',
                    'amount': '10.00',
                    'note': f'Concurrent test {user_id}'
                },
                headers=headers
            )
            
            response_time = time.time() - start_time
            results.put({
                'success': response.status_code == 200,
                'response_time': response_time,
                'status_code': response.status_code
            })
            
        except Exception as e:
            results.put({'success': False, 'error': str(e)})
    
    # Create threads for concurrent transactions
    threads = []
    for i in range(100):  # 100 concurrent transactions
        thread = threading.Thread(target=send_transaction, args=(i,))
        threads.append(thread)
    
    # Start all threads
    start_time = time.time()
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Collect results
    all_results = []
    while not results.empty():
        all_results.append(results.get())
    
    successful = [r for r in all_results if r.get('success', False)]
    failed = [r for r in all_results if not r.get('success', False)]
    
    return {
        'total_transactions': len(all_results),
        'successful_transactions': len(successful),
        'failed_transactions': len(failed),
        'success_rate': len(successful) / len(all_results) if all_results else 0,
        'total_time': total_time,
        'transactions_per_second': len(all_results) / total_time if total_time > 0 else 0,
        'avg_response_time': statistics.mean([r['response_time'] for r in successful if 'response_time' in r]) if successful else 0
    }

@pytest.mark.performance
def test_system_performance_under_load():
    """Test system performance with 500+ concurrent users"""
    print(f"\nStarting load test with {CONCURRENT_USERS} concurrent users for {TEST_DURATION} seconds...")
    
    # Run the load test
    metrics = asyncio.run(run_load_test(CONCURRENT_USERS, TEST_DURATION))
    results = metrics.get_metrics()
    
    print("\n=== LOAD TEST RESULTS ===")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful Requests: {results['success_count']}")
    print(f"Failed Requests: {results['error_count']}")
    print(f"Error Rate: {results['error_rate']:.2%}")
    print(f"Average Response Time: {results['avg_response_time']:.3f}s")
    print(f"95th Percentile Response Time: {results['p95_response_time']:.3f}s")
    print(f"99th Percentile Response Time: {results['p99_response_time']:.3f}s")
    print(f"Throughput: {results['throughput']:.2f} requests/second")
    print(f"Test Duration: {results['duration']:.2f} seconds")
    
    # Validate performance thresholds
    assert results['p95_response_time'] < PERFORMANCE_THRESHOLDS['response_time_p95'], \
        f"95th percentile response time {results['p95_response_time']:.3f}s exceeds threshold {PERFORMANCE_THRESHOLDS['response_time_p95']}s"
    
    assert results['avg_response_time'] < PERFORMANCE_THRESHOLDS['response_time_avg'], \
        f"Average response time {results['avg_response_time']:.3f}s exceeds threshold {PERFORMANCE_THRESHOLDS['response_time_avg']}s"
    
    assert results['error_rate'] < PERFORMANCE_THRESHOLDS['error_rate'], \
        f"Error rate {results['error_rate']:.2%} exceeds threshold {PERFORMANCE_THRESHOLDS['error_rate']:.2%}"
    
    assert results['throughput'] > PERFORMANCE_THRESHOLDS['throughput_min'], \
        f"Throughput {results['throughput']:.2f} req/s below threshold {PERFORMANCE_THRESHOLDS['throughput_min']} req/s"

@pytest.mark.performance
def test_concurrent_transaction_processing():
    """Test concurrent transaction processing integrity"""
    print("\nTesting concurrent transaction processing...")
    
    results = run_concurrent_transaction_test()
    
    print("\n=== CONCURRENT TRANSACTION TEST RESULTS ===")
    print(f"Total Transactions: {results['total_transactions']}")
    print(f"Successful Transactions: {results['successful_transactions']}")
    print(f"Failed Transactions: {results['failed_transactions']}")
    print(f"Success Rate: {results['success_rate']:.2%}")
    print(f"Total Time: {results['total_time']:.2f}s")
    print(f"Transactions per Second: {results['transactions_per_second']:.2f}")
    print(f"Average Response Time: {results['avg_response_time']:.3f}s")
    
    # Validate concurrent processing
    assert results['success_rate'] > 0.95, f"Success rate {results['success_rate']:.2%} too low for concurrent processing"
    assert results['transactions_per_second'] > 10, f"Transaction throughput {results['transactions_per_second']:.2f} too low"
    assert results['avg_response_time'] < 1.0, f"Average response time {results['avg_response_time']:.3f}s too high"

@pytest.mark.performance
def test_database_performance():
    """Test database performance under load"""
    import requests
    import time
    
    print("\nTesting database performance...")
    
    # Test multiple concurrent database operations
    operations = [
        ('GET', '/api/accounts/balance'),
        ('GET', '/api/transactions/history'),
        ('GET', '/api/events/active'),
        ('GET', '/api/money-requests/pending'),
        ('GET', '/api/reporting/personal')
    ]
    
    response_times = []
    
    for method, endpoint in operations:
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(f'{BASE_URL}{endpoint}')
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            print(f"{method} {endpoint}: {response_time:.3f}s")
            
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
    
    if response_times:
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        print(f"\nDatabase Performance Summary:")
        print(f"Average Response Time: {avg_response_time:.3f}s")
        print(f"Maximum Response Time: {max_response_time:.3f}s")
        
        # Validate database performance
        assert avg_response_time < 0.1, f"Average database response time {avg_response_time:.3f}s too high"
        assert max_response_time < 0.5, f"Maximum database response time {max_response_time:.3f}s too high"

@pytest.mark.performance
def test_memory_usage():
    """Test memory usage under load"""
    import psutil
    import os
    
    print("\nTesting memory usage...")
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"Initial Memory Usage: {initial_memory:.2f} MB")
    
    # Run a smaller load test to monitor memory
    metrics = asyncio.run(run_load_test(50, 30))  # 50 users for 30 seconds
    
    # Get final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print(f"Final Memory Usage: {final_memory:.2f} MB")
    print(f"Memory Increase: {memory_increase:.2f} MB")
    
    # Validate memory usage (should not increase by more than 100MB)
    assert memory_increase < 100, f"Memory increase {memory_increase:.2f} MB too high"

if __name__ == "__main__":
    # Run performance tests directly
    print("Running SoftBankCashWire Performance Tests")
    print("=" * 50)
    
    try:
        test_system_performance_under_load()
        test_concurrent_transaction_processing()
        test_database_performance()
        test_memory_usage()
        
        print("\n" + "=" * 50)
        print("All performance tests passed!")
        
    except Exception as e:
        print(f"\nPerformance test failed: {e}")
        exit(1)