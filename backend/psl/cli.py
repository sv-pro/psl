#!/usr/bin/env python3
"""CLI interface for PSL health checks and utilities"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from .health import HealthChecker, format_health_report, HealthStatus


def cmd_healthcheck(args):
    """Run health checks on all providers"""
    print("Running PSL health checks...\n")

    checker = HealthChecker()
    results = checker.check_all()

    # Print report
    report = format_health_report(results)
    print(report)

    # Exit code based on results
    if args.strict:
        # In strict mode, fail if any provider is unhealthy
        if any(c.status == HealthStatus.UNHEALTHY for c in results.values()):
            print("\n⚠️  Some providers are unhealthy (strict mode enabled)")
            return 1
    else:
        # In normal mode, only fail if all configured providers are unhealthy
        configured = [c for c in results.values() if c.api_key_configured]
        if configured and all(c.status == HealthStatus.UNHEALTHY for c in configured):
            print("\n⚠️  All configured providers are unhealthy")
            return 1

    # Check if at least one provider is healthy
    if any(c.status == HealthStatus.HEALTHY for c in results.values()):
        print("\n✅ At least one provider is healthy - ready to use!")
        return 0
    else:
        print("\n⚠️  No healthy providers found. Configure API keys in .env file.")
        return 1


def cmd_check_provider(args):
    """Check a specific provider"""
    checker = HealthChecker()
    available_providers = checker.get_available_providers()

    if args.provider not in available_providers:
        print(f"Error: Unknown provider '{args.provider}'")
        print(f"Available: {', '.join(sorted(available_providers))}")
        return 1

    print(f"Checking {args.provider}...\n")
    
    try:
        result = checker.check_provider(args.provider)
        report = format_health_report({args.provider: result})
        print(report)
        return 0 if result.status == HealthStatus.HEALTHY else 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1


def cmd_list_models(args):
    """List available models from all providers"""
    checker = HealthChecker()
    results = checker.check_all()

    print("Available Models:")
    print("=" * 70)

    for provider_key, check in results.items():
        if check.status == HealthStatus.HEALTHY and check.models_checked:
            print(f"\n{check.provider}:")
            for model in check.models_checked:
                if model.status == HealthStatus.HEALTHY:
                    print(f"  • {model.model}")
                    if model.message and model.message != "Model available":
                        print(f"    {model.message}")
        elif check.status == HealthStatus.UNCONFIGURED:
            print(f"\n{check.provider}: Not configured")
        elif check.status == HealthStatus.UNHEALTHY:
            print(f"\n{check.provider}: {check.message}")

    print()
    return 0


def main():
    """Main CLI entry point"""
    # Load .env file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print("⚠️  Warning: .env file not found. API keys may not be configured.")
        print(f"   Expected location: {env_file.absolute()}\n")

    parser = argparse.ArgumentParser(
        description="PSL - Prompt Semantic Linter CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  psl healthcheck              Run health checks on all providers
  psl healthcheck --strict     Fail if any provider is unhealthy
  psl check openai             Check only OpenAI provider
  psl list-models              List all available models
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # healthcheck command
    health_parser = subparsers.add_parser(
        "healthcheck",
        help="Check connectivity and model availability for all providers"
    )
    health_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any provider is unhealthy (not just all)"
    )
    health_parser.set_defaults(func=cmd_healthcheck)

    # check command
    check_parser = subparsers.add_parser(
        "check",
        help="Check a specific provider"
    )
    
    # Get available providers dynamically
    try:
        temp_checker = HealthChecker()
        available_providers = temp_checker.get_available_providers()
    except:
        available_providers = ["openai", "anthropic", "google", "ollama"]
    
    check_parser.add_argument(
        "provider",
        choices=sorted(available_providers),
        help="Provider to check"
    )
    check_parser.set_defaults(func=cmd_check_provider)

    # list-models command
    list_parser = subparsers.add_parser(
        "list-models",
        help="List available models from all providers"
    )
    list_parser.set_defaults(func=cmd_list_models)

    # Parse args
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if "--debug" in sys.argv:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
