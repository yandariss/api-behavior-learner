import json
from typing import Any

from api_behavior_learner.auth_detector import AuthDetector
from api_behavior_learner.grouper import EndpointPattern
from api_behavior_learner.llm_analyzer import LLMAnalyzer
from api_behavior_learner.schema_inferrer import ResponseAnalyzer


class SpecGenerator:
    """Generate markdown and OpenAPI specifications."""

    def __init__(self, analyzer: LLMAnalyzer):
        self.analyzer = analyzer

    def generate_markdown(self, endpoints: dict[str, EndpointPattern]) -> str:
        """Generate markdown API documentation."""
        md = "# API Documentation\n\n"
        md += f"Generated from {len(endpoints)} endpoint patterns.\n\n"

        for pattern, endpoint in sorted(endpoints.items()):
            analysis = self.analyzer.analyze_endpoint(endpoint)
            sample_tx = endpoint.transactions[0] if endpoint.transactions else None
            request_tx = next(
                (tx for tx in endpoint.transactions if tx.request.body is not None),
                None,
            )
            auth_label = AuthDetector.label(endpoint)
            response_desc = ""

            if sample_tx and sample_tx.response.body:
                response_desc = ResponseAnalyzer.describe_response(
                    sample_tx.response.body
                )

            if request_tx:
                md += "### Request Body\n\n"
                md += "```json\n"
                md += json.dumps(request_tx.request.body, indent=2)
                md += "\n```\n\n"

            md += f"## {analysis.get('resource', 'Resource').title()}\n\n"
            md += f"**Pattern:** `{pattern}`\n\n"
            md += f"**Purpose:** {analysis.get('purpose', 'Unknown')}\n\n"
            md += f"**Authentication:** {auth_label}\n\n"

            md += "### Methods\n\n"
            for method in sorted(endpoint.methods):
                desc = analysis.get("methods_info", {}).get(method, f"{method} request")
                md += f"- **{method}**: {desc}\n"
            md += "\n"

            if endpoint.param_names:
                md += "### Query Parameters\n\n"
                for param in sorted(endpoint.param_names):
                    md += f"- `{param}`: Unknown type\n"
                md += "\n"

            md += "### Response\n\n"
            md += f"- **Type:** {analysis.get('response_type', 'JSON')}\n"
            if response_desc:
                md += f"- **Description:** {response_desc}\n"
            md += f"- **Status Codes:** {', '.join(sorted(str(s) for s in endpoint.status_codes))}\n"
            md += "\n"

        return md

    def generate_openapi(
        self,
        endpoints: dict[str, EndpointPattern],
        title: str = "API",
        version: str = "1.0.0",
    ) -> dict[str, Any]:
        """Generate OpenAPI 3.0.0 specification."""
        detected_auth = AuthDetector.detect_all(endpoints)

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
                "description": "Generated from HTTP traffic analysis",
            },
            "servers": [
                {"url": "https://api.example.com", "description": "API Server"}
            ],
            "paths": {},
        }

        if detected_auth:
            spec["components"] = {
                "securitySchemes": {
                    name: scheme.openapi() for name, scheme in detected_auth.items()
                }
            }

        for pattern, endpoint in endpoints.items():
            analysis = self.analyzer.analyze_endpoint(endpoint)
            sample_tx = endpoint.transactions[0] if endpoint.transactions else None
            request_tx = next(
                (tx for tx in endpoint.transactions if tx.request.body is not None),
                None,
            )
            auth_schemes = AuthDetector.detect_endpoint(endpoint)

            if pattern not in spec["paths"]:
                spec["paths"][pattern] = {}

            for method in sorted(endpoint.methods):
                method_lower = method.lower()
                method_desc = analysis.get("methods_info", {}).get(method, "")

                operation = {
                    "summary": method_desc or f"{method} {pattern}",
                    "tags": [analysis.get("resource", "resource").title()],
                    "responses": {},
                }

                if auth_schemes:
                    operation["security"] = [
                        {scheme.name: []} for scheme in auth_schemes
                    ]

                # Add parameter documentation
                if endpoint.param_names:
                    operation["parameters"] = [
                        {
                            "name": param,
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        }
                        for param in sorted(endpoint.param_names)
                    ]

                if request_tx:
                    operation["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": ResponseAnalyzer.get_schema(
                                    request_tx.request.body
                                ),
                                "example": request_tx.request.body,
                            }
                        },
                    }

                # Add response schemas with inferred types
                for status in sorted(endpoint.status_codes):
                    response_schema = {"type": "object"}
                    response_desc = "Response"

                    if sample_tx and sample_tx.response.body:
                        response_schema = ResponseAnalyzer.get_schema(
                            sample_tx.response.body
                        )
                        response_desc = ResponseAnalyzer.describe_response(
                            sample_tx.response.body
                        )

                    operation["responses"][str(status)] = {
                        "description": response_desc,
                        "content": {"application/json": {"schema": response_schema}},
                    }

                if not operation["responses"]:
                    operation["responses"]["200"] = {
                        "description": "Success",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }

                spec["paths"][pattern][method_lower] = operation

        return spec
