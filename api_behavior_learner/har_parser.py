import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs


@dataclass
class HTTPRequest:
    method: str
    url: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, List[str]]
    body: Optional[Any] = None


@dataclass
class HTTPResponse:
    status: int
    headers: Dict[str, str]
    body: Optional[Any] = None


@dataclass
class HTTPTransaction:
    request: HTTPRequest
    response: HTTPResponse
    time: float  # ms


class HARParser:
    """Parse HTTP Archive (HAR) files."""

    def __init__(self, har_path: str):
        self.har_path = har_path

    def load(self) -> List[HTTPTransaction]:
        """Load and parse HAR file, returning list of HTTP transactions."""
        with open(self.har_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transactions = []
        entries = data.get('log', {}).get('entries', [])

        for entry in entries:
            req_data = entry.get('request', {})
            res_data = entry.get('response', {})
            time_ms = entry.get('time', 0.0)

            # Parse Request
            url = req_data.get('url', '')
            parsed_url = urlparse(url)
            
            headers_raw = req_data.get('headers', [])
            if isinstance(headers_raw, dict):
                headers = headers_raw
            else:
                headers = {
                    h.get('name'): h.get('value')
                    for h in headers_raw
                }

            query_params = parse_qs(parsed_url.query)

            # Request Body
            post_data = req_data.get('postData', {})
            req_body = post_data.get('text')
            if req_body and post_data.get('mimeType', '').startswith('application/json'):
                try:
                    req_body = json.loads(req_body)
                except json.JSONDecodeError:
                    pass

            # Filter out static assets / noise
            path = parsed_url.path.lower()
            ignored_extensions = ('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', '.woff', '.woff2', '.ttf')
            if path.endswith(ignored_extensions) or 'favicon' in path:
                continue

            request = HTTPRequest(
                method=req_data.get('method', 'GET'),
                url=url,
                path=parsed_url.path,
                headers=headers,
                query_params=query_params,
                body=req_body
            )

            # Parse Response
            res_headers_raw = res_data.get('headers', [])
            if isinstance(res_headers_raw, dict):
                res_headers = res_headers_raw
            else:
                res_headers = {
                    h.get('name'): h.get('value')
                    for h in res_headers_raw
                }

            # Response Body
            res_content = res_data.get('content', {})
            res_body = res_content.get('text')
            if res_body and res_content.get('mimeType', '').startswith('application/json'):
                try:
                    res_body = json.loads(res_body)
                except json.JSONDecodeError:
                    pass

            response = HTTPResponse(
                status=res_data.get('status', 0),
                headers=res_headers,
                body=res_body
            )

            transactions.append(HTTPTransaction(
                request=request,
                response=response,
                time=time_ms
            ))

        return transactions
