# Hyperact MCP

An MCP server that surfaces Hyperact blog content. Exposes a resource to list articles and a tool to search for relevant posts by subject, optionally including a content snippet. The server auto-switches transports: stdio by default for local MCP clients, HTTP when `PORT` or `MCP_TRANSPORT=http` is set.

## Requirements
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Configuration
- `HYPERACT_API_BASE_URL` (optional): Base URL for the Hyperact MCP API. Defaults to `https://hyperact.co.uk/api/mcp`.

## Local development
```bash
uv sync            
uv run server.py   
```

Run HTTP locally:
```bash
MCP_TRANSPORT=http PORT=8080 uv run server.py
```

## Docker
```bash
docker build -t hyperact-mcp .
docker run -p 8080:8080 -e PORT=8080 hyperact-mcp
```

## Deploying to Cloud Run (manual)
```bash
PROJECT_ID=your-project
REGION=your-region
IMAGE="gcr.io/${PROJECT_ID}/hyperact-mcp"

docker build -t "$IMAGE" .
docker push "$IMAGE"
gcloud run deploy hyperact-mcp \
  --image "$IMAGE" \
  --region "$REGION" \
  --port 8080 \
  --allow-unauthenticated
```

## Infrastructure as code (Pulumi + uv)
```bash
cd infra
uv sync
export PULUMI_BACKEND_URL="gs://mcp_state_bucket"   # bucket must already exist
pulumi stack init dev
# ensure Docker is running and gcloud auth is configured: gcloud auth configure-docker
pulumi up
```

Pulumi will build and push the Docker image (default: `gcr.io/<gcp_project>/<serviceName>:<stack>`) using the root `Dockerfile`, then deploy Cloud Run + the global HTTPS load balancer. Point `mcp.hyperact.co.uk` at the exported load balancer IP and wait for the managed cert to become ACTIVE.
