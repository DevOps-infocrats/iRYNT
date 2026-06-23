#!/usr/bin/env python3
"""
VIL Mobile API - Comprehensive Testing Script
Tests all endpoints and documents results

Run: python api_tester.py
"""

import json
import sys
import time
from datetime import datetime, timedelta
import base64
from io import BytesIO
from pathlib import Path

# Attempt to import requests, if not available, provide helpful error
try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not installed. Install with: pip install requests")
    sys.exit(1)

class APITester:
    def __init__(self, base_url="http://localhost:5000", debug=False):
        self.base_url = base_url
        self.debug = debug
        self.session = requests.Session()
        self.results = []
        self.access_token = None
        self.refresh_token = None
        self.test_user_id = None
        self.errors = []
        
    def log(self, message):
        """Log message"""
        print(message)
    
    def test_endpoint(self, method, endpoint, name, data=None, headers=None, expected_status=None, require_auth=False):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        full_headers = headers or {}
        
        # Add auth header if required
        if require_auth and self.access_token:
            full_headers['Authorization'] = f'Bearer {self.access_token}'
        
        full_headers['Content-Type'] = 'application/json'
        full_headers['Accept'] = 'application/json'
        
        start_time = time.time()
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=full_headers, json=data, timeout=5)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=full_headers, json=data, timeout=5)
            elif method.upper() == 'PUT':
                response = self.session.put(url, headers=full_headers, json=data, timeout=5)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, headers=full_headers, json=data, timeout=5)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=full_headers, json=data, timeout=5)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Check if response is successful
            is_success = response.status_code < 400
            
            # Determine result
            if expected_status and response.status_code != expected_status:
                result = "WARN"
                message = f"Expected {expected_status}, got {response.status_code}"
            elif is_success:
                result = "PASS"
                message = f"Success - {response.status_code} OK"
            else:
                result = "FAIL"
                message = f"Error - {response.status_code}"
            
            result_entry = {
                'name': name,
                'endpoint': endpoint,
                'method': method.upper(),
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'result': result,
                'message': message,
                'response': response_data,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result_entry)
            
            # Log result
            status_indicator = "✓" if result == "PASS" else "✗" if result == "FAIL" else "⚠"
            self.log(f"{status_indicator} [{result}] {method.upper()} {endpoint} - {response.status_code} ({response_time:.0f}ms)")
            
            if self.debug and result != "PASS":
                self.log(f"  Request: {json.dumps(data, indent=2) if data else 'No body'}")
                self.log(f"  Response: {json.dumps(response_data, indent=2) if isinstance(response_data, dict) else response_data}")
            
            return response, response_data
            
        except requests.exceptions.ConnectionError:
            self.log(f"✗ [FAIL] {method.upper()} {endpoint} - Connection refused")
            self.log(f"  ** Make sure Flask app is running on {self.base_url}")
            error = {
                'endpoint': endpoint,
                'error': 'Connection refused',
                'message': f'Could not connect to {self.base_url}'
            }
            self.errors.append(error)
            self.results.append({
                'name': name,
                'endpoint': endpoint,
                'method': method.upper(),
                'status_code': 0,
                'response_time_ms': 0,
                'result': 'FAIL',
                'message': 'Connection refused',
                'response': None,
                'timestamp': datetime.now().isoformat()
            })
            return None, None
        except Exception as e:
            self.log(f"✗ [FAIL] {method.upper()} {endpoint} - {str(e)}")
            error = {
                'endpoint': endpoint,
                'error': type(e).__name__,
                'message': str(e)
            }
            self.errors.append(error)
            self.results.append({
                'name': name,
                'endpoint': endpoint,
                'method': method.upper(),
                'status_code': 0,
                'response_time_ms': 0,
                'result': 'FAIL',
                'message': str(e),
                'response': None,
                'timestamp': datetime.now().isoformat()
            })
            return None, None
    
    def create_dummy_image_base64(self, width=100, height=100):
        """Create a minimal base64-encoded JPEG image"""
        # Create a simple minimal JPEG in base64
        # This is a 1x1 white pixel JPEG
        jpeg_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwwUAxUTAwwSBxMPDw8LCw4RDg4KDw4TCw8UFBcVFBYUFRYVGRkZGBkZGRkZGRkZGRj/2wBDAQICAgICAwUDAwwUEA4IDBQTDAwTGBEPDw8PGxELDw8NDw8PGBkZGBkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8VAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="
        return jpeg_base64

    def generate_test_report(self):
        """Generate test report summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['result'] == 'PASS')
        failed = sum(1 for r in self.results if r['result'] == 'FAIL')
        warning = sum(1 for r in self.results if r['result'] == 'WARN')
        
        report = {
            'title': 'VIL Mobile API - Test Report',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'warnings': warning,
                'pass_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            'results': self.results,
            'errors': self.errors
        }
        
        return report
    
    def save_report(self, filename="api_test_results.json"):
        """Save test report to file"""
        report = self.generate_test_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        self.log(f"\n✓ Test report saved to {filename}")
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("=" * 80)
        self.log("VIL Mobile API - Comprehensive Test Suite")
        self.log("=" * 80)
        self.log(f"Base URL: {self.base_url}")
        self.log(f"Start Time: {datetime.now().isoformat()}")
        self.log("")
        
        # Phase 1: Auth Tests
        self.log("PHASE 1: AUTHENTICATION ENDPOINTS")
        self.log("-" * 80)
        self.test_login()
        self.test_refresh_token()
        self.test_forgot_password()
        self.test_invalid_login()
        self.test_logout()
        
        # Phase 2: Deployment Tests
        self.log("\nPHASE 2: DEPLOYMENT ENDPOINTS")
        self.log("-" * 80)
        self.test_get_current_deployment()
        
        # Phase 3: Vehicle Tests
        self.log("\nPHASE 3: VEHICLE ENDPOINTS")
        self.log("-" * 80)
        self.test_get_current_vehicle()
        
        # Phase 4: Attendance Tests
        self.log("\nPHASE 4: ATTENDANCE ENDPOINTS")
        self.log("-" * 80)
        self.test_attendance_check_in()
        self.test_attendance_check_out()
        self.test_gps_sync()
        
        # Generate report
        self.log("\n" + "=" * 80)
        report = self.generate_test_report()
        self.log(f"Test Summary:")
        self.log(f"  Total Tests: {report['summary']['total_tests']}")
        self.log(f"  Passed: {report['summary']['passed']}")
        self.log(f"  Failed: {report['summary']['failed']}")
        self.log(f"  Warnings: {report['summary']['warnings']}")
        self.log(f"  Pass Rate: {report['summary']['pass_rate']}")
        self.log("=" * 80)
        
        return report
    
    # Auth Tests
    def test_login(self):
        """Test login endpoint"""
        # First try with test credentials
        response, data = self.test_endpoint(
            'POST', '/api/v1/auth/login', 'Login with valid credentials',
            data={
                'email': 'superadmin@example.com',
                'password': 'Admin@321'
            },
            expected_status=200
        )
        
        if response and response.status_code == 200 and isinstance(data, dict):
            if data.get('data', {}).get('access_token'):
                self.access_token = data['data']['access_token']
                self.refresh_token = data['data'].get('refresh_token')
                self.test_user_id = data['data'].get('user', {}).get('id')
                self.log(f"  → Obtained access token")
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        self.test_endpoint(
            'POST', '/api/v1/auth/login', 'Login with invalid credentials',
            data={
                'email': 'invalid@example.com',
                'password': 'wrongpassword'
            },
            expected_status=401
        )
    
    def test_refresh_token(self):
        """Test refresh token endpoint"""
        if not self.refresh_token:
            self.log("⊘ [SKIP] Refresh token test - no token available")
            return
        
        response, data = self.test_endpoint(
            'POST', '/api/v1/auth/refresh', 'Refresh access token',
            data={'refresh_token': self.refresh_token},
            expected_status=200
        )
        
        if response and response.status_code == 200 and isinstance(data, dict):
            if data.get('data', {}).get('access_token'):
                self.access_token = data['data']['access_token']
                self.log(f"  → Updated access token")
    
    def test_forgot_password(self):
        """Test forgot password endpoint"""
        self.test_endpoint(
            'POST', '/api/v1/auth/password/forgot', 'Request password reset',
            data={'email': 'test@example.com'},
            expected_status=200
        )
    
    def test_logout(self):
        """Test logout endpoint"""
        if not self.refresh_token:
            self.log("⊘ [SKIP] Logout test - no refresh token available")
            return
        
        self.test_endpoint(
            'POST', '/api/v1/auth/logout', 'Logout',
            data={'refresh_token': self.refresh_token},
            expected_status=200
        )
    
    # Deployment Tests
    def test_get_current_deployment(self):
        """Test get current deployment endpoint"""
        if not self.access_token:
            self.log("⊘ [SKIP] Get deployment test - not authenticated")
            return
        
        self.test_endpoint(
            'GET', '/api/v1/deployments/current', 'Get current deployment',
            require_auth=True,
            expected_status=200
        )
    
    # Vehicle Tests
    def test_get_current_vehicle(self):
        """Test get current vehicle endpoint"""
        if not self.access_token:
            self.log("⊘ [SKIP] Get vehicle test - not authenticated")
            return
        
        self.test_endpoint(
            'GET', '/api/v1/vehicles/current', 'Get current vehicle',
            require_auth=True,
            expected_status=200
        )
    
    # Attendance Tests
    def test_attendance_check_in(self):
        """Test check-in endpoint"""
        if not self.access_token:
            self.log("⊘ [SKIP] Check-in test - not authenticated")
            return
        
        # Get a driver profile first (would need to be fetched from DB in real scenario)
        # For now, this will likely return 404 but we test the endpoint structure
        dummy_image = self.create_dummy_image_base64()
        
        response, data = self.test_endpoint(
            'POST', '/api/v1/attendance/check-in', 'Check-in',
            data={
                'driver_profile_id': 'test-profile-id',
                'latitude': 19.0760,
                'longitude': 72.8777,
                'accuracy': 10.5,
                'selfie_data': dummy_image,
                'odometer': 45623.5
            },
            require_auth=True
        )
    
    def test_attendance_check_out(self):
        """Test check-out endpoint"""
        if not self.access_token:
            self.log("⊘ [SKIP] Check-out test - not authenticated")
            return
        
        dummy_image = self.create_dummy_image_base64()
        
        response, data = self.test_endpoint(
            'POST', '/api/v1/attendance/check-out', 'Check-out',
            data={
                'driver_profile_id': 'test-profile-id',
                'latitude': 19.0765,
                'longitude': 72.8785,
                'accuracy': 8.2,
                'selfie_data': dummy_image,
                'odometer': 45750.3
            },
            require_auth=True
        )
    
    def test_gps_sync(self):
        """Test GPS sync endpoint"""
        if not self.access_token:
            self.log("⊘ [SKIP] GPS sync test - not authenticated")
            return
        
        response, data = self.test_endpoint(
            'POST', '/api/v1/attendance/gps/sync', 'GPS synchronization',
            data={
                'deployment_id': 'test-deployment-id',
                'coordinates': [
                    {
                        'latitude': 19.0760,
                        'longitude': 72.8777,
                        'timestamp': datetime.now().isoformat() + 'Z',
                        'speed': 45.5,
                        'accuracy': 10.5
                    }
                ]
            },
            require_auth=True
        )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VIL Mobile API Tester')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of API')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--output', default='api_test_results.json', help='Output report filename')
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.url, debug=args.debug)
    report = tester.run_all_tests()
    tester.save_report(args.output)
    
    # Return exit code based on results
    if report['summary']['failed'] > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
