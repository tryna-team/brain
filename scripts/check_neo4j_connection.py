from app.graph.neo4j_client import neo4j_client

neo4j_client.connect()
neo4j_client.verify_connectivity()

records, summary, keys = neo4j_client.driver.execute_query(
    "RETURN 'Hello tryna' AS message"
)

print(records[0]["message"])
neo4j_client.close()
