"""
Security testing framework for AI Guardian.
"""
import os
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityTestFramework:
    """Framework for running security tests and scans."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"
        
    def run_bandit_security_scan(self) -> Dict[str, Any]:
        """Run Bandit security scan on Python code."""
        try:
            cmd = ["bandit", "-r", str(self.backend_path), "-f", "json", "-ll"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {"status": "success", "issues": [], "message": "No security issues found"}
            else:
                try:
                    issues = json.loads(result.stdout)
                    return {"status": "warning", "issues": issues, "message": "Security issues detected"}
                except json.JSONDecodeError:
                    return {"status": "error", "message": f"Bandit scan failed: {result.stderr}"}
                    
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Bandit scan timed out"}
        except FileNotFoundError:
            return {"status": "error", "message": "Bandit not installed. Install with: pip install bandit"}
        except Exception as e:
            return {"status": "error", "message": f"Bandit scan error: {str(e)}"}
    
    def check_dependency_vulnerabilities(self) -> Dict[str, Any]:
        """Check for known vulnerabilities in dependencies."""
        results = {}
        
        # Check Python dependencies
        try:
            cmd = ["safety", "check", "--json"]
            result = subprocess.run(cmd, cwd=self.backend_path, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                results["python"] = {"status": "success", "vulnerabilities": []}
            else:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    results["python"] = {"status": "warning", "vulnerabilities": vulnerabilities}
                except json.JSONDecodeError:
                    results["python"] = {"status": "error", "message": result.stderr}
                    
        except subprocess.TimeoutExpired:
            results["python"] = {"status": "error", "message": "Safety check timed out"}
        except FileNotFoundError:
            results["python"] = {"status": "error", "message": "Safety not installed. Install with: pip install safety"}
        except Exception as e:
            results["python"] = {"status": "error", "message": f"Safety check error: {str(e)}"}
        
        # Check Node.js dependencies
        try:
            cmd = ["npm", "audit", "--json"]
            result = subprocess.run(cmd, cwd=self.frontend_path, capture_output=True, text=True, timeout=300)
            
            audit_data = json.loads(result.stdout)
            if audit_data.get("metadata", {}).get("vulnerabilities", {}).get("total", 0) == 0:
                results["nodejs"] = {"status": "success", "vulnerabilities": []}
            else:
                results["nodejs"] = {"status": "warning", "vulnerabilities": audit_data}
                
        except subprocess.TimeoutExpired:
            results["nodejs"] = {"status": "error", "message": "npm audit timed out"}
        except FileNotFoundError:
            results["nodejs"] = {"status": "error", "message": "npm not installed"}
        except json.JSONDecodeError:
            results["nodejs"] = {"status": "error", "message": "Failed to parse npm audit output"}
        except Exception as e:
            results["nodejs"] = {"status": "error", "message": f"npm audit error: {str(e)}"}
            
        return results
    
    def check_secrets_in_code(self) -> Dict[str, Any]:
        """Check for hardcoded secrets in code."""
        secrets_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API Key pattern
        ]
        
        issues = []
        
        try:
            for pattern in secrets_patterns:
                cmd = ["grep", "-r", "-n", "-E", pattern, str(self.project_root), 
                       "--exclude-dir=.git", "--exclude-dir=node_modules", 
                       "--exclude-dir=__pycache__", "--exclude=*.pyc"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            issues.append({"pattern": pattern, "match": line})
                            
        except Exception as e:
            return {"status": "error", "message": f"Secret scan error: {str(e)}"}
        
        return {"status": "warning" if issues else "success", "issues": issues}
    
    def validate_environment_security(self) -> Dict[str, Any]:
        """Validate environment configuration for security issues."""
        issues = []
        
        # Check .env.example files
        env_files = [
            self.backend_path / ".env.example",
            self.frontend_path / ".env.example"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        content = f.read()
                        
                    # Check for default/weak values
                    weak_patterns = [
                        ("SECRET_KEY=your-secret-key-here", "Default secret key detected"),
                        ("JWT_SECRET_KEY=your-jwt-secret", "Default JWT secret detected"),
                        ("password=password", "Default password detected"),
                        ("minioadmin", "Default MinIO credentials detected"),
                    ]
                    
                    for pattern, message in weak_patterns:
                        if pattern in content:
                            issues.append({
                                "file": str(env_file),
                                "issue": message,
                                "pattern": pattern
                            })
                            
                except Exception as e:
                    issues.append({
                        "file": str(env_file),
                        "issue": f"Failed to read env file: {str(e)}"
                    })
        
        return {"status": "warning" if issues else "success", "issues": issues}
    
    def run_all_security_checks(self) -> Dict[str, Any]:
        """Run all security checks and return comprehensive report."""
        logger.info("Starting comprehensive security scan...")
        
        report = {
            "timestamp": str(Path.cwd()),
            "bandit_scan": self.run_bandit_security_scan(),
            "dependency_vulnerabilities": self.check_dependency_vulnerabilities(),
            "secrets_check": self.check_secrets_in_code(),
            "environment_validation": self.validate_environment_security()
        }
        
        # Calculate overall status
        statuses = [check.get("status", "error") for check in report.values() if isinstance(check, dict)]
        if "error" in statuses:
            report["overall_status"] = "error"
        elif "warning" in statuses:
            report["overall_status"] = "warning"
        else:
            report["overall_status"] = "success"
        
        logger.info(f"Security scan completed with overall status: {report['overall_status']}")
        return report

# Global instance
security_tester = SecurityTestFramework()