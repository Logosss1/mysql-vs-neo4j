"""Read the PDF data, keep source details, check records, and count them."""
from __future__ import annotations

from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from .curation import AUDIENCES, ISSUES, RELATIONS, ROWS, TOPICS

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ID = "vpl1"


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_mentions(text: str) -> tuple[list[dict], list[dict]]:
    # Remove page numbers. Keep page breaks to track each citation's page.
    pages = [re.sub(r"\n\s*\d+\s*$", "", page) for page in text.split("\f")]
    body = "\f\n".join(pages)
    mentions = []

    def add(start, end, mention_id, category, position, resource_id):
        excerpt = body[start:end].strip()
        actual_start = start + len(body[start:end]) - len(body[start:end].lstrip())
        actual_end = end - len(body[start:end]) + len(body[start:end].rstrip())
        retrieved = re.search(r"Retrieved\s+September\s+(\d+),\s*2026", excerpt)
        mentions.append({
            "id": mention_id, "resource_id": resource_id, "source_id": SOURCE_ID,
            "source_category": category, "source_position": position,
            "page_start": body[:actual_start].count("\f") + 1,
            "page_end": body[:actual_end].count("\f") + 1,
            "citation_raw": excerpt,
            "retrieved_on": f"2026-09-{int(retrieved[1]):02}" if retrieved else None,
        })

    def numbered(start, end, prefix, category, offset):
        matches = list(re.finditer(r"(?m)^\s*(\d+)\.\s+", body[start:end]))
        for i, match in enumerate(matches):
            number = int(match[1])
            stop = start + matches[i + 1].start() if i + 1 < len(matches) else end
            add(start + match.start(), stop, f"{prefix}-{number:02}", category,
                number, f"r{offset + number:03}")

    bibliography = body.index("1. Ansberry,")
    videos = body.index("\nVideos", bibliography)
    podcasts = body.index("\nPodcasts", videos)
    websites = body.index("\nWebsites", podcasts)
    hotlines = body.index("\nHotlines", websites)
    flyers = body.index("Fliers & Written Resources", hotlines)
    numbered(bibliography, videos, "bib", "bibliography", 0)
    numbered(videos + len("\nVideos"), podcasts, "video", "Videos", 32)
    add(podcasts + len("\nPodcasts"), websites, "podcast-01", "Podcasts", 1, "r046")
    add(websites + len("\nWebsites"), hotlines, "website-01", "Websites", 1, "r022")
    hotline_start = hotlines + len("\nHotlines")
    hotline_match = re.search(r"National Elder Fraud Hotline[^\n]+", body[hotline_start:flyers])
    if not hotline_match:
        raise ValueError("Hotline source block changed")
    add(hotline_start + hotline_match.start(), hotline_start + hotline_match.end(),
        "hotline-01", "Hotlines", 1, "r047")
    bullets = list(re.finditer("●", body[flyers:]))
    for i, match in enumerate(bullets):
        end = flyers + bullets[i + 1].start() if i + 1 < len(bullets) else len(body)
        add(flyers + match.end(), end, f"flyer-{i+1:02}", "Fliers & Written Resources",
            i + 1, f"r{48+i:03}")

    statements = []
    headings = [body.index("1. Users."), body.index("2. Topic or focus"),
                body.index("3. Outcomes or goals"), body.index("4. Resources or materials")]
    for i, kind in enumerate(["audiences", "topics", "goals"]):
        start, end = headings[i:i+2]
        statements.append({"id": f"plan-{kind}", "source_id": SOURCE_ID, "statement_kind": kind,
                           "page_start": body[:start].count("\f") + 1,
                           "page_end": body[:end].count("\f") + 1,
                           "statement_text": body[start:end].strip()})
    orphan_start = hotline_start + hotline_match.end()
    orphan = normalized(body[orphan_start:flyers])
    if orphan:
        statements.append({"id": "plan-unassigned", "source_id": SOURCE_ID,
                           "statement_kind": "unassigned_fragment", "page_start": 4, "page_end": 4,
                           "statement_text": orphan})
    return mentions, statements


def build_dataset(root: Path = ROOT) -> dict[str, list[dict]]:
    pdf_path, text_path = root / "VPL-1_resources.pdf", root / "data/source.txt"
    source_text = text_path.read_text(encoding="utf-8")
    mentions, statements = extract_mentions(source_text)
    tables = {name: [] for name in [
        "source_document", "resource", "source_mention", "agent", "resource_agent", "format",
        "resource_format", "topic", "audience", "resource_topic", "resource_audience", "identifier",
        "quality_issue", "resource_relation", "planning_statement", "age_definition",
    ]}
    tables["source_document"] = [{"id": SOURCE_ID, "filename": pdf_path.name,
                                  "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                                  "text_sha256": hashlib.sha256(text_path.read_bytes()).hexdigest(),
                                  "page_count": 5, "ingested_on": "2026-10-21"}]
    tables["source_mention"] = mentions
    tables["planning_statement"] = statements
    extension_pages = {"accessible_design": 3, "accessibility": 3, "social_engineering": 3,
                       "reporting_support": 2, "shopping_scams": 4, "predatory_lending": 4,
                       "tax_assistance": 2}
    tables["topic"] = [{"id": key, "name": value, "source_id": SOURCE_ID,
                        "source_page": extension_pages.get(key, 1),
                        "basis": "curator_extension_from_citation" if key in extension_pages and key not in
                        ("reporting_support", "tax_assistance") else "source_planning_vocabulary"}
                       for key, value in TOPICS.items()]
    tables["audience"] = [{"id": key, "name": value, "source_id": SOURCE_ID,
                           "source_page": 3 if key == "people_with_disabilities" else 1}
                           for key, value in AUDIENCES.items()]
    agents = {}
    for index, row in enumerate(ROWS, 1):
        title, published, format_id, creators, publisher, container, locators, topics = row
        rid = f"r{index:03}"
        mention = next(m for m in mentions if m["resource_id"] == rid)
        precision = {4: "year", 7: "month", 10: "day"}.get(len(published or ""), "unknown")
        tables["resource"].append({"id": rid, "title": title, "publication_value": published,
                                   "publication_precision": precision, "container_title": container,
                                   "publisher_statement": publisher,
                                   "citation_text": normalized(mention["citation_raw"]),
                                   "verification_status": "unverified"})
        tables["resource_format"].append({"resource_id": rid, "format_id": format_id,
                                          "source_mention_id": mention["id"], "basis": "provisional_curation"})
        publisher_credit = []
        if publisher and publisher != "Independently published":
            publisher_credit = [("P:" if publisher == "Michael D. Rudy" else "O:") + publisher]
        for role, names in [("creator", creators), ("publisher", publisher_credit)]:
            for position, name in enumerate(names, 1):
                kind, label = name.split(":", 1)
                key = (kind, label)
                if key not in agents:
                    agents[key] = f"a{len(agents)+1:03}"
                    tables["agent"].append({"id": agents[key], "name": label,
                                            "agent_kind": "person" if kind == "P" else "organization",
                                            "identity_status": "source_local_unverified"})
                tables["resource_agent"].append({"resource_id": rid, "agent_id": agents[key],
                                                 "contribution_role": role, "credit_order": position,
                                                 "source_mention_id": mention["id"]})
        for topic in topics:
            tables["resource_topic"].append({"resource_id": rid, "topic_id": topic,
                                             "source_mention_id": mention["id"],
                                             "basis": "inferred_from_citation", "review_status": "proposed"})
        # Audience tags show the intended readers. They still need review.
        audiences = {"older_adults": "collection_context"}
        if index in (15, 24):
            audiences.update(caregivers="inferred_from_title", family="inferred_from_title")
        if index == 15:
            audiences["library_staff"] = "inferred_from_title"
        if index == 20:
            audiences["people_with_disabilities"] = "inferred_from_title"
        for audience, basis in audiences.items():
            tables["resource_audience"].append({"resource_id": rid, "audience_id": audience,
                                                "source_mention_id": mention["id"], "basis": basis,
                                                "review_status": "proposed"})
        for locator in locators:
            kind, value = ("phone", locator[4:]) if locator.startswith("tel:") else ("url", locator)
            tables["identifier"].append({"id": f"i{len(tables['identifier'])+1:03}", "resource_id": rid,
                                         "identifier_kind": kind, "identifier_value": value,
                                         "source_mention_id": mention["id"]})
            if locator.startswith("https://doi.org/"):
                tables["identifier"].append({"id": f"i{len(tables['identifier'])+1:03}", "resource_id": rid,
                                             "identifier_kind": "doi", "identifier_value": locator[16:].lower(),
                                             "source_mention_id": mention["id"]})
        issues = list(ISSUES.get(index, []))
        if not locators:
            issues.append(("missing_locator", "No URL, DOI, or telephone locator supplied; do not invent one."))
        if not creators:
            issues.append(("missing_creator", "Creator or service operator is not established by this citation."))
        for code, detail in issues:
            tables["quality_issue"].append({"id": f"q{len(tables['quality_issue'])+1:03}",
                                            "mention_id": mention["id"], "issue_code": code,
                                            "detail": detail, "review_status": "open"})
    tables["format"] = [{"id": key, "name": key.replace("_", " ").title()}
                         for key in sorted({r[2] for r in ROWS})]
    for i, (left, right, kind, evidence) in enumerate(RELATIONS, 1):
        left_mention = next(m["id"] for m in mentions if m["resource_id"] == left)
        right_mention = next(m["id"] for m in mentions if m["resource_id"] == right)
        tables["resource_relation"].append({"id": f"rel{i:03}", "from_resource_id": left,
                                             "to_resource_id": right, "relation_kind": kind,
                                             "evidence": evidence, "review_status": "proposed",
                                             "from_mention_id": left_mention, "to_mention_id": right_mention})
    for i, (age, comparison, evidence) in enumerate([
        (55, ">=", "55 or older"), (60, ">=", "60 or older"), (65, ">=", "65 or older"),
        (65, ">", "members of the elderly community (> 65 years old)"),
    ], 1):
        tables["age_definition"].append({"id": f"age{i}", "audience_id": "older_adults",
                                          "source_id": SOURCE_ID, "source_page": 1, "minimum_age": age,
                                          "comparison_operator": comparison, "evidence": evidence,
                                          "review_status": "unresolved"})
    validate(tables)
    return tables


def validate(tables: dict) -> None:
    resources = {r["id"] for r in tables["resource"]}
    if len(resources) != len(tables["resource"]):
        raise ValueError("Duplicate resource ID")
    mention_map = {m["id"]: m for m in tables["source_mention"]}
    for mention in mention_map.values():
        if mention["resource_id"] not in resources or not 1 <= mention["page_start"] <= mention["page_end"] <= 5:
            raise ValueError(f"Invalid mention: {mention['id']}")
    identifiers = set()
    for identifier in tables["identifier"]:
        key = (identifier["identifier_kind"], identifier["identifier_value"])
        if key in identifiers:
            raise ValueError(f"Duplicate identifier: {key}")
        identifiers.add(key)
    for resource in tables["resource"]:
        value, precision = resource["publication_value"], resource["publication_precision"]
        patterns = {"year": r"\d{4}", "month": r"\d{4}-\d{2}", "day": r"\d{4}-\d{2}-\d{2}"}
        if precision == "unknown":
            if value is not None:
                raise ValueError("Unknown dates must be null")
        else:
            if not value or not re.fullmatch(patterns[precision], value):
                raise ValueError(f"Invalid date precision: {resource['id']}")
            date.fromisoformat(value + {"year": "-01-01", "month": "-01", "day": ""}[precision])
    for name in ["resource_agent", "resource_format", "resource_topic", "resource_audience", "identifier"]:
        for row in tables[name]:
            if mention_map[row["source_mention_id"]]["resource_id"] != row["resource_id"]:
                raise ValueError(f"Mismatched provenance in {name}")
    for relation in tables["resource_relation"]:
        for side in ("from", "to"):
            if mention_map[relation[f"{side}_mention_id"]]["resource_id"] != relation[f"{side}_resource_id"]:
                raise ValueError("Mismatched relation evidence")


def profile(tables: dict) -> dict:
    url_resources = {r["resource_id"] for r in tables["identifier"] if r["identifier_kind"] == "url"}
    known_dates = sum(r["publication_value"] is not None for r in tables["resource"])
    topic_counts = Counter(r["topic_id"] for r in tables["resource_topic"])
    return {"source_pages": 5, "resource_mentions": len(tables["source_mention"]),
            "catalog_records": len(tables["resource"]),
            "mentions_by_source_category": dict(Counter(m["source_category"] for m in tables["source_mention"])),
            "records_by_proposed_format": dict(Counter(r["format_id"] for r in tables["resource_format"])),
            "resources_with_url": len(url_resources),
            "resources_with_doi": sum(r["identifier_kind"] == "doi" for r in tables["identifier"]),
            "publication_date_known": known_dates, "publication_date_unknown": len(tables["resource"]) - known_dates,
            "all_citations_externally_unverified": True,
            "issues_by_code": dict(Counter(r["issue_code"] for r in tables["quality_issue"])),
            "proposed_topic_counts": dict(topic_counts),
            "topics_without_tagged_resources": [t["id"] for t in tables["topic"] if not topic_counts[t["id"]]],
            "note": "Coverage is based on provisional citation tags, not full-text content review or a performance benchmark."}


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
