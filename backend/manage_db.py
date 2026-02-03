#!/usr/bin/env python
"""
IGA Database Management CLI
Manage migrations, seeders, and database operations
"""

import sys
import argparse
import logging
from app.seeders import SEEDERS
from app.seeders.runner import run_all_seeders
from app.migration_helper import MigrationHelper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def cmd_seed_all(args):
    """Run all registered seeders"""
    print("\n🌱 Running all seeders...")
    run_all_seeders()
    print("✓ All seeders completed\n")


def cmd_list_seeders(args):
    """List all registered seeders"""
    print("\n📋 Registered Seeders:")
    print("=" * 60)
    for i, SeederClass in enumerate(SEEDERS, 1):
        seeder = SeederClass()
        print(f"{i}. {seeder.name} (order: {seeder.order})")
        if seeder.description:
            print(f"   {seeder.description}")
        if seeder.requires_env_flag:
            print(f"   [Requires ENV flag]")
    print("=" * 60)
    print(f"Total: {len(SEEDERS)} seeders\n")


def cmd_track_migration(args):
    """Track a manual migration"""
    print(f"\n📝 Tracking migration: {args.name}")
    MigrationHelper.track(
        migration_name=args.name,
        description=args.description,
        executed_by=args.by
    )
    print("✓ Migration tracked\n")


def cmd_list_migrations(args):
    """List all tracked migrations"""
    MigrationHelper.list_migrations()


def cmd_init_tracker(args):
    """Initialize migration tracker table"""
    print("\n🔧 Initializing migration tracker...")
    MigrationHelper.init_table()
    print("✓ Migration tracker initialized\n")


def main():
    parser = argparse.ArgumentParser(
        description='IGA Database Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all seeders
  python manage_db.py seed

  # List registered seeders
  python manage_db.py seeders

  # Track a manual migration
  python manage_db.py track "add_custom_column" -d "Added custom column to users"

  # List tracked migrations
  python manage_db.py migrations

  # Initialize migration tracker
  python manage_db.py init
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Seed command
    parser_seed = subparsers.add_parser('seed', help='Run all seeders')
    parser_seed.set_defaults(func=cmd_seed_all)
    
    # List seeders command
    parser_seeders = subparsers.add_parser('seeders', help='List registered seeders')
    parser_seeders.set_defaults(func=cmd_list_seeders)
    
    # Track migration command
    parser_track = subparsers.add_parser('track', help='Track a manual migration')
    parser_track.add_argument('name', help='Migration name')
    parser_track.add_argument('-d', '--description', help='Migration description')
    parser_track.add_argument('-b', '--by', default='manual', help='Executed by (default: manual)')
    parser_track.set_defaults(func=cmd_track_migration)
    
    # List migrations command
    parser_migrations = subparsers.add_parser('migrations', help='List tracked migrations')
    parser_migrations.set_defaults(func=cmd_list_migrations)
    
    # Init tracker command
    parser_init = subparsers.add_parser('init', help='Initialize migration tracker')
    parser_init.set_defaults(func=cmd_init_tracker)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
