import pytest

from api_behavior_learner.grouper import EndpointGrouper
from api_behavior_learner.har_parser import HARParser
from api_behavior_learner.llm_analyzer import LLMAnalyzer
from api_behavior_learner.schema_inferrer import ResponseAnalyzer, SchemaInferrer
from api_behavior_learner.spec_generator import SpecGenerator


def test_har_parser_load():
    """Test HAR file loading."""
    har_parser = HARParser("samples/sample.har")
    transactions = har_parser.load()

    assert len(transactions) > 0
    assert transactions[0].request.method in ["GET", "POST", "PUT", "DELETE"]
    assert transactions[0].response.status > 0


def test_endpoint_grouper():
    """Test endpoint pattern grouping."""
    har_parser = HARParser("samples/sample.har")
    transactions = har_parser.load()

    grouper = EndpointGrouper(transactions)
    endpoints = grouper.group()

    assert len(endpoints) > 0
    assert any("{id}" in pattern for pattern in endpoints)


def test_pattern_extraction():
    """Test ID pattern replacement."""
    har_parser = HARParser("samples/sample.har")
    transactions = har_parser.load()

    grouper = EndpointGrouper(transactions)
    patterns = [grouper._extract_pattern(tx.request.path) for tx in transactions]

    assert "/users/{id}" in patterns or "/products/{id}" in patterns


def test_schema_inference_primitives():
    """Test schema inference for primitive types."""
    assert SchemaInferrer.infer(None) == {"type": "null"}
    assert SchemaInferrer.infer(True) == {"type": "boolean"}
    assert SchemaInferrer.infer(42) == {"type": "integer"}
    assert SchemaInferrer.infer(3.14) == {"type": "number"}
    assert SchemaInferrer.infer("hello") == {"type": "string"}


def test_schema_inference_array():
    """Test schema inference for arrays."""
    schema = SchemaInferrer.infer([1, 2, 3])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "integer"


def test_schema_inference_object():
    """Test schema inference for objects."""
    data = {"name": "John", "age": 30}
    schema = SchemaInferrer.infer(data)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"


def test_response_analyzer_description():
    """Test response description generation."""
    products_response = {"products": [{"id": 1, "name": "Product 1"}], "total": 1}

    desc = ResponseAnalyzer.describe_response(products_response)
    assert "products" in desc.lower()


def test_request_body_in_openapi():
    """Test request body schema and example generation."""
    transactions = HARParser("samples/sample.har").load()
    endpoints = EndpointGrouper(transactions).group()
    spec = SpecGenerator(LLMAnalyzer(api_key="")).generate_openapi(endpoints)

    create_user = spec["paths"]["/users"]["post"]
    request_body = create_user["requestBody"]
    schema = request_body["content"]["application/json"]["schema"]

    assert request_body["required"] is True
    assert schema["properties"]["name"]["type"] == "string"
    assert request_body["content"]["application/json"]["example"]["email"]


def test_request_body_in_markdown():
    """Test request body example in Markdown output."""
    transactions = HARParser("samples/sample.har").load()
    endpoints = EndpointGrouper(transactions).group()
    docs = SpecGenerator(LLMAnalyzer(api_key="")).generate_markdown(endpoints)

    assert "### Request Body" in docs
    assert '"name": "David"' in docs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
