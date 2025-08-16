#!/usr/bin/env python3
"""
Quick demo script - tạo data và chạy evaluation ngay
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and print results"""
    print(f"\n🔧 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print(f"✅ Success!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Error (return code: {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("🚀 PII Evaluation Quick Demo")
    print("=" * 60)
    
    # Step 1: Generate test data
    run_command("python generate_test_data.py", "Generating test data...")
    
    # Step 2: Run simple evaluation
    run_command("python simple_pii_evaluation.py", "Running PII evaluation...")
    
    print("\n🎉 Demo completed!")
    print("Check the generated files:")
    print("  - simple_test_data.csv")
    print("  - complex_test_data_with_pii.csv") 
    print("  - evaluation_results.json")

if __name__ == "__main__":
    main()
