from neo4j import Driver, Record
from typing import List, Dict, Any

class RuleHubRepo:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def find_rules_by_activity(self, activity_code: str) -> List[Dict[str, Any]]:
        """
        새로운 M1 온톨로지 스키마(3-Hop)를 기반으로 추천 룰과 액션을 조회합니다.
        AI 팀은 LLM을 통해 추출한 activity_code를 이 메서드에 넘겨주기만 하면 됩니다.

        경로: (Activity) <-[:APPLIES_TO]- (PreparationRule) -[:SUGGESTS]-> (Action)
        """
        query = """
        MATCH (act:Activity {code: $activity_code})
        MATCH (rule:PreparationRule)-[:APPLIES_TO]->(act)
        WHERE rule.status = 'APPROVED'
        
        MATCH (rule)-[:SUGGESTS]->(action:Action)
        OPTIONAL MATCH (rule)-[:TARGETS]->(item:Item)
        
        RETURN 
            rule.code AS ruleCode,
            rule.reminderPhase AS reminderPhase,
            rule.importance AS importance,
            action.name AS actionName,
            item.name AS itemName
        """

        records, _, _ = self._driver.execute_query(
            query,
            activity_code=activity_code
        )

        return [
            {
                "ruleCode": record["ruleCode"],
                "action": record["actionName"],
                "targetItem": record["itemName"],
                "reminderPhase": record["reminderPhase"],
                "importance": record["importance"]
            }
            for record in records
        ]