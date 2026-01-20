import sys
import os

# Update path to include the backend directory so we can import app modules
sys.path.append(os.path.join(os.getcwd()))

from app.core.config import settings
from app.api.v1.endpoints.metabase import get_metabase_dashboard_url

def test_metabase_url_generation():
    print("Testing Metabase URL Generation...")
    
    # Mock settings for testing
    original_secret = settings.METABASE_SECRET_KEY
    original_url = settings.METABASE_SITE_URL
    
    settings.METABASE_SECRET_KEY = "test_secret_key"
    settings.METABASE_SITE_URL = "http://test.metabase.com"
    
    try:
        # Test Case 1: Simple Dashboard ID
        result = get_metabase_dashboard_url(dashboard_id=5)
        print(f"\n[Success] Generated URL: {result['iframe_url']}")
        assert "dashboard" in result['iframe_url']
        assert "http://test.metabase.com" in result['iframe_url']
        
        # Test Case 2: With Parameters (Company, Branch)
        result_params = get_metabase_dashboard_url(
            dashboard_id=10, 
            company_id="FIRM_01", 
            branch_id="MAIN", 
            period="2024"
        )
        print(f"\n[Success] Generated URL with Params: {result_params['iframe_url']}")
        
        print("\nAll tests passed!")
        
    except Exception as e:
        print(f"\n[Failed] Error: {e}")
    finally:
        # Restore settings
        settings.METABASE_SECRET_KEY = original_secret
        settings.METABASE_SITE_URL = original_url

if __name__ == "__main__":
    test_metabase_url_generation()
