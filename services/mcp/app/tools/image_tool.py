from mcp.tools import Tool
from typing import Dict, Any
import httpx
import logging
from app.config import settings
from app.types import ToolDefinition

logger = logging.getLogger(__name__)

class ImageTool(Tool):
    def __init__(self):
        self.definition = ToolDefinition(
            name="image",
            description="Generate and manipulate images",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate", "edit", "analyze"],
                        "description": "The image operation to perform"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt for image generation"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "URL of image to edit or analyze"
                    },
                    "style": {
                        "type": "string",
                        "description": "Style for image generation",
                        "default": "photorealistic"
                    },
                    "size": {
                        "type": "object",
                        "properties": {
                            "width": {"type": "integer"},
                            "height": {"type": "integer"}
                        },
                        "default": {"width": 1024, "height": 1024}
                    },
                    "edits": {
                        "type": "array",
                        "description": "List of edit operations to apply"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis to perform",
                        "default": "general"
                    }
                },
                "required": ["action"]
            }
        )

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def description(self) -> str:
        return self.definition.description or ""

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute image operations"""
        try:
            action = args.get("action")
            if not action:
                raise ValueError("Action is required")
                
            async with httpx.AsyncClient() as client:
                if action == "generate":
                    result = await self._generate_image(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Image generated successfully"
                            },
                            {
                                "type": "image",
                                "url": result.get('image_url')
                            }
                        ]
                    }
                elif action == "edit":
                    result = await self._edit_image(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Image edited successfully"
                            },
                            {
                                "type": "image",
                                "url": result.get('edited_url')
                            }
                        ]
                    }
                elif action == "analyze":
                    result = await self._analyze_image(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Analysis results:"
                            },
                            {
                                "type": "analysis",
                                "data": result.get('analysis', {})
                            }
                        ]
                    }
                else:
                    raise ValueError(f"Unknown action: {action}")
                    
        except Exception as e:
            logger.error(f"Error in image tool: {str(e)}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }

    async def _generate_image(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new image"""
        prompt = args.get("prompt")
        if not prompt:
            raise ValueError("Prompt is required for image generation")
            
        response = await client.post(
            f"{settings.AGENTS_SERVICE_URL}/abilities/image/generate",
            json={
                "prompt": prompt,
                "style": args.get("style", "photorealistic"),
                "size": args.get("size", {"width": 1024, "height": 1024}),
                "metadata": args.get("metadata", {})
            }
        )
        response.raise_for_status()
        return response.json()

    async def _edit_image(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Edit an existing image"""
        image_url = args.get("image_url")
        if not image_url:
            raise ValueError("image_url is required for editing")
            
        response = await client.post(
            f"{settings.AGENTS_SERVICE_URL}/abilities/image/edit",
            json={
                "image_url": image_url,
                "edits": args.get("edits", []),
                "metadata": args.get("metadata", {})
            }
        )
        response.raise_for_status()
        return response.json()

    async def _analyze_image(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image content"""
        image_url = args.get("image_url")
        if not image_url:
            raise ValueError("image_url is required for analysis")
            
        response = await client.post(
            f"{settings.AGENTS_SERVICE_URL}/abilities/image/analyze",
            json={
                "image_url": image_url,
                "analysis_type": args.get("analysis_type", "general"),
                "metadata": args.get("metadata", {})
            }
        )
        response.raise_for_status()
        return response.json() 
