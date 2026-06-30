from neo4j import GraphDatabase
from app.config import settings

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = settings.NEO4J_URI
AUTH = (settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

    records, summary, keys = driver.execute_query(
        "RETURN 'Hello tryna' AS message"
    )

    print(records[0]["message"])