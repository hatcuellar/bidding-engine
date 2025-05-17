#!/usr/bin/env python
"""
OpenAPI Specification Exporter

This script exports the OpenAPI specification from the FastAPI app for the
platform team to use in client generation and documentation.

The exported specification is a JSON file that describes all available
endpoints, request/response models, and authentication requirements.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

def export_openapi_spec(output_path: str = None) -> None:
    """
    Export the OpenAPI specification from the FastAPI app.
    
    Args:
        output_path: Path to save the exported specification
    """
    # Get the OpenAPI JSON
    openapi_spec = app.openapi()
    
    # Set default output path if not provided
    if not output_path:
        output_path = os.path.join(os.path.dirname(__file__), "openapi_v1.0.0.json")
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write the specification to file
    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
    
    print(f"OpenAPI specification exported to: {output_path}")
    
    # Generate a markdown summary
    summary_path = os.path.splitext(output_path)[0] + "_summary.md"
    generate_api_summary(openapi_spec, summary_path)
    
def generate_api_summary(openapi_spec: dict, output_path: str) -> None:
    """
    Generate a markdown summary of the API endpoints.
    
    Args:
        openapi_spec: OpenAPI specification dictionary
        output_path: Path to save the markdown summary
    """
    with open(output_path, "w") as f:
        f.write(f"# Multi-Model Ad Bidding Engine API v{openapi_spec['info']['version']}\n\n")
        f.write(f"{openapi_spec['info']['description']}\n\n")
        
        f.write("## Endpoints\n\n")
        
        # Group endpoints by tag
        endpoints_by_tag = {}
        for path, methods in openapi_spec["paths"].items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    tags = details.get("tags", ["untagged"])
                    for tag in tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        
                        summary = details.get("summary", path)
                        endpoints_by_tag[tag].append({
                            "method": method.upper(),
                            "path": path,
                            "summary": summary,
                            "description": details.get("description", "")
                        })
        
        # Write endpoints by tag
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            f.write(f"### {tag.capitalize()}\n\n")
            
            for endpoint in sorted(endpoints, key=lambda e: e["path"]):
                f.write(f"#### {endpoint['method']} {endpoint['path']}\n\n")
                f.write(f"{endpoint['summary']}\n\n")
                if endpoint['description']:
                    f.write(f"{endpoint['description']}\n\n")
                f.write("---\n\n")
        
        # Write schemas section
        f.write("## Models\n\n")
        for schema_name, schema in openapi_spec["components"]["schemas"].items():
            f.write(f"### {schema_name}\n\n")
            if "description" in schema:
                f.write(f"{schema['description']}\n\n")
            f.write("---\n\n")
    
    print(f"API summary exported to: {output_path}")

if __name__ == "__main__":
    export_openapi_spec()