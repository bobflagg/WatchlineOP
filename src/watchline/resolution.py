"""Q1.3: turn a typed address into the answer contract.

    {input, outcome, bbl, bin, inGraph, relatedLots, candidates, grc, message, tried}

outcome is one of exact / variant / ambiguous / not_found (specs/questions/q01.md), plus `unavailable` when the
Geosupport service could not be reached. `unavailable` is an outage, never an answer about the address.

Geosupport decides the outcome. The graph only says whether the BBL it returned is a Lot we hold (inGraph) and
which other Lots share its BIN (relatedLots, for example the second lot of a condominium building).
"""
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from neo4j import Driver, RoutingControl

from .geosupport import Client, Outcome, Result


class Match(StrEnum):
    EXACT = "exact"
    VARIANT = "variant"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"


def _norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip().upper()


def classify(r: Result) -> Match:
    """Geosupport result to outcome. Pure. exact means the returned house and street equal the typed ones after
    case and whitespace only; a warning (GRC 01) or a respelled retry makes it a variant."""
    if r.outcome is Outcome.UNAVAILABLE:
        return Match.UNAVAILABLE
    if r.outcome is Outcome.STREET_AMBIGUOUS:
        return Match.AMBIGUOUS
    if r.outcome is Outcome.RESOLVED:
        same = _norm(f"{r.house} {r.street}") == _norm(r.typed)
        return Match.EXACT if same and not r.inferred and r.grc == "00" else Match.VARIANT
    return Match.NOT_FOUND


class Graph(Protocol):
    def has_lot(self, bbl: str) -> bool: ...
    def other_lots_on_bin(self, bin_: str, bbl: str) -> list[str]: ...


class Neo4jGraph:
    """Read-only lookups in the watchline graph."""

    def __init__(self, driver: Driver, database: str):
        self._driver, self._db = driver, database

    def _read(self, query: str, **params):
        return self._driver.execute_query(query, params, database_=self._db, routing_=RoutingControl.READ).records

    def has_lot(self, bbl: str) -> bool:
        return bool(self._read("MATCH (l:Lot {bbl: $bbl}) RETURN l.bbl AS bbl", bbl=bbl))

    def other_lots_on_bin(self, bin_: str, bbl: str) -> list[str]:
        rows = self._read("MATCH (l:Lot)-[:HAS_BUILDING]->(:Building {bin: $bin}) WHERE l.bbl <> $bbl "
                          "RETURN l.bbl AS bbl ORDER BY bbl", bin=bin_, bbl=bbl)
        return [r["bbl"] for r in rows]


@dataclass(frozen=True)
class Answer:
    input: str
    outcome: Match
    bbl: str | None = None
    bin: str | None = None
    in_graph: bool | None = None            # None when there is no BBL to look up
    related_lots: tuple[str, ...] = ()      # other graph Lots that share the BIN
    candidates: tuple[str, ...] = ()        # similar street names, for ambiguous
    grc: str | None = None
    message: str | None = None
    tried: tuple[str, ...] = ()             # every spelling sent to Geosupport
    inferred: bool = False                  # the lot came from a respelled address, not the one typed


def resolve_address(client: Client, graph: Graph, house: str, street: str, *,
                    borough: str | None = None, zip5: str | None = None) -> Answer:
    result, tried = client.resolve(house, street, zip5=zip5, borough=borough)
    outcome = classify(result)
    in_graph, related = None, ()
    if result.bbl:
        in_graph = graph.has_lot(result.bbl)
        if result.bin:
            related = tuple(graph.other_lots_on_bin(result.bin, result.bbl))
    return Answer(input=f"{house} {street}", outcome=outcome, bbl=result.bbl, bin=result.bin, in_graph=in_graph,
                  related_lots=related, candidates=result.candidates, grc=result.grc, message=result.message,
                  tried=tuple(tried), inferred=result.inferred)
