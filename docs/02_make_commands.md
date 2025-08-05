# Makefile Commands Documentation

This document describes all available Makefile commands for the Awesome Docify project.

## Makefile Commands

```bash
# Development
make install          # Install all dependencies
make start-backend    # Start backend server
make start-frontend   # Start frontend server

# Docker
make docker-up        # Start all services
make docker-down      # Stop all services
make docker-logs      # View logs
make status           # Check service status

# Help
make help             # Show the available commands
