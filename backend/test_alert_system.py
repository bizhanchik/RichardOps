#!/usr/bin/env python3
"""
Comprehensive Test Alert System

This script provides functionality to test the email alert system with various scenarios:
1. Test basic email functionality
2. Test analytics anomaly alerts
3. Test security alerts
4. Test high severity alerts
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.email import send_alert_email, format_alert_email_content
from services.anomaly_detection import Anomaly, AnomalyDetectionService

# Load .env if present
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class AlertTester:
    """Test class for email alert functionality"""
    
    def __init__(self):
        self.brevo_api_key = os.getenv("BREVO_API_KEY")
        self.alert_email = os.getenv("ALERT_EMAIL") or os.getenv("TEST_EMAIL")
        self.sender_name = os.getenv("ALERT_SENDER_NAME", "Monitoring Bot")
        self.sender_email = os.getenv("ALERT_SENDER_EMAIL", "noreply@yourdomain.com")
        
        # Validate configuration
        if not self.brevo_api_key:
            print("❌ ERROR: BREVO_API_KEY is not set. Add it to .env file.")
            sys.exit(1)
        if not self.alert_email:
            print("❌ ERROR: ALERT_EMAIL or TEST_EMAIL is not set. Add it to .env file.")
            sys.exit(1)
    
    def test_basic_email(self) -> bool:
        """Test basic email functionality"""
        print("📧 Testing basic email functionality...")
        
        try:
            subject = "🧪 Test Alert - Basic Email Functionality"
            content = self._create_test_email_content()
            
            send_alert_email(subject, content, self.alert_email)
            print(f"✅ Basic email test sent successfully to {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"❌ Basic email test failed: {str(e)}")
            return False
    
    def test_analytics_anomaly_alert(self) -> bool:
        """Test analytics anomaly alert"""
        print("📊 Testing analytics anomaly alert...")
        
        try:
            # Create a mock anomaly
            anomaly = Anomaly(
                type="cpu_spike",
                severity="HIGH",
                timestamp=datetime.now(timezone.utc),
                description="CPU usage spiked to 95% (baseline: 45%)",
                details={
                    "current_usage": 95.2,
                    "baseline": 45.0,
                    "spike_percentage": 111.1,
                    "container": "web_server_1"
                },
                affected_resource="container_web_1",
                confidence=0.92
            )
            
            subject = f"🚨 ANOMALY DETECTED - {anomaly.severity} Severity"
            content = self._create_anomaly_email_content(anomaly)
            
            send_alert_email(subject, content, self.alert_email)
            print(f"✅ Analytics anomaly alert sent successfully to {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"❌ Analytics anomaly alert test failed: {str(e)}")
            return False
    
    def test_security_alert(self) -> bool:
        """Test security alert"""
        print("🔒 Testing security alert...")
        
        try:
            subject = "🚨 SECURITY ALERT - Brute Force Attack Detected"
            content = self._create_security_alert_content()
            
            send_alert_email(subject, content, self.alert_email)
            print(f"✅ Security alert sent successfully to {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"❌ Security alert test failed: {str(e)}")
            return False
    
    def test_high_severity_alert(self) -> bool:
        """Test high severity alert"""
        print("⚠️ Testing high severity alert...")
        
        try:
            alerts = [
                "[container_db] Database connection pool exhausted",
                "[container_web] Memory usage critical: 98%",
                "[container_cache] Redis connection timeout"
            ]
            
            subject = "🚨 HIGH SEVERITY Alert - Multiple Critical Issues"
            content = format_alert_email_content(
                host="test-server-01",
                server_id="srv-001",
                env="production",
                alerts=alerts,
                score=0.95
            )
            
            send_alert_email(subject, content, self.alert_email)
            print(f"✅ High severity alert sent successfully to {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"❌ High severity alert test failed: {str(e)}")
            return False
    
    def test_multiple_anomalies_alert(self) -> bool:
        """Test alert with multiple anomalies"""
        print("📈 Testing multiple anomalies alert...")
        
        try:
            anomalies = [
                Anomaly(
                    type="memory_spike",
                    severity="MEDIUM",
                    timestamp=datetime.now(timezone.utc),
                    description="Memory usage increased by 35%",
                    details={"current": 85.2, "baseline": 63.0},
                    affected_resource="container_app_1"
                ),
                Anomaly(
                    type="ip_request_spike",
                    severity="HIGH",
                    timestamp=datetime.now(timezone.utc),
                    description="Suspicious request volume from IP 192.168.1.100",
                    details={"requests_per_hour": 250, "threshold": 100},
                    affected_resource="web_server"
                ),
                Anomaly(
                    type="high_error_rate",
                    severity="MEDIUM",
                    timestamp=datetime.now(timezone.utc),
                    description="Error rate increased to 15%",
                    details={"error_rate": 15.3, "threshold": 10.0},
                    affected_resource="container_api_1"
                )
            ]
            
            subject = "🚨 MULTIPLE ANOMALIES DETECTED - System Health Alert"
            content = self._create_multiple_anomalies_content(anomalies)
            
            send_alert_email(subject, content, self.alert_email)
            print(f"✅ Multiple anomalies alert sent successfully to {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"❌ Multiple anomalies alert test failed: {str(e)}")
            return False
    
    def _create_test_email_content(self) -> str:
        """Create HTML content for basic test email"""
        now = datetime.now(timezone.utc).isoformat()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Test Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 20px; margin-bottom: 20px;">
                <h1 style="color: #2196f3; margin: 0 0 10px 0;">🧪 Test Alert - Email System Verification</h1>
                <p style="margin: 0; font-size: 16px;">This is a test email to verify the alert system functionality.</p>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #333; margin-top: 0;">Test Information</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; width: 30%;">Test Type:</td>
                        <td style="padding: 8px 0;">Basic Email Functionality</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Timestamp:</td>
                        <td style="padding: 8px 0;">{now}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Sender:</td>
                        <td style="padding: 8px 0;">{self.sender_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Recipient:</td>
                        <td style="padding: 8px 0;">{self.alert_email}</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px;">
                <h3 style="color: #28a745; margin-top: 0;">✅ Email System Status</h3>
                <p>If you received this email, the alert system is working correctly!</p>
                <ul>
                    <li>✅ Brevo API integration functional</li>
                    <li>✅ Email formatting working</li>
                    <li>✅ Environment variables configured</li>
                    <li>✅ SMTP delivery successful</li>
                </ul>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
                <p>This is a test email from the Monitoring System Alert functionality.</p>
                <p>Generated at: {now}</p>
            </div>
        </body>
        </html>
        """
    
    def _create_anomaly_email_content(self, anomaly: Anomaly) -> str:
        """Create HTML content for anomaly alert"""
        severity_colors = {
            "HIGH": "#d32f2f",
            "MEDIUM": "#f57c00", 
            "LOW": "#388e3c"
        }
        color = severity_colors.get(anomaly.severity, "#666")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Anomaly Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #ffebee; border-left: 4px solid {color}; padding: 20px; margin-bottom: 20px;">
                <h1 style="color: {color}; margin: 0 0 10px 0;">🚨 ANOMALY DETECTED - {anomaly.severity} Severity</h1>
                <p style="margin: 0; font-size: 16px;">{anomaly.description}</p>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #333; margin-top: 0;">Anomaly Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; width: 30%;">Type:</td>
                        <td style="padding: 8px 0;">{anomaly.type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Severity:</td>
                        <td style="padding: 8px 0; color: {color}; font-weight: bold;">{anomaly.severity}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Timestamp:</td>
                        <td style="padding: 8px 0;">{anomaly.timestamp.isoformat()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Affected Resource:</td>
                        <td style="padding: 8px 0;">{anomaly.affected_resource or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Confidence:</td>
                        <td style="padding: 8px 0;">{anomaly.confidence:.1%}</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px;">
                <h2 style="color: #333; margin-top: 0;">Technical Details</h2>
                <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px;">
{json.dumps(anomaly.details, indent=2)}
                </pre>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
                <p>This is an automated anomaly alert from the Analytics System.</p>
                <p>Please investigate immediately if this is a HIGH severity anomaly.</p>
            </div>
        </body>
        </html>
        """
    
    def _create_security_alert_content(self) -> str:
        """Create HTML content for security alert"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 20px; margin-bottom: 20px;">
                <h1 style="color: #d32f2f; margin: 0 0 10px 0;">🔒 SECURITY ALERT - Brute Force Attack Detected</h1>
                <p style="margin: 0; font-size: 16px;">Multiple failed login attempts detected from suspicious IP addresses.</p>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #333; margin-top: 0;">Attack Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; width: 30%;">Attack Type:</td>
                        <td style="padding: 8px 0;">Brute Force Login Attempt</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Source IP:</td>
                        <td style="padding: 8px 0;">192.168.1.100</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Failed Attempts:</td>
                        <td style="padding: 8px 0; color: #d32f2f; font-weight: bold;">25</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Time Window:</td>
                        <td style="padding: 8px 0;">Last 10 minutes</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Confidence:</td>
                        <td style="padding: 8px 0;">95%</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 20px;">
                <h2 style="color: #856404; margin-top: 0;">🛡️ Recommended Actions</h2>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Block IP address 192.168.1.100 immediately</li>
                    <li>Review authentication logs for the affected service</li>
                    <li>Check for any successful logins from this IP</li>
                    <li>Consider implementing rate limiting</li>
                    <li>Monitor for similar patterns from other IPs</li>
                </ul>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
                <p>This is an automated security alert from the Monitoring System.</p>
                <p>Immediate action required to protect system security.</p>
            </div>
        </body>
        </html>
        """
    
    def _create_multiple_anomalies_content(self, anomalies: List[Anomaly]) -> str:
        """Create HTML content for multiple anomalies alert"""
        anomaly_items = ""
        for anomaly in anomalies:
            severity_color = {"HIGH": "#d32f2f", "MEDIUM": "#f57c00", "LOW": "#388e3c"}.get(anomaly.severity, "#666")
            anomaly_items += f"""
            <li style="margin: 10px 0; padding: 10px; border-left: 3px solid {severity_color}; background-color: #f8f9fa;">
                <strong style="color: {severity_color};">[{anomaly.severity}] {anomaly.type}</strong><br>
                <span style="color: #666;">{anomaly.description}</span><br>
                <small style="color: #999;">Resource: {anomaly.affected_resource or 'N/A'} | Confidence: {anomaly.confidence:.1%}</small>
            </li>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Multiple Anomalies Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 20px; margin-bottom: 20px;">
                <h1 style="color: #d32f2f; margin: 0 0 10px 0;">🚨 MULTIPLE ANOMALIES DETECTED</h1>
                <p style="margin: 0; font-size: 16px;">{len(anomalies)} anomalies detected across different system components.</p>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #333; margin-top: 0;">Summary</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; width: 30%;">Total Anomalies:</td>
                        <td style="padding: 8px 0;">{len(anomalies)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">High Severity:</td>
                        <td style="padding: 8px 0; color: #d32f2f; font-weight: bold;">{len([a for a in anomalies if a.severity == 'HIGH'])}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Medium Severity:</td>
                        <td style="padding: 8px 0; color: #f57c00; font-weight: bold;">{len([a for a in anomalies if a.severity == 'MEDIUM'])}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Detection Time:</td>
                        <td style="padding: 8px 0;">{datetime.now(timezone.utc).isoformat()}</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px;">
                <h2 style="color: #333; margin-top: 0;">Detected Anomalies</h2>
                <ul style="margin: 0; padding: 0; list-style: none;">
                    {anomaly_items}
                </ul>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
                <p>This is an automated alert from the Analytics Anomaly Detection System.</p>
                <p>Multiple anomalies require immediate investigation.</p>
            </div>
        </body>
        </html>
        """
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all alert tests"""
        print("🚀 Starting comprehensive alert system tests...\n")
        
        results = {}
        
        # Test basic email
        results['basic_email'] = self.test_basic_email()
        print()
        
        # Test analytics anomaly
        results['analytics_anomaly'] = self.test_analytics_anomaly_alert()
        print()
        
        # Test security alert
        results['security_alert'] = self.test_security_alert()
        print()
        
        # Test high severity alert
        results['high_severity'] = self.test_high_severity_alert()
        print()
        
        # Test multiple anomalies
        results['multiple_anomalies'] = self.test_multiple_anomalies_alert()
        print()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test results summary"""
        print("=" * 60)
        print("📊 ALERT SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        print("-" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Email alert system is working correctly.")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} test(s) failed. Check configuration and logs.")
        
        print(f"\n📧 Test emails sent to: {self.alert_email}")
        print("Check your inbox for the test alerts.")


def main():
    """Main function to run alert tests"""
    print("🧪 Alert System Test Suite")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("services/email.py").exists():
        print("❌ Error: Please run this script from the backend directory")
        print("   cd RichardOps/backend")
        print("   python test_alert_system.py")
        sys.exit(1)
    
    # Initialize tester
    try:
        tester = AlertTester()
    except SystemExit:
        return
    
    # Run tests
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "basic":
            tester.test_basic_email()
        elif test_type == "anomaly":
            tester.test_analytics_anomaly_alert()
        elif test_type == "security":
            tester.test_security_alert()
        elif test_type == "high":
            tester.test_high_severity_alert()
        elif test_type == "multiple":
            tester.test_multiple_anomalies_alert()
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("Available tests: basic, anomaly, security, high, multiple")
            sys.exit(1)
    else:
        # Run all tests
        results = tester.run_all_tests()
        tester.print_summary(results)


if __name__ == "__main__":
    main()