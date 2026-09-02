"""
Root execution proxy for University Student Course Enrollment Portal.
Run `python main.py` or `python portal_server.py` to start on http://localhost:8000/
"""

import sys
import argparse
from portal_server import run_portal_server, PORT


def main():
    parser = argparse.ArgumentParser(description="University Student Course Enrollment Portal")
    parser.add_argument("--port", type=int, default=PORT, help="Port to bind server (default: 8000)")
    parser.add_argument("--tests", action="store_true", help="Run automated test suite (TC-01 to TC-10)")
    parser.add_argument("--server", action="store_true", default=True, help="Run localhost web application (default)")

    args = parser.parse_args()

    if args.tests:
        from test_cases import run_tests
        success = run_tests()
        sys.exit(0 if success else 1)
    else:
        server = run_portal_server(args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            server.server_close()


if __name__ == "__main__":
    main()
