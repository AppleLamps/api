#!/usr/bin/env python3
"""
API Key Management CLI

Usage:
    python manage_keys.py init                                      # Initialize database
    python manage_keys.py create <name> <email> [rate_limit]        # Create new API key
    python manage_keys.py list [--all]                              # List active API keys
    python manage_keys.py revoke <key_id>                           # Revoke an API key
    python manage_keys.py delete <key_id>                           # Delete an API key
    python manage_keys.py info <key_id>                             # Show key details
"""

import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from models import (
    init_db, create_api_key, get_all_api_keys, 
    revoke_api_key, SessionLocal, APIKey
)

load_dotenv()


def init_database():
    """Initialize database"""
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)


def create_key(user_name: str, user_email: str, rate_limit: int = 10, notes: str = None):
    """Create a new API key"""
    try:
        key = create_api_key(user_name, user_email, rate_limit, notes)
        print(f"✓ API key created successfully")
        print(f"\n  User: {user_name}")
        print(f"  Email: {user_email}")
        print(f"  Rate Limit: {rate_limit} requests/minute")
        print(f"  Key: {key}")
        print(f"\n  ⚠️  Save this key - you won't be able to see it again!")
        print(f"  Use it as: curl -H 'X-API-Key: {key}' https://your-api.com/health")
        
    except Exception as e:
        print(f"✗ Error creating API key: {e}")
        sys.exit(1)


def list_keys(show_all: bool = False):
    """List API keys"""
    try:
        keys = get_all_api_keys(active_only=not show_all)
        
        if not keys:
            print("No API keys found")
            return
        
        print(f"\n{'ID':<36} {'User':<20} {'Email':<30} {'Rate Limit':<12} {'Active':<8} {'Last Used':<20}")
        print("-" * 130)
        
        for key in keys:
            last_used = key.last_used.strftime("%Y-%m-%d %H:%M:%S") if key.last_used else "Never"
            print(f"{key.id:<36} {key.user_name:<20} {key.user_email:<30} {key.rate_limit:<12} {str(key.is_active):<8} {last_used:<20}")
        
        print(f"\nTotal: {len(keys)} keys")
        
    except Exception as e:
        print(f"✗ Error listing API keys: {e}")
        sys.exit(1)


def revoke_key(key_id: str):
    """Revoke an API key"""
    try:
        success = revoke_api_key(key_id)
        if success:
            print(f"✓ API key revoked: {key_id}")
        else:
            print(f"✗ API key not found: {key_id}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error revoking API key: {e}")
        sys.exit(1)


def delete_key(key_id: str):
    """Delete an API key from database"""
    try:
        db = SessionLocal()
        try:
            key_record = db.query(APIKey).filter(APIKey.id == key_id).first()
            if not key_record:
                print(f"✗ API key not found: {key_id}")
                sys.exit(1)
            
            db.delete(key_record)
            db.commit()
            print(f"✓ API key deleted: {key_id}")
        finally:
            db.close()
    except Exception as e:
        print(f"✗ Error deleting API key: {e}")
        sys.exit(1)


def show_info(key_id: str):
    """Show detailed information about an API key"""
    try:
        db = SessionLocal()
        try:
            key_record = db.query(APIKey).filter(APIKey.id == key_id).first()
            if not key_record:
                print(f"✗ API key not found: {key_id}")
                sys.exit(1)
            
            print(f"\nAPI Key Details:")
            print(f"  ID: {key_record.id}")
            print(f"  User: {key_record.user_name}")
            print(f"  Email: {key_record.user_email}")
            print(f"  Rate Limit: {key_record.rate_limit} requests/minute")
            print(f"  Active: {key_record.is_active}")
            print(f"  Created: {key_record.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  Last Used: {key_record.last_used.strftime('%Y-%m-%d %H:%M:%S UTC') if key_record.last_used else 'Never'}")
            if key_record.notes:
                print(f"  Notes: {key_record.notes}")
        finally:
            db.close()
    except Exception as e:
        print(f"✗ Error fetching key info: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Grokipedia API Key Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    subparsers.add_parser("init", help="Initialize database")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new API key")
    create_parser.add_argument("name", help="User name")
    create_parser.add_argument("email", help="User email")
    create_parser.add_argument("--rate-limit", type=int, default=10, help="Rate limit (requests/min, default: 10)")
    create_parser.add_argument("--notes", help="Optional notes about this key")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List API keys")
    list_parser.add_argument("--all", action="store_true", help="Show all keys including inactive ones")
    
    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("key_id", help="API key ID")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an API key")
    delete_parser.add_argument("key_id", help="API key ID")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show key details")
    info_parser.add_argument("key_id", help="API key ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "init":
        init_database()
    elif args.command == "create":
        create_key(args.name, args.email, args.rate_limit, args.notes)
    elif args.command == "list":
        list_keys(show_all=args.all)
    elif args.command == "revoke":
        revoke_key(args.key_id)
    elif args.command == "delete":
        delete_key(args.key_id)
    elif args.command == "info":
        show_info(args.key_id)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
