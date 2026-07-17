from app.graph.neo4j_client import neo4j_client
from app.graph.repositories.recommendation_repo import RecommendationRepo


def main() -> None:
    neo4j_client.connect()
    neo4j_client.verify_connectivity()

    repository = RecommendationRepo(
        driver=neo4j_client.driver,
    )

    candidates = repository.find_candidates(
        event_type="meeting",
        contexts=[],
        place_type=None,
        limit=12,
    )

    print(f"조회 후보 수: {len(candidates)}")

    for candidate in candidates:
        print(candidate)


if __name__ == "__main__":
    try:
        main()
    finally:
        neo4j_client.close()