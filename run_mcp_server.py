#!/usr/bin/env python
"""Run AIPentester MCP server for Claude Code."""

import asyncio
import sys
import os

# Add src to path if running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Log startup to stderr (won't interfere with MCP protocol on stdout)
print("AIPentester MCP server starting...", file=sys.stderr, flush=True)

try:
    from aipentester.mcp_server import main
    print("Imports successful", file=sys.stderr, flush=True)
except Exception as e:
    print(f"Import failed: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    try:
        print("Starting async main...", file=sys.stderr, flush=True)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr, flush=True)
        pass
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
