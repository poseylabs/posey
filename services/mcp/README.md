# Posey MCP Server

A Model Context Protocol (MCP) server implementation for the Posey.AI platform that enables seamless integration between LLMs and Posey's specialized agents and abilities.

## Features

- Agent delegation and task management
- Memory operations (store/retrieve/search)
- Image generation and manipulation
- Extensible tool system

## Setup
All services are meant to be run from the root of the /services folder using docker compose:

1. Build the Docker image:
```bash
docker compose build posey-mcp
```

2. Run the container:
```bash
docker compose up posey-mcp
```

## Available Tools

### Agent Tool
Delegate tasks to specialized agents:
```json
{
    "name": "agent",
    "arguments": {
        "action": "delegate",
        "task": "Generate an image of a sunset",
        "agent_id": "image_agent"
    }
}
```

### Memory Tool
Manage agent memories:
```json
{
    "name": "memory",
    "arguments": {
        "action": "store",
        "content": "User prefers minimalist design",
        "metadata": {
            "category": "preferences"
        }
    }
}
```

### Image Tool
Generate and manipulate images:
```json
{
    "name": "image",
    "arguments": {
        "action": "generate",
        "prompt": "A beautiful sunset over mountains",
        "style": "photorealistic"
    }
}
```

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run locally:
```bash
python -m app.main
```

## Testing

Run tests:
```bash
pytest tests/
``` 
