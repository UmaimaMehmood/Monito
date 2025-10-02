import urllib.request as urllib
import urllib.error
import ssl
import time
import json
import os
from datetime import datetime
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SiteConnectivityChecker:
    def __init__(self):
        self.history = []
        self.log_file = "connectivity_log.json"
        self.load_history()
    
    def load_history(self):
        """Load historical data from log file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def save_to_log(self, data):
        """Save check results to log file"""
        self.history.append(data)
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.history, f, indent=2)
            print(f"✓ Results saved to {self.log_file}")
        except Exception as e:
            print(f"✗ Error saving to log: {e}")
    
    def check_single_site(self, url, search_content=None, timeout=10):
        """Check a single site with comprehensive analysis"""
        print(f"\n{'='*60}")
        print(f"Checking: {url}")
        print(f"{'='*60}")
        
        result = {
            'url': url,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'unknown',
            'response_code': None,
            'response_time': None,
            'ssl_valid': None,
            'content_found': None,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            # Create request with headers
            req = urllib.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Check SSL certificate
            if url.startswith('https://'):
                result['ssl_valid'] = self.check_ssl_certificate(url)
            
            # Make request
            response = urllib.urlopen(req, timeout=timeout)
            response_time = time.time() - start_time
            
            result['response_code'] = response.getcode()
            result['response_time'] = round(response_time, 3)
            result['status'] = 'success'
            
            # Display results
            print(f"✓ Status: CONNECTED")
            print(f"✓ Response Code: {response.getcode()} - {self.interpret_status_code(response.getcode())}")
            print(f"✓ Response Time: {response_time:.3f} seconds")
            
            if result['ssl_valid'] is not None:
                ssl_status = "Valid" if result['ssl_valid'] else "Invalid/Expired"
                print(f"✓ SSL Certificate: {ssl_status}")
            
            # Display headers
            print(f"\nResponse Headers:")
            print(f"{'-'*60}")
            for header, value in response.headers.items():
                print(f"{header}: {value}")
            
            # Check for specific content
            if search_content:
                page_content = response.read().decode('utf-8', errors='ignore')
                content_found = search_content in page_content
                result['content_found'] = content_found
                status = "FOUND" if content_found else "NOT FOUND"
                print(f"\n✓ Content Search: '{search_content}' - {status}")
            
        except urllib.error.HTTPError as e:
            response_time = time.time() - start_time
            result['status'] = 'http_error'
            result['response_code'] = e.code
            result['response_time'] = round(response_time, 3)
            result['error'] = str(e)
            
            print(f"✗ HTTP Error: {e.code} - {self.interpret_status_code(e.code)}")
            print(f"✗ Response Time: {response_time:.3f} seconds")
            
        except urllib.error.URLError as e:
            response_time = time.time() - start_time
            result['status'] = 'url_error'
            result['response_time'] = round(response_time, 3)
            result['error'] = str(e.reason)
            
            print(f"✗ Connection Failed: {e.reason}")
            print(f"✗ Response Time: {response_time:.3f} seconds")
            
        except Exception as e:
            response_time = time.time() - start_time
            result['status'] = 'error'
            result['response_time'] = round(response_time, 3)
            result['error'] = str(e)
            
            print(f"✗ Error: {e}")
            print(f"✗ Response Time: {response_time:.3f} seconds")
        
        self.save_to_log(result)
        return result
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        try:
            hostname = url.split('//')[1].split('/')[0]
            context = ssl.create_default_context()
            with context.wrap_socket(ssl.socket(), server_hostname=hostname) as s:
                s.connect((hostname, 443))
                cert = s.getpeercert()
                return True
        except:
            return False
    
    def interpret_status_code(self, code):
        """Interpret HTTP status codes"""
        status_codes = {
            200: "OK - Request successful",
            201: "Created - Resource created successfully",
            204: "No Content - Successful but no content",
            301: "Moved Permanently - Redirect",
            302: "Found - Temporary redirect",
            304: "Not Modified - Cached version is valid",
            400: "Bad Request - Invalid request",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Access denied",
            404: "Not Found - Resource not found",
            500: "Internal Server Error - Server error",
            502: "Bad Gateway - Invalid response from upstream",
            503: "Service Unavailable - Server overloaded or down",
            504: "Gateway Timeout - Upstream server timeout"
        }
        return status_codes.get(code, "Unknown status code")
    
    def check_multiple_sites(self, urls, search_content=None):
        """Check multiple sites"""
        results = []
        print(f"\n{'#'*60}")
        print(f"Checking {len(urls)} sites...")
        print(f"{'#'*60}")
        
        for url in urls:
            result = self.check_single_site(url, search_content)
            results.append(result)
            time.sleep(1)  # Delay between requests
        
        self.display_summary(results)
        return results
    
    def display_summary(self, results):
        """Display summary of multiple checks"""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        
        total = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = total - successful
        avg_response_time = sum(r['response_time'] for r in results if r['response_time']) / total if total > 0 else 0
        
        print(f"Total Sites Checked: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"Average Response Time: {avg_response_time:.3f} seconds")
        
        print(f"\nDetailed Results:")
        print(f"{'-'*60}")
        for r in results:
            status_symbol = "✓" if r['status'] == 'success' else "✗"
            code = r['response_code'] if r['response_code'] else "N/A"
            time_str = f"{r['response_time']:.3f}s" if r['response_time'] else "N/A"
            print(f"{status_symbol} {r['url']:<40} [{code}] {time_str}")
    
    def monitor_site(self, url, interval=60, duration=3600, alert_email=None):
        """Monitor a site periodically"""
        print(f"\n{'='*60}")
        print(f"Starting monitoring: {url}")
        print(f"Interval: {interval} seconds | Duration: {duration} seconds")
        print(f"{'='*60}")
        
        start_time = time.time()
        check_count = 0
        failures = 0
        
        while (time.time() - start_time) < duration:
            check_count += 1
            print(f"\n[Check #{check_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            result = self.check_single_site(url)
            
            if result['status'] != 'success':
                failures += 1
                if alert_email:
                    self.send_alert(url, result, alert_email)
            
            uptime_percentage = ((check_count - failures) / check_count) * 100
            print(f"\nUptime: {uptime_percentage:.2f}% ({check_count - failures}/{check_count} checks)")
            
            if (time.time() - start_time) < duration:
                print(f"\nNext check in {interval} seconds...")
                time.sleep(interval)
        
        print(f"\n{'='*60}")
        print("Monitoring Complete")
        print(f"{'='*60}")
        print(f"Total Checks: {check_count}")
        print(f"Successful: {check_count - failures}")
        print(f"Failed: {failures}")
        print(f"Overall Uptime: {((check_count - failures) / check_count) * 100:.2f}%")
    
    def send_alert(self, url, result, recipient_email):
        """Send email alert on failure (requires SMTP configuration)"""
        print(f"\n⚠ ALERT: Site {url} is down!")
        print(f"Note: Email alerts require SMTP configuration in the code")
        # SMTP configuration would go here
        # This is a placeholder - users need to configure their email settings
    
    def generate_report(self):
        """Generate a report from historical data"""
        if not self.history:
            print("No historical data available")
            return
        
        print(f"\n{'='*60}")
        print("HISTORICAL REPORT")
        print(f"{'='*60}")
        
        # Group by URL
        url_stats = {}
        for entry in self.history:
            url = entry['url']
            if url not in url_stats:
                url_stats[url] = {'total': 0, 'success': 0, 'response_times': []}
            
            url_stats[url]['total'] += 1
            if entry['status'] == 'success':
                url_stats[url]['success'] += 1
            if entry['response_time']:
                url_stats[url]['response_times'].append(entry['response_time'])
        
        # Display stats
        for url, stats in url_stats.items():
            uptime = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
            avg_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            
            print(f"\nURL: {url}")
            print(f"  Total Checks: {stats['total']}")
            print(f"  Successful: {stats['success']}")
            print(f"  Uptime: {uptime:.2f}%")
            print(f"  Avg Response Time: {avg_time:.3f}s")


def main():
    checker = SiteConnectivityChecker()
    
    print("="*60)
    print("ADVANCED SITE CONNECTIVITY CHECKER")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("1. Check single site")
        print("2. Check multiple sites")
        print("3. Check with content search")
        print("4. Monitor site (periodic checks)")
        print("5. View historical report")
        print("6. Load URLs from file")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            url = input("Enter URL (include http:// or https://): ").strip()
            if url:
                checker.check_single_site(url)
        
        elif choice == '2':
            print("Enter URLs (one per line, empty line to finish):")
            urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
            if urls:
                checker.check_multiple_sites(urls)
        
        elif choice == '3':
            url = input("Enter URL: ").strip()
            content = input("Enter text to search for: ").strip()
            if url and content:
                checker.check_single_site(url, search_content=content)
        
        elif choice == '4':
            url = input("Enter URL to monitor: ").strip()
            interval = int(input("Check interval (seconds, default 60): ").strip() or "60")
            duration = int(input("Monitor duration (seconds, default 300): ").strip() or "300")
            if url:
                checker.monitor_site(url, interval, duration)
        
        elif choice == '5':
            checker.generate_report()
        
        elif choice == '6':
            filename = input("Enter filename: ").strip()
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                checker.check_multiple_sites(urls)
            else:
                print(f"File '{filename}' not found")
        
        elif choice == '7':
            print("\nThank you for using Site Connectivity Checker!")
            break
        
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()