import json
from typing import Dict, Any, Optional


class SchemaInferrer:
    """Infer JSON schemas from sample response data."""

    @staticmethod
    def infer(data: Any) -> Dict[str, Any]:
        """Infer schema from sample data."""
        if data is None:
            return {"type": "null"}
        
        if isinstance(data, bool):
            return {"type": "boolean"}
        
        if isinstance(data, int):
            return {"type": "integer"}
        
        if isinstance(data, float):
            return {"type": "number"}
        
        if isinstance(data, str):
            return {"type": "string"}
        
        if isinstance(data, list):
            if not data:
                return {"type": "array", "items": {}}
            
            item_schemas = [SchemaInferrer.infer(item) for item in data]
            merged = SchemaInferrer._merge_schemas(item_schemas)
            return {"type": "array", "items": merged}
        
        if isinstance(data, dict):
            properties = {}
            for key, value in data.items():
                properties[key] = SchemaInferrer.infer(value)
            
            return {
                "type": "object",
                "properties": properties
            }
        
        return {"type": "unknown"}

    @staticmethod
    def _merge_schemas(schemas: list) -> Dict[str, Any]:
        """Merge multiple schemas into one."""
        if not schemas:
            return {}
        
        first = schemas[0]
        first_type = first.get("type")
        
        if all(s.get("type") == first_type for s in schemas):
            if first_type == "object":
                all_props = {}
                for schema in schemas:
                    all_props.update(schema.get("properties", {}))
                return {"type": "object", "properties": all_props}
            return first
        
        return {"type": "object"}


class ResponseAnalyzer:
    """Analyze response bodies to infer structure."""

    @staticmethod
    def get_schema(body: Any) -> Dict[str, Any]:
        """Get schema for response body."""
        return SchemaInferrer.infer(body)

    @staticmethod
    def describe_response(body: Any) -> str:
        """Generate human description of response."""
        if body is None:
            return "Empty response"
        
        if isinstance(body, dict):
            if "products" in body and isinstance(body["products"], list):
                return f"List of {len(body.get('products', []))} products with metadata"
            elif "users" in body and isinstance(body["users"], list):
                return f"List of {len(body.get('users', []))} users"
            elif "id" in body:
                keys = ", ".join(str(k) for k in list(body.keys())[:3])
                return f"Object with fields: {keys}"
            else:
                keys = ", ".join(str(k) for k in list(body.keys())[:3])
                return f"Response object: {keys}"
        
        if isinstance(body, list):
            if body and isinstance(body[0], dict):
                keys = ", ".join(str(k) for k in list(body[0].keys())[:3])
                return f"Array of {len(body)} objects with fields: {keys}"
            return f"Array with {len(body)} items"
        
        if isinstance(body, str):
            return f"String: {body[:50]}"
        
        return str(type(body).__name__)
