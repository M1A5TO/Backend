#!/usr/bin/env python3
"""
Script to export FastAPI documentation to static HTML files.
Generates both ReDoc and Swagger UI versions.
"""
import json
import os
import sys
from pathlib import Path

# Add api directory to path
sys.path.insert(0, str(Path(__file__).parent / "api"))

try:
    from fastapi.openapi.utils import get_openapi
    from api.app.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    print("Install dependencies with: pip install -r api/requirements.txt")
    sys.exit(1)


def generate_openapi_schema():
    """Generate OpenAPI schema from FastAPI app."""
    openapi_schema = get_openapi(
        title=app.title if hasattr(app, 'title') else "API Documentation",
        version=app.version if hasattr(app, 'version') else "1.0.0",
        description=app.description if hasattr(app, 'description') else "API Documentation",
        routes=app.routes,
    )
    return openapi_schema


def generate_redoc_html(openapi_schema: dict, output_file: str = "docs/redoc.html"):
    """Generate ReDoc HTML from OpenAPI schema."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    schema_json = json.dumps(openapi_schema, indent=2)
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>API Documentation - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url='data:text/json;charset=utf-8,{schema_json.replace("'", "\\'")}'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    
    # Escape properly for HTML
    import html
    schema_json_escaped = html.escape(json.dumps(openapi_schema))
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>API Documentation - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec='{schema_json_escaped}'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ Generated ReDoc HTML: {output_file}")


def generate_swagger_html(openapi_schema: dict, output_file: str = "docs/swagger.html"):
    """Generate Swagger UI HTML from OpenAPI schema."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    schema_json = json.dumps(openapi_schema, indent=2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>API Documentation - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                spec: {schema_json},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }})
        }}
    </script>
</body>
</html>"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ Generated Swagger UI HTML: {output_file}")


def save_openapi_json(openapi_schema: dict, output_file: str = "docs/openapi.json"):
    """Save OpenAPI schema as JSON."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved OpenAPI JSON: {output_file}")


def main():
    print("Generating API documentation...")
    
    # Generate OpenAPI schema
    openapi_schema = generate_openapi_schema()
    
    # Save JSON schema
    save_openapi_json(openapi_schema)
    
    # Generate HTML documentation
    generate_redoc_html(openapi_schema)
    generate_swagger_html(openapi_schema)
    
    print("\n✅ Documentation exported successfully!")
    print("\nGenerated files:")
    print("  - docs/openapi.json (OpenAPI schema)")
    print("  - docs/redoc.html (ReDoc - interactive)")
    print("  - docs/swagger.html (Swagger UI - interactive)")
    print("\nOpen docs/redoc.html or docs/swagger.html in your browser!")


if __name__ == "__main__":
    main()

