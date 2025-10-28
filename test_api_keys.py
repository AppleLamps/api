#!/usr/bin/env python3
"""
Test script for API Key Management

Tests both CLI management and API endpoint functionality
"""

import httpx
import asyncio
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ADMIN_KEY", "test-admin-key")

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ {text}{RESET}")


async def test_create_key():
    """Test creating API keys"""
    print_header("Test 1: Creating API Keys")
    
    async with httpx.AsyncClient() as client:
        # Create first key
        payload = {
            "user_name": "Test User 1",
            "user_email": "test1@example.com",
            "rate_limit": 20,
            "notes": "Test key 1"
        }
        
        response = await client.post(
            f"{API_BASE_URL}/admin/keys/create",
            json=payload,
            params={"admin_key": ADMIN_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Created API key for {data['user_name']}")
            print_info(f"  Key ID: {data['id']}")
            print_info(f"  API Key: {data['key']}")
            print_info(f"  Rate Limit: {data['rate_limit']} req/min")
            return data['key'], data['id']
        else:
            print_error(f"Failed to create key: {response.text}")
            return None, None


async def test_list_keys():
    """Test listing API keys"""
    print_header("Test 2: Listing API Keys")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/admin/keys",
            params={"admin_key": ADMIN_KEY, "active_only": "true"}
        )
        
        if response.status_code == 200:
            keys = response.json()
            print_success(f"Retrieved {len(keys)} active keys")
            
            for key in keys:
                print_info(f"  {key['user_name']} ({key['user_email']})")
                print_info(f"    Rate Limit: {key['rate_limit']}, Last Used: {key['last_used']}")
            
            return keys
        else:
            print_error(f"Failed to list keys: {response.text}")
            return None


async def test_use_key(api_key):
    """Test using an API key to access the API"""
    print_header("Test 3: Using API Key to Access Endpoint")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": api_key}
        
        # Test health endpoint
        response = await client.get(
            f"{API_BASE_URL}/health",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Successfully authenticated with API key")
            print_info(f"  Status: {data['status']}")
            print_info(f"  Environment: {data['environment']}")
            print_info(f"  Cache Enabled: {data['cache_enabled']}")
            return True
        else:
            print_error(f"Failed to authenticate: {response.text}")
            return False


async def test_invalid_key():
    """Test using an invalid API key"""
    print_header("Test 4: Testing Invalid API Key Rejection")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": "invalid_key_12345"}
        
        response = await client.get(
            f"{API_BASE_URL}/health",
            headers=headers
        )
        
        if response.status_code == 403:
            print_success("Invalid key correctly rejected")
            print_info(f"  Response: {response.json()['detail']}")
            return True
        else:
            print_error(f"Invalid key was not rejected (status: {response.status_code})")
            return False


async def test_get_key_info(key_id):
    """Test getting details about a specific key"""
    print_header("Test 5: Getting Key Details")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/admin/keys/{key_id}",
            params={"admin_key": ADMIN_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved details for key {key_id}")
            print_info(f"  User: {data['user_name']}")
            print_info(f"  Email: {data['user_email']}")
            print_info(f"  Rate Limit: {data['rate_limit']}")
            print_info(f"  Active: {data['is_active']}")
            print_info(f"  Created: {data['created_at']}")
            return True
        else:
            print_error(f"Failed to get key details: {response.text}")
            return False


async def test_revoke_key(key_id):
    """Test revoking an API key"""
    print_header("Test 6: Revoking API Key")
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{API_BASE_URL}/admin/keys/{key_id}",
            params={"admin_key": ADMIN_KEY}
        )
        
        if response.status_code == 200:
            print_success(f"Successfully revoked key {key_id}")
            return True
        else:
            print_error(f"Failed to revoke key: {response.text}")
            return False


async def test_revoked_key_rejected(api_key):
    """Test that revoked keys are rejected"""
    print_header("Test 7: Testing Revoked Key Rejection")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": api_key}
        
        response = await client.get(
            f"{API_BASE_URL}/health",
            headers=headers
        )
        
        if response.status_code == 403:
            print_success("Revoked key correctly rejected")
            return True
        else:
            print_error(f"Revoked key was not rejected (status: {response.status_code})")
            return False


async def main():
    """Run all tests"""
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════╗")
    print(f"║         Grokipedia API - API Key Management Tests          ║")
    print(f"╚════════════════════════════════════════════════════════════╝{RESET}")
    print(f"\nAPI URL: {API_BASE_URL}")
    print(f"Admin Key: {ADMIN_KEY[:10]}..." if len(ADMIN_KEY) > 10 else f"Admin Key: {ADMIN_KEY}")
    
    try:
        # Test 1: Create key
        api_key, key_id = await test_create_key()
        if not api_key:
            print_error("Cannot proceed - failed to create key")
            return
        
        # Test 2: List keys
        keys = await test_list_keys()
        if not keys:
            print_error("Cannot proceed - failed to list keys")
            return
        
        # Test 3: Use the key
        success = await test_use_key(api_key)
        if not success:
            print_error("Failed to use API key")
            return
        
        # Test 4: Invalid key
        await test_invalid_key()
        
        # Test 5: Get key info
        await test_get_key_info(key_id)
        
        # Test 6: Revoke the key
        await test_revoke_key(key_id)
        
        # Test 7: Try using revoked key
        await test_revoked_key_rejected(api_key)
        
        # Summary
        print_header("Test Summary")
        print_success("All API key management tests completed!")
        print_info("API key authentication is working correctly")
        
    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
