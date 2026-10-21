"""Create MySQL and SQLite tables from the same design."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    name: str
    definition: str
    primary_key: tuple[str, ...]


TABLES = [
    Table("source_document", """
        id VARCHAR(64) PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        sha256 CHAR(64) NOT NULL UNIQUE,
        text_sha256 CHAR(64) NOT NULL,
        page_count INT NOT NULL CHECK (page_count > 0),
        ingested_on DATE NOT NULL
    """, ("id",)),
    Table("resource", """
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(1024) NOT NULL,
        publication_value VARCHAR(10),
        publication_precision VARCHAR(16) NOT NULL,
        container_title TEXT,
        publisher_statement TEXT,
        citation_text TEXT NOT NULL,
        verification_status VARCHAR(32) NOT NULL CHECK (verification_status IN ('unverified', 'verified', 'rejected')),
        CONSTRAINT ck_publication_precision CHECK (
            (publication_precision = 'unknown' AND publication_value IS NULL) OR
            (publication_precision = 'year' AND publication_value IS NOT NULL AND LENGTH(publication_value) = 4) OR
            (publication_precision = 'month' AND publication_value IS NOT NULL AND LENGTH(publication_value) = 7) OR
            (publication_precision = 'day' AND publication_value IS NOT NULL AND LENGTH(publication_value) = 10)
        )
    """, ("id",)),
    Table("source_mention", """
        id VARCHAR(64) PRIMARY KEY,
        resource_id VARCHAR(64) NOT NULL,
        source_id VARCHAR(64) NOT NULL,
        source_category VARCHAR(64) NOT NULL,
        source_position INT NOT NULL CHECK (source_position > 0),
        page_start INT NOT NULL CHECK (page_start > 0),
        page_end INT NOT NULL CHECK (page_end >= page_start),
        citation_raw TEXT NOT NULL,
        retrieved_on DATE,
        UNIQUE (source_id, source_category, source_position),
        UNIQUE (id, resource_id),
        FOREIGN KEY (resource_id) REFERENCES resource(id),
        FOREIGN KEY (source_id) REFERENCES source_document(id)
    """, ("id",)),
    Table("agent", """
        id VARCHAR(64) PRIMARY KEY,
        name VARCHAR(512) NOT NULL,
        agent_kind VARCHAR(32) NOT NULL CHECK (agent_kind IN ('person', 'organization')),
        identity_status VARCHAR(64) NOT NULL
    """, ("id",)),
    Table("format", """
        id VARCHAR(64) PRIMARY KEY,
        name VARCHAR(128) NOT NULL UNIQUE
    """, ("id",)),
    Table("topic", """
        id VARCHAR(64) PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        source_id VARCHAR(64) NOT NULL,
        source_page INT NOT NULL CHECK (source_page > 0),
        basis VARCHAR(64) NOT NULL,
        FOREIGN KEY (source_id) REFERENCES source_document(id)
    """, ("id",)),
    Table("audience", """
        id VARCHAR(64) PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        source_id VARCHAR(64) NOT NULL,
        source_page INT NOT NULL CHECK (source_page > 0),
        FOREIGN KEY (source_id) REFERENCES source_document(id)
    """, ("id",)),
    Table("resource_agent", """
        resource_id VARCHAR(64) NOT NULL,
        agent_id VARCHAR(64) NOT NULL,
        contribution_role VARCHAR(32) NOT NULL CHECK (contribution_role IN ('creator', 'publisher')),
        credit_order INT NOT NULL CHECK (credit_order > 0),
        source_mention_id VARCHAR(64) NOT NULL,
        PRIMARY KEY (resource_id, contribution_role, credit_order),
        UNIQUE (resource_id, agent_id, contribution_role),
        FOREIGN KEY (resource_id) REFERENCES resource(id),
        FOREIGN KEY (agent_id) REFERENCES agent(id),
        FOREIGN KEY (source_mention_id, resource_id) REFERENCES source_mention(id, resource_id)
    """, ("resource_id", "contribution_role", "credit_order")),
    Table("resource_format", """
        resource_id VARCHAR(64) NOT NULL,
        format_id VARCHAR(64) NOT NULL,
        source_mention_id VARCHAR(64) NOT NULL,
        basis VARCHAR(64) NOT NULL,
        PRIMARY KEY (resource_id, format_id),
        FOREIGN KEY (resource_id) REFERENCES resource(id),
        FOREIGN KEY (format_id) REFERENCES format(id),
        FOREIGN KEY (source_mention_id, resource_id) REFERENCES source_mention(id, resource_id)
    """, ("resource_id", "format_id")),
    Table("resource_topic", """
        resource_id VARCHAR(64) NOT NULL,
        topic_id VARCHAR(64) NOT NULL,
        source_mention_id VARCHAR(64) NOT NULL,
        basis VARCHAR(64) NOT NULL,
        review_status VARCHAR(32) NOT NULL CHECK (review_status IN ('proposed', 'approved', 'rejected')),
        PRIMARY KEY (resource_id, topic_id),
        FOREIGN KEY (resource_id) REFERENCES resource(id),
        FOREIGN KEY (topic_id) REFERENCES topic(id),
        FOREIGN KEY (source_mention_id, resource_id) REFERENCES source_mention(id, resource_id)
    """, ("resource_id", "topic_id")),
    Table("resource_audience", """
        resource_id VARCHAR(64) NOT NULL,
        audience_id VARCHAR(64) NOT NULL,
        source_mention_id VARCHAR(64) NOT NULL,
        basis VARCHAR(64) NOT NULL,
        review_status VARCHAR(32) NOT NULL CHECK (review_status IN ('proposed', 'approved', 'rejected')),
        PRIMARY KEY (resource_id, audience_id),
        FOREIGN KEY (resource_id) REFERENCES resource(id),
        FOREIGN KEY (audience_id) REFERENCES audience(id),
        FOREIGN KEY (source_mention_id, resource_id) REFERENCES source_mention(id, resource_id)
    """, ("resource_id", "audience_id")),
    Table("identifier", """
        id VARCHAR(64) PRIMARY KEY,
        resource_id VARCHAR(64) NOT NULL,
        identifier_kind VARCHAR(16) NOT NULL CHECK (identifier_kind IN ('url', 'doi', 'phone')),
        identifier_value VARCHAR(700) NOT NULL,
        source_mention_id VARCHAR(64) NOT NULL,
        UNIQUE (identifier_kind, identifier_value),
        FOREIGN KEY (resource_id) REFERENCES resource(id),
        FOREIGN KEY (source_mention_id, resource_id) REFERENCES source_mention(id, resource_id)
    """, ("id",)),
    Table("quality_issue", """
        id VARCHAR(64) PRIMARY KEY,
        mention_id VARCHAR(64) NOT NULL,
        issue_code VARCHAR(64) NOT NULL,
        detail TEXT NOT NULL,
        review_status VARCHAR(32) NOT NULL CHECK (review_status IN ('open', 'resolved', 'dismissed')),
        FOREIGN KEY (mention_id) REFERENCES source_mention(id)
    """, ("id",)),
    Table("resource_relation", """
        id VARCHAR(64) PRIMARY KEY,
        from_resource_id VARCHAR(64) NOT NULL,
        to_resource_id VARCHAR(64) NOT NULL,
        relation_kind VARCHAR(64) NOT NULL CHECK (relation_kind IN ('possible_same_work', 'describes_service')),
        evidence TEXT NOT NULL,
        review_status VARCHAR(32) NOT NULL CHECK (review_status IN ('proposed', 'approved', 'rejected')),
        from_mention_id VARCHAR(64) NOT NULL,
        to_mention_id VARCHAR(64) NOT NULL,
        UNIQUE (from_resource_id, to_resource_id, relation_kind),
        CHECK (from_resource_id <> to_resource_id),
        FOREIGN KEY (from_resource_id) REFERENCES resource(id),
        FOREIGN KEY (to_resource_id) REFERENCES resource(id),
        FOREIGN KEY (from_mention_id, from_resource_id) REFERENCES source_mention(id, resource_id),
        FOREIGN KEY (to_mention_id, to_resource_id) REFERENCES source_mention(id, resource_id)
    """, ("id",)),
    Table("planning_statement", """
        id VARCHAR(64) PRIMARY KEY,
        source_id VARCHAR(64) NOT NULL,
        statement_kind VARCHAR(64) NOT NULL,
        page_start INT NOT NULL CHECK (page_start > 0),
        page_end INT NOT NULL CHECK (page_end >= page_start),
        statement_text TEXT NOT NULL,
        FOREIGN KEY (source_id) REFERENCES source_document(id)
    """, ("id",)),
    Table("age_definition", """
        id VARCHAR(64) PRIMARY KEY,
        audience_id VARCHAR(64) NOT NULL,
        source_id VARCHAR(64) NOT NULL,
        source_page INT NOT NULL CHECK (source_page > 0),
        minimum_age INT NOT NULL CHECK (minimum_age >= 0 AND minimum_age <= 120),
        comparison_operator VARCHAR(2) NOT NULL CHECK (comparison_operator IN ('>=', '>')),
        evidence TEXT NOT NULL,
        review_status VARCHAR(32) NOT NULL CHECK (review_status IN ('unresolved', 'approved', 'rejected')),
        FOREIGN KEY (audience_id) REFERENCES audience(id),
        FOREIGN KEY (source_id) REFERENCES source_document(id)
    """, ("id",)),
]

INDEXES = [
    ("ix_mentions_resource", "source_mention", "resource_id"),
    ("ix_topic_resource", "resource_topic", "topic_id, resource_id"),
    ("ix_audience_resource", "resource_audience", "audience_id, resource_id"),
    ("ix_format_resource", "resource_format", "format_id, resource_id"),
    ("ix_agent_resource", "resource_agent", "agent_id, resource_id"),
    ("ix_resource_date", "resource", "publication_value"),
    ("ix_issue_queue", "quality_issue", "review_status, issue_code"),
    ("ix_relation_target", "resource_relation", "to_resource_id"),
]


def relational_schema(dialect: str) -> str:
    if dialect not in ("mysql", "sqlite"):
        raise ValueError(dialect)
    header = ("SET NAMES utf8mb4;\n" if dialect == "mysql" else "PRAGMA foreign_keys = ON;\n")
    statements = [header]
    for table in TABLES:
        indexes = [f"INDEX {name} ({columns})" for name, target, columns in INDEXES if target == table.name]
        if dialect == "mysql" and table.name == "resource":
            indexes.append("FULLTEXT INDEX resource_search (title, citation_text)")
        definition = table.definition.strip()
        if dialect == "mysql" and indexes:
            definition += ",\n        " + ",\n        ".join(indexes)
        suffix = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin" if dialect == "mysql" else ""
        statements.append(f"CREATE TABLE IF NOT EXISTS {table.name} (\n        {definition}\n){suffix};")
    if dialect == "sqlite":
        statements.extend(f"CREATE INDEX IF NOT EXISTS {name} ON {target} ({columns});"
                          for name, target, columns in INDEXES)
        statements.append("CREATE VIRTUAL TABLE IF NOT EXISTS resource_fts USING fts5(resource_id UNINDEXED, title, citation_text);")
    return "\n\n".join(statements) + "\n"
