import re
from typing import Dict, List, Set
from dataclasses import dataclass, field
from api_behavior_learner.har_parser import HTTPTransaction


@dataclass
class EndpointPattern:
    """Grouped HTTP endpoint with methods and examples."""
    pattern: str
    methods: Set[str] = field(default_factory=set)
    transactions: List[HTTPTransaction] = field(default_factory=list)
    status_codes: Set[int] = field(default_factory=set)
    param_names: Set[str] = field(default_factory=set)


class EndpointGrouper:
    """Group HTTP transactions by endpoint patterns."""

    def __init__(self, transactions: List[HTTPTransaction]):
        self.transactions = transactions

    def group(self) -> Dict[str, EndpointPattern]:
        """Group transactions by endpoint pattern."""
        patterns: Dict[str, EndpointPattern] = {}

        for tx in self.transactions:
            pattern = self._extract_pattern(tx.request.path)

            if pattern not in patterns:
                patterns[pattern] = EndpointPattern(pattern=pattern)

            ep = patterns[pattern]
            ep.methods.add(tx.request.method)
            ep.transactions.append(tx)
            ep.status_codes.add(tx.response.status)

            # Extract parameter names from query strings
            for param in tx.request.query_params.keys():
                ep.param_names.add(param)

        return patterns

    def _extract_pattern(self, path: str) -> str:
        """Convert path to pattern, replacing IDs with placeholders."""
        if not path:
            return "/"

        # Split path into segments
        segments = path.strip('/').split('/')
        pattern_segments = []

        for seg in segments:
            # Detect UUID patterns (8-4-4-4-12 hex digits)
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', seg, re.I):
                pattern_segments.append('{id}')
            # Detect numeric IDs (all digits, typically 1-20 chars)
            elif re.match(r'^\d{1,20}$', seg):
                pattern_segments.append('{id}')
            # Detect hex IDs (hex string)
            elif re.match(r'^[0-9a-f]+$', seg) and len(seg) > 12:
                pattern_segments.append('{id}')
            else:
                pattern_segments.append(seg)

        return '/' + '/'.join(pattern_segments)
