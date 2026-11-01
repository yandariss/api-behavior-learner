import json
import os
from typing import Dict, Any, Optional
from api_behavior_learner.grouper import EndpointPattern


class LLMAnalyzer:
    """Use LLM to analyze API patterns and infer behavior."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package not installed, LLM features disabled")

    def analyze_endpoint(self, endpoint: EndpointPattern) -> Dict[str, Any]:
        """Analyze endpoint pattern and infer purpose, parameters, responses."""
        if not self.client:
            return self._analyze_without_llm(endpoint)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an API analyst. Analyze HTTP endpoint patterns and infer their purpose, required parameters, and response types. Respond in JSON format."
                    },
                    {
                        "role": "user",
                        "content": self._build_prompt(endpoint)
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except Exception as e:
            print(f"LLM analysis failed: {e}, using fallback")
            return self._analyze_without_llm(endpoint)

    def _build_prompt(self, endpoint: EndpointPattern) -> str:
        """Build analysis prompt from endpoint data."""
        methods = ", ".join(sorted(endpoint.methods))
        status_codes = ", ".join(sorted(str(s) for s in endpoint.status_codes))
        params = ", ".join(sorted(endpoint.param_names)) if endpoint.param_names else "none"

        # Get sample request/response
        sample_tx = endpoint.transactions[0] if endpoint.transactions else None
        sample_body = ""
        sample_response = ""

        if sample_tx:
            if sample_tx.request.body:
                sample_body = f"Sample request body: {json.dumps(sample_tx.request.body)[:200]}"
            if sample_tx.response.body:
                sample_response = f"Sample response body: {json.dumps(sample_tx.response.body)[:200]}"

        prompt = f"""Analyze this API endpoint:

Pattern: {endpoint.pattern}
Methods: {methods}
Status Codes: {status_codes}
Query Parameters: {params}
{sample_body}
{sample_response}

Provide JSON with:
- "purpose": what this endpoint does
- "resource": what resource it manages
- "methods_info": object with each method's description
- "parameters": list of parameter descriptions
- "response_type": type of data returned
- "authentication": whether authentication appears required
- "rate_limit": whether rate limiting appears present
"""
        return prompt

    def _analyze_without_llm(self, endpoint: EndpointPattern) -> Dict[str, Any]:
        """Fallback analysis without LLM."""
        methods = list(endpoint.methods)
        
        # Infer resource from path
        parts = endpoint.pattern.strip('/').split('/')
        resource = parts[0] if parts else 'resource'

        # Infer read vs write
        read_methods = {'GET', 'HEAD', 'OPTIONS'}
        write_methods = {'POST', 'PUT', 'PATCH', 'DELETE'}

        is_collection = '{id}' not in endpoint.pattern
        
        methods_info = {}
        for method in methods:
            if method in read_methods:
                desc = f"Retrieve {resource}"
                if not is_collection:
                    desc = f"Get single {resource}"
            elif method in write_methods:
                desc = f"Modify {resource}"
            else:
                desc = f"Perform {method} on {resource}"
            methods_info[method] = desc

        return {
            "purpose": f"Manage {resource} resources",
            "resource": resource,
            "methods_info": methods_info,
            "parameters": list(endpoint.param_names),
            "response_type": "JSON",
            "authentication": "unknown",
            "rate_limit": "unknown"
        }
