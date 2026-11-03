from dataclasses import dataclass
from typing import Any

from api_behavior_learner.grouper import EndpointPattern


@dataclass(frozen=True)
class AuthScheme:
    name: str
    type: str
    scheme: str | None = None
    bearer_format: str | None = None
    parameter_name: str | None = None
    location: str | None = None

    def openapi(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type}
        if self.scheme:
            result["scheme"] = self.scheme
        if self.bearer_format:
            result["bearerFormat"] = self.bearer_format
        if self.parameter_name:
            result["name"] = self.parameter_name
        if self.location:
            result["in"] = self.location
        return result


class AuthDetector:
    """Detect authentication schemes without exposing credential values."""

    @classmethod
    def detect_endpoint(cls, endpoint: EndpointPattern) -> list[AuthScheme]:
        schemes: dict[str, AuthScheme] = {}
        for transaction in endpoint.transactions:
            headers = {
                str(key).lower(): str(value)
                for key, value in transaction.request.headers.items()
            }
            authorization = headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                schemes["bearerAuth"] = AuthScheme(
                    name="bearerAuth", type="http", scheme="bearer", bearer_format="JWT"
                )
            elif authorization.lower().startswith("basic "):
                schemes["basicAuth"] = AuthScheme(
                    name="basicAuth", type="http", scheme="basic"
                )
            elif authorization:
                schemes["authorizationAuth"] = AuthScheme(
                    name="authorizationAuth", type="http", scheme="bearer"
                )

            for header_name in ("x-api-key", "api-key"):
                if header_name in headers:
                    schemes["apiKeyHeader"] = AuthScheme(
                        name="apiKeyHeader",
                        type="apiKey",
                        parameter_name=header_name,
                        location="header",
                    )
            if "x-auth-token" in headers:
                schemes["authTokenHeader"] = AuthScheme(
                    name="authTokenHeader",
                    type="apiKey",
                    parameter_name="X-Auth-Token",
                    location="header",
                )
            if headers.get("cookie"):
                schemes["cookieAuth"] = AuthScheme(
                    name="cookieAuth",
                    type="apiKey",
                    parameter_name="Cookie",
                    location="cookie",
                )
        return list(schemes.values())

    @classmethod
    def detect_all(cls, endpoints: dict[str, EndpointPattern]) -> dict[str, AuthScheme]:
        schemes: dict[str, AuthScheme] = {}
        for endpoint in endpoints.values():
            for scheme in cls.detect_endpoint(endpoint):
                schemes[scheme.name] = scheme
        return schemes

    @classmethod
    def label(cls, endpoint: EndpointPattern) -> str:
        schemes = cls.detect_endpoint(endpoint)
        if not schemes:
            return "Not detected"
        return ", ".join(scheme.name for scheme in schemes)
