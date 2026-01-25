import sys
import unittest
from unittest.mock import MagicMock

# Mock the database response
def test_deduplication():
    print("Testing deduplication logic...")
    
    # Simulating data returned from Logo SQL query
    # Multiple LOGICALREFs for the same CODE
    mock_data = [
        {'LOGICALREF': 1, 'CODE': 'ABBAS.OTHMN', 'DEFINITION_': 'ABBAS OTHMN'},
        {'LOGICALREF': 2, 'CODE': 'ABBAS.OTHMN', 'DEFINITION_': 'ABBAS OTHMN'},
        {'LOGICALREF': 3, 'CODE': 'ABBAS.OTHMN', 'DEFINITION_': 'ABBAS OTHMN'},
        {'LOGICALREF': 4, 'CODE': 'ABDULLAH.DIAA', 'DEFINITION_': 'Abdullah Diaa Abdullah'},
        {'LOGICALREF': 5, 'CODE': 'ABDULLAH.DIAA', 'DEFINITION_': 'Abdullah Diaa Abdullah'},
        {'LOGICALREF': 6, 'CODE': 'ABUZENAB', 'DEFINITION_': 'Abu Zenab'}
    ]
    
    salesmen = []
    seen_sls = set()
    
    for r in mock_data:
        lref = str(r.get('LOGICALREF') or "")
        sid = str(r['CODE'] or "").strip()
        name = str(r['DEFINITION_'] or "").strip()
        
        # This is the logic we applied in installer_service.py:
        unique_key = sid 
        
        if sid and sid != '0' and unique_key not in seen_sls:
            salesmen.append({"id": sid, "name": name, "logo_ref": lref})
            seen_sls.add(unique_key)
            
    print(f"Results: {len(salesmen)} unique salesmen found.")
    for s in salesmen:
        print(f" - {s['id']}: {s['name']}")
        
    expected_count = 3
    if len(salesmen) == expected_count:
        print("\nSUCCESS: Deduplication is working correctly!")
        return True
    else:
        print(f"\nFAILURE: Expected {expected_count} results, but got {len(salesmen)}.")
        return False

if __name__ == "__main__":
    if test_deduplication():
        sys.exit(0)
    else:
        sys.exit(1)
