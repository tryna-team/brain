from neo4j import GraphDatabase # neo4j 접속을 위한 Python 공식 라이브러리
from app.core.config import settings

URI = settings.neo4j_uri
AUTH = (settings.neo4j_username, settings.neo4j_password)

driver = GraphDatabase.driver(URI, auth=AUTH)

summary = driver.execute_query(
    """
    CREATE (e:EventType {name: $event})
    CREATE (r:RecommendationTemplate {name: $recommendation})
    CREATE (e)-[:RECOMMENDS]->(r)
    """,
    event="팀플 회의",
    recommendation="회의 안건 확인"
).summary

print(f"Created {summary.counters.nodes_created} nodes")
print(f"Created {summary.counters.relationships_created} relationships")

driver.close()