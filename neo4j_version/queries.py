"""Matched research questions, with explicit meanings and an independent JSON oracle."""
from collections import Counter


def item(id, question, columns, sql, cypher, interpretation, parameters=None):
    return dict(id=id, question=question, columns=columns.split(), mysql=sql.strip(), neo4j=cypher.strip(),
                interpretation=interpretation, parameters=parameters or {})


FILTER_SQL = """
SELECT DISTINCT r.id, r.title FROM resource r
JOIN resource_topic t ON t.resource_id=r.id
JOIN resource_format f ON f.resource_id=r.id
JOIN resource_audience a ON a.resource_id=r.id
WHERE t.topic_id='phishing' AND f.format_id='video' AND a.audience_id='older_adults'
AND t.review_status <> 'rejected' AND a.review_status <> 'rejected'
"""
FILTER_CYPHER = """
MATCH (r:Resource)-[:HAS_TOPIC_ASSIGNMENT]->(t:TopicAssignment)-[:ASSIGNS_TOPIC]->(:Topic {id:'phishing'}),
(r)-[:HAS_FORMAT_ASSIGNMENT]->(:FormatAssignment)-[:ASSIGNS_FORMAT]->(:Format {id:'video'}),
(r)-[:HAS_AUDIENCE_ASSIGNMENT]->(a:AudienceAssignment)-[:ASSIGNS_AUDIENCE]->(:Audience {id:'older_adults'})
WHERE t.review_status <> 'rejected' AND a.review_status <> 'rejected'
RETURN DISTINCT r.id AS id, r.title AS title
"""

QUERIES = [
item("Q01", "How many resources and original mentions are stored?", "resources mentions",
     "SELECT (SELECT COUNT(*) FROM resource) AS resources,(SELECT COUNT(*) FROM source_mention) AS mentions",
     "MATCH (r:Resource) WITH count(r) AS resources MATCH (m:Mention) RETURN resources,count(m) AS mentions",
     "Distinct resources and citation occurrences are different counting units."),
item("Q02", "How many resources credit the FBI as creator or publisher?", "role resources",
     """SELECT 'creator' AS role,COUNT(DISTINCT ra.resource_id) AS resources FROM resource_agent ra JOIN agent a ON a.id=ra.agent_id
        WHERE a.name='Federal Bureau of Investigation' AND ra.contribution_role='creator'
        UNION ALL SELECT 'publisher' AS role,COUNT(DISTINCT ra.resource_id) AS resources FROM resource_agent ra JOIN agent a ON a.id=ra.agent_id
        WHERE a.name='Federal Bureau of Investigation' AND ra.contribution_role='publisher'""",
     """UNWIND ['creator','publisher'] AS role
        OPTIONAL MATCH (r:Resource)-[:HAS_CONTRIBUTION]->(c:Contribution)-[:CREDITS_AGENT]->(:Agent {name:'Federal Bureau of Investigation'})
        WHERE c.contribution_role=role RETURN role,count(DISTINCT r) AS resources""",
     "Credit role is explicit. A zero publisher count does not establish that the FBI published no relevant material."),
item("Q03", "Which resources contain phishing in the title or citation?", "id title",
     "SELECT id,title FROM resource WHERE LOCATE('phishing',LOWER(CONCAT(title,' ',citation_text)))>0",
     "MATCH (r:Resource) WHERE toLower(r.title+' '+r.citation_text) CONTAINS 'phishing' RETURN r.id AS id,r.title AS title",
     "Case-insensitive substring matching on metadata only. Each resource is counted once."),
item("Q04", "Which suggested phishing videos are tagged for older adults?", "id title", FILTER_SQL, FILTER_CYPHER,
     "Curator view includes proposed and approved assignments, following the baseline query policy."),
item("Q05", "Which resources share a suggested topic with r034?", "id shared_topics",
     """SELECT b.resource_id AS id,COUNT(DISTINCT a.topic_id) AS shared_topics
        FROM resource_topic a JOIN resource_topic b ON b.topic_id=a.topic_id
        WHERE a.resource_id='r034' AND b.resource_id<>a.resource_id
        AND a.review_status<>'rejected' AND b.review_status<>'rejected' GROUP BY b.resource_id""",
     """MATCH (:Resource {id:'r034'})-[:HAS_TOPIC_ASSIGNMENT]->(a:TopicAssignment)-[:ASSIGNS_TOPIC]->(t:Topic)
        <-[:ASSIGNS_TOPIC]-(b:TopicAssignment)<-[:HAS_TOPIC_ASSIGNMENT]-(r:Resource)
        WHERE r.id<>'r034' AND a.review_status<>'rejected' AND b.review_status<>'rejected'
        RETURN r.id AS id,count(DISTINCT t) AS shared_topics""",
     "Shared provisional tags establish catalog connections, not resource quality or user suitability."),
item("Q06", "How many resources are tagged with each topic, including zero counts?", "id resources",
     """SELECT t.id,COUNT(DISTINCT a.resource_id) AS resources FROM topic t
        LEFT JOIN resource_topic a ON a.topic_id=t.id AND a.review_status<>'rejected' GROUP BY t.id""",
     """MATCH (t:Topic) OPTIONAL MATCH (r:Resource)-[:HAS_TOPIC_ASSIGNMENT]->(a:TopicAssignment)-[:ASSIGNS_TOPIC]->(t)
        WHERE a.review_status<>'rejected' RETURN t.id AS id,count(DISTINCT r) AS resources""",
     "Zero means no assigned tag in this snapshot. General resources may still cover the topic."),
item("Q07", "What original citations support r022?", "id category page_start page_end retrieved_on citation_raw",
     "SELECT id,source_category AS category,page_start,page_end,retrieved_on,citation_raw FROM source_mention WHERE resource_id='r022'",
     """MATCH (m:Mention)-[:REFERS_TO]->(:Resource {id:'r022'})
        RETURN m.id AS id,m.source_category AS category,m.page_start AS page_start,m.page_end AS page_end,
        m.retrieved_on AS retrieved_on,m.citation_raw AS citation_raw""",
     "Both original mentions and their different access dates remain available."),
item("Q08", "Which citation problems remain open?", "id resource_id issue_code",
     "SELECT q.id,m.resource_id,q.issue_code FROM quality_issue q JOIN source_mention m ON m.id=q.mention_id WHERE q.review_status='open'",
     """MATCH (q:QualityIssue)<-[:HAS_ISSUE]-(m:Mention)-[:REFERS_TO]->(r:Resource)
        WHERE q.review_status='open' RETURN q.id AS id,r.id AS resource_id,q.issue_code AS issue_code""",
     "Issue rows are counted separately from resources; one resource can have several issues."),
item("Q09", "Which possible duplicate pairs need review?", "id from_id to_id status evidence",
     "SELECT id,from_resource_id AS from_id,to_resource_id AS to_id,review_status AS status,evidence FROM resource_relation WHERE relation_kind='possible_same_work'",
     """MATCH (a:Resource)-[:HAS_RESOURCE_LINK]->(x:ResourceLink)-[:TARGETS_RESOURCE]->(b:Resource)
        WHERE x.relation_kind='possible_same_work'
        RETURN x.id AS id,a.id AS from_id,b.id AS to_id,x.review_status AS status,x.evidence AS evidence""",
     "Possible duplicates remain separate records. The query makes no automatic merge."),
item("Q10", "What is the current verification status of the resources?", "status resources",
     """SELECT 'unverified' AS status,COUNT(*) AS resources FROM resource WHERE verification_status='unverified'
        UNION ALL SELECT 'verified',COUNT(*) FROM resource WHERE verification_status='verified'
        UNION ALL SELECT 'rejected',COUNT(*) FROM resource WHERE verification_status='rejected'""",
     """UNWIND ['unverified','verified','rejected'] AS status
        OPTIONAL MATCH (r:Resource) WHERE r.verification_status=status RETURN status,count(r) AS resources""",
     "Current status does not identify the reviewer or review date."),
item("Q11", "Which phishing videos meet an example approved-only policy?", "id title",
     FILTER_SQL.replace("t.review_status <> 'rejected' AND a.review_status <> 'rejected'", "t.review_status='approved' AND a.review_status='approved' AND r.verification_status='verified'"),
     FILTER_CYPHER.replace("t.review_status <> 'rejected' AND a.review_status <> 'rejected'", "t.review_status='approved' AND a.review_status='approved' AND r.verification_status='verified'"),
     "Illustrative public filter requires a verified resource plus approved topic and audience tags. This is a proposed policy, not a completed review."),
item("Q12", "What citation evidence supports the shared-topic link from r034?", "id topic seed_mention candidate_mention",
     """SELECT b.resource_id AS id,a.topic_id AS topic,ma.id AS seed_mention,mb.id AS candidate_mention
        FROM resource_topic a JOIN resource_topic b ON a.topic_id=b.topic_id
        JOIN source_mention ma ON ma.id=a.source_mention_id AND ma.resource_id=a.resource_id
        JOIN source_mention mb ON mb.id=b.source_mention_id AND mb.resource_id=b.resource_id
        WHERE a.resource_id='r034' AND b.resource_id<>'r034' AND a.review_status<>'rejected' AND b.review_status<>'rejected'""",
     """MATCH (:Resource {id:'r034'})-[:HAS_TOPIC_ASSIGNMENT]->(a:TopicAssignment)-[:ASSIGNS_TOPIC]->(t:Topic)
        <-[:ASSIGNS_TOPIC]-(b:TopicAssignment)<-[:HAS_TOPIC_ASSIGNMENT]-(r:Resource),
        (a)-[:EVIDENCED_BY]->(ma:Mention),(b)-[:EVIDENCED_BY]->(mb:Mention)
        WHERE r.id<>'r034' AND a.review_status<>'rejected' AND b.review_status<>'rejected'
        RETURN r.id AS id,t.id AS topic,ma.id AS seed_mention,mb.id AS candidate_mention""",
     "Evidence nodes make the path traceable. Topic labels are still inferred from citations."),
item("Q13", "Does r003 retain the original creator order?", "name credit_order",
     "SELECT a.name,c.credit_order FROM resource_agent c JOIN agent a ON a.id=c.agent_id WHERE c.resource_id='r003' AND c.contribution_role='creator'",
     """MATCH (:Resource {id:'r003'})-[:HAS_CONTRIBUTION]->(c:Contribution)-[:CREDITS_AGENT]->(a:Agent)
        WHERE c.contribution_role='creator' RETURN a.name AS name,c.credit_order AS credit_order""",
     "The contributor order is a stored property and must be explicitly sorted for display."),
item("Q14", "Which resources have a supplied telephone identifier?", "id phone",
     "SELECT resource_id AS id,identifier_value AS phone FROM identifier WHERE identifier_kind='phone'",
     """MATCH (r:Resource)-[:HAS_IDENTIFIER]->(i:Identifier) WHERE i.identifier_kind='phone'
        RETURN r.id AS id,i.identifier_value AS phone""",
     "This number identifies a listed assistance service. It is not a suspected scam-caller number."),
]


def oracle(data):
    resources = {r["id"]: r for r in data["resource"]}
    agents = {r["id"]: r for r in data["agent"]}
    mentions = {r["id"]: r for r in data["source_mention"]}
    tags = [r for r in data["resource_topic"] if r["review_status"] != "rejected"]
    audiences = [r for r in data["resource_audience"] if r["review_status"] != "rejected"]
    videos = {r["resource_id"] for r in data["resource_format"] if r["format_id"] == "video"}
    phishing = {r["resource_id"] for r in tags if r["topic_id"] == "phishing"}
    older = {r["resource_id"] for r in audiences if r["audience_id"] == "older_adults"}
    seed = [r for r in tags if r["resource_id"] == "r034"]
    seed_topics = {r["topic_id"] for r in seed}
    common = {}
    for row in tags:
        if row["resource_id"] != "r034" and row["topic_id"] in seed_topics:
            common.setdefault(row["resource_id"], set()).add(row["topic_id"])
    def titles(ids):
        return [{"id": rid, "title": resources[rid]["title"]} for rid in sorted(ids)]
    approved_phishing = {r["resource_id"] for r in tags if r["topic_id"] == "phishing" and r["review_status"] == "approved"}
    approved_older = {r["resource_id"] for r in audiences if r["audience_id"] == "older_adults" and r["review_status"] == "approved"}
    verified = {r["id"] for r in data["resource"] if r["verification_status"] == "verified"}
    return {
        "Q01": [{"resources": len(resources), "mentions": len(mentions)}],
        "Q02": [{"role": role, "resources": len({r["resource_id"] for r in data["resource_agent"]
                  if agents[r["agent_id"]]["name"] == "Federal Bureau of Investigation" and r["contribution_role"] == role})}
                 for role in ["creator", "publisher"]],
        "Q03": titles({r["id"] for r in resources.values() if "phishing" in (r["title"] + " " + r["citation_text"]).lower()}),
        "Q04": titles(videos & phishing & older),
        "Q05": [{"id": rid, "shared_topics": len(topics)} for rid, topics in common.items()],
        "Q06": [{"id": topic["id"], "resources": len({r["resource_id"] for r in tags if r["topic_id"] == topic["id"]})} for topic in data["topic"]],
        "Q07": [{"id": m["id"], "category": m["source_category"], "page_start": m["page_start"], "page_end": m["page_end"],
                  "retrieved_on": m["retrieved_on"], "citation_raw": m["citation_raw"]} for m in mentions.values() if m["resource_id"] == "r022"],
        "Q08": [{"id": q["id"], "resource_id": mentions[q["mention_id"]]["resource_id"], "issue_code": q["issue_code"]}
                 for q in data["quality_issue"] if q["review_status"] == "open"],
        "Q09": [{"id": r["id"], "from_id": r["from_resource_id"], "to_id": r["to_resource_id"], "status": r["review_status"], "evidence": r["evidence"]}
                 for r in data["resource_relation"] if r["relation_kind"] == "possible_same_work"],
        "Q10": [{"status": status, "resources": sum(r["verification_status"] == status for r in resources.values())}
                 for status in ["unverified", "verified", "rejected"]],
        "Q11": titles(videos & approved_phishing & approved_older & verified),
        "Q12": [{"id": b["resource_id"], "topic": a["topic_id"], "seed_mention": a["source_mention_id"], "candidate_mention": b["source_mention_id"]}
                 for a in seed for b in tags if b["topic_id"] == a["topic_id"] and b["resource_id"] != "r034"],
        "Q13": [{"name": agents[c["agent_id"]]["name"], "credit_order": c["credit_order"]}
                 for c in data["resource_agent"] if c["resource_id"] == "r003" and c["contribution_role"] == "creator"],
        "Q14": [{"id": i["resource_id"], "phone": i["identifier_value"]} for i in data["identifier"] if i["identifier_kind"] == "phone"],
    }
