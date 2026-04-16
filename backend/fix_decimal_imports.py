#!/usr/bin/env python3
"""Fix Decimal imports in all model files"""

import os
import re

def fix_decimal_imports(file_path):
    """Fix Decimal imports in a model file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace Decimal( with DECIMAL(
    content = re.sub(r'Decimal\(', 'DECIMAL(', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

# Fix all model files
model_files = [
    'backend/app/models/financial.py',
    'backend/app/models/inventory.py', 
    'backend/app/models/sales.py',
    'backend/app/models/pricing_models.py'
]

for file_path in model_files:
    if os.path.exists(file_path):
        fix_decimal_imports(file_path)

print("All Decimal imports fixed!")
