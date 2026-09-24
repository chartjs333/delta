"""Candidate exact coordinate/range projection from the frozen round contract."""

import re


class CoordinateError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise CoordinateError(reason)


def native_schema_projection(contract: dict) -> dict:
    """Resolve all coordinates from immutable metadata, never from observed votes.

    Public parameter IDs identify domain/shard obligations. Their explicit ranges
    refer to a shared ordered vector; each domain covers the entire vector once.
    Shard identity denotes the same contiguous range across every domain.
    """
    schema = contract["parameter_schema"]
    coordinates = schema["coordinates"]
    require(type(coordinates) is list and 0 < len(coordinates) <= 4096, "COORDINATE_BOUND")
    require(
        all(type(c) is str and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", c) for c in coordinates),
        "COORDINATE_IDENTIFIER",
    )
    require(coordinates == sorted(set(coordinates)), "COORDINATE_ORDER")
    ranges = schema["ranges"]
    require(type(ranges) is list and 0 < len(ranges) <= 4096, "COORDINATE_RANGE_BOUND")
    require(
        [item["parameter_id"] for item in ranges] == schema["parameter_ids"],
        "COORDINATE_RANGE_ORDER_OR_COVERAGE",
    )
    by_parameter = {}
    for item in ranges:
        offset, length = item["offset"], item["length"]
        require(
            type(offset) is int
            and type(length) is int
            and offset >= 0
            and length > 0
            and offset + length <= len(coordinates),
            "COORDINATE_RANGE_BOUNDS",
        )
        require(item["parameter_id"] not in by_parameter, "COORDINATE_RANGE_DUPLICATE")
        by_parameter[item["parameter_id"]] = (offset, length)
    domains = contract["round_config"]["domain_ids"]
    coverage = {domain: [] for domain in domains}
    shards = {}
    keys = set()
    for assignment in contract["shard_plan"]["assignments"]:
        parameter, domain, shard = (
            assignment["parameter_id"],
            assignment["domain_id"],
            assignment["shard_id"],
        )
        require(parameter in by_parameter and domain in coverage, "COORDINATE_ASSIGNMENT")
        require((domain, shard) not in keys, "COORDINATE_DOMAIN_SHARD_DUPLICATE")
        keys.add((domain, shard))
        interval = by_parameter[parameter]
        require(shard not in shards or shards[shard] == interval, "COORDINATE_SHARD_ALIAS")
        shards[shard] = interval
        offset, length = interval
        coverage[domain].append((offset, length))
    for intervals in coverage.values():
        cursor = 0
        for offset, length in sorted(intervals):
            require(offset == cursor, "COORDINATE_EXACT_DOMAIN_COVERAGE")
            cursor += length
        require(cursor == len(coordinates), "COORDINATE_EXACT_DOMAIN_COVERAGE")
    require(keys == {(d, s) for d in domains for s in shards}, "COORDINATE_DOMAIN_SHARD_MATRIX")
    return {
        "coordinates": list(coordinates),
        "shards": [
            {"id": shard, "offset": offset, "length": length}
            for shard, (offset, length) in sorted(shards.items())
        ],
    }
