# Prerequisites
This document outlines all the required tools and software needed to develop and run the awesome-docify project.

## Required Tools

- **UV** - Fast Python package manager
- **PNPM** - Fast Next.js & React package manager
- **Make** - Build automation tool
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration
- **Pre-commit** - Git hooks for code quality

Depending on the operating system, choose the installation guide from the following links:

### Installation Guides:
- [UV Installation](https://docs.astral.sh/uv/getting-started/installation/)
- [PNPM Installation](https://pnpm.io/installation)
- [Next.js Installation](https://nextjs.org/docs/getting-started/installation)
- [React Installation](https://react.dev/learn/start-a-new-react-project)
- [Docker Installation](https://docs.docker.com/get-docker/)
- [Docker Compose Installation](https://docs.docker.com/compose/install/)
- [Pre-commit Installation](https://pre-commit.com/#install)

### Quick Verification

Run this command to verify all prerequisites are installed:

```bash
echo "UV: $(uv --version)" && echo "PNPM: $(pnpm --version)" && echo "Docker: $(docker --version)" && echo "Docker Compose: $(docker compose version)" && echo "Pre-commit: $(pre-commit --version)" && echo "Make: $(make --version)"
```
