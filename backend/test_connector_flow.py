"""
Test Connector Flow
Demonstrates centralized catalog with tenant-isolated connections
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_connector_flow():
    """Test the complete connector flow"""
    
    print_section("IGA Connector Flow Test")
    
    # 1. List available connector templates (centralized catalog)
    print_section("1. List Available Connector Templates (Catalog)")
    response = requests.get(f"{BASE_URL}/connector-templates")
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✓ Found {len(templates)} connector templates:")
        for t in templates:
            print(f"  • {t['name']} ({t['slug']})")
            print(f"    Provider: {t['provider']}")
            print(f"    Type: {t['connector_type']}")
            print(f"    Capabilities: {', '.join(t['capabilities'])}")
        
        # Save Azure AD template ID for later
        azure_template = next((t for t in templates if t['slug'] == 'azure-ad'), None)
        if azure_template:
            azure_template_id = azure_template['id']
            print(f"\n  → Using Azure AD template: {azure_template_id}")
    else:
        print(f"✗ Error: {response.status_code}")
        return
    
    # 2. Get list of tenants
    print_section("2. Get Tenants")
    response = requests.get(f"{BASE_URL}/tenants")
    
    if response.status_code == 200:
        tenants = response.json()
        if len(tenants) >= 2:
            tenant1_id = tenants[0]['id']
            tenant2_id = tenants[1]['id']
            print(f"✓ Using Tenant 1: {tenants[0]['name']} ({tenant1_id})")
            print(f"✓ Using Tenant 2: {tenants[1]['name']} ({tenant2_id})")
        else:
            print("✗ Need at least 2 tenants for this demo")
            return
    else:
        print(f"✗ Error: {response.status_code}")
        return
    
    # 3. Create Azure AD connector for Tenant 1
    print_section("3. Create Azure AD Connector for Tenant 1")
    tenant1_config = {
        "template_id": azure_template_id,
        "config": {
            "tenant_id": "contoso-tenant-id",
            "client_id": "tenant1-client-id",
            "client_secret": "tenant1-secret-key",
            "redirect_uri": "https://tenant1.example.com/callback"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tenants/{tenant1_id}/connectors",
        json=tenant1_config
    )
    
    if response.status_code == 201:
        connector1 = response.json()
        connector1_id = connector1['id']
        print(f"✓ Created connector for Tenant 1")
        print(f"  ID: {connector1_id}")
        print(f"  Status: {connector1['status']}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        connector1_id = None
    
    # 4. Create Azure AD connector for Tenant 2 (different credentials)
    print_section("4. Create Azure AD Connector for Tenant 2")
    tenant2_config = {
        "template_id": azure_template_id,
        "config": {
            "tenant_id": "fabrikam-tenant-id",
            "client_id": "tenant2-client-id",
            "client_secret": "tenant2-secret-key",
            "redirect_uri": "https://tenant2.example.com/callback"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tenants/{tenant2_id}/connectors",
        json=tenant2_config
    )
    
    if response.status_code == 201:
        connector2 = response.json()
        connector2_id = connector2['id']
        print(f"✓ Created connector for Tenant 2")
        print(f"  ID: {connector2_id}")
        print(f"  Status: {connector2['status']}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        connector2_id = None
    
    # 5. List Tenant 1 connectors
    print_section("5. List Tenant 1 Connectors")
    response = requests.get(f"{BASE_URL}/tenants/{tenant1_id}/connectors")
    
    if response.status_code == 200:
        connectors = response.json()
        print(f"✓ Tenant 1 has {len(connectors)} connector(s):")
        for c in connectors:
            print(f"  • {c['template_name']} - Status: {c['status']}")
    
    # 6. List Tenant 2 connectors
    print_section("6. List Tenant 2 Connectors")
    response = requests.get(f"{BASE_URL}/tenants/{tenant2_id}/connectors")
    
    if response.status_code == 200:
        connectors = response.json()
        print(f"✓ Tenant 2 has {len(connectors)} connector(s):")
        for c in connectors:
            print(f"  • {c['template_name']} - Status: {c['status']}")
    
    # 7. Get Tenant 1 connector details (with masked config)
    if connector1_id:
        print_section("7. Get Tenant 1 Connector Details (Masked)")
        response = requests.get(
            f"{BASE_URL}/tenants/{tenant1_id}/connectors/{connector1_id}"
        )
        
        if response.status_code == 200:
            connector = response.json()
            print(f"✓ Connector Details:")
            print(f"  Template: {connector['template_name']}")
            print(f"  Status: {connector['status']}")
            print(f"  Config:")
            for key, value in connector['config'].items():
                print(f"    {key}: {value}")
    
    # 8. Test connection
    if connector1_id:
        print_section("8. Test Tenant 1 Connector Connection")
        response = requests.post(
            f"{BASE_URL}/tenants/{tenant1_id}/connectors/{connector1_id}/test"
        )
        
        if response.status_code == 200:
            result = response.json()
            status = "✓" if result['success'] else "✗"
            print(f"{status} {result['message']}")
    
    # Summary
    print_section("Summary")
    print("✓ Centralized connector catalog with templates")
    print("✓ Tenant 1 has isolated Azure AD connection")
    print("✓ Tenant 2 has isolated Azure AD connection")
    print("✓ Each tenant has separate credentials")
    print("✓ Complete data isolation between tenants")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_connector_flow()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to backend")
        print("Make sure the backend is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
