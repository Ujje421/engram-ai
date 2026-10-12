"""
Engram — FalkorDB Feature Verification Script
Tests Cypher syntax compatibility against a live FalkorDB instance.

Run: python tests/verify_falkordb_features.py
"""

import os
import sys
import time

def test_falkordb_compatibility():
    try:
        from falkordb import FalkorDB
    except ImportError:
        print("❌ FalkorDB python client not installed.")
        print("   Install it via: pip install falkordb")
        return False

    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", 6379))
    print(f"Connecting to FalkorDB at {host}:{port}...")

    try:
        db = FalkorDB(host=host, port=port)
    except Exception as e:
        print(f"❌ Failed to connect to FalkorDB: {e}")
        print("   Ensure Docker is running and: docker-compose up -d")
        return False

    graph_name = "test_falkordb_syntax"
    graph = db.select_graph(graph_name)

    results = {}
    print("\nStarting Cypher Syntax Compatibility Tests...")

    # Clean up previous run if any
    try:
        graph.delete()
        graph = db.select_graph(graph_name)
    except Exception:
        pass

    # Test 1: Node creation with integer sentinel and properties
    try:
        res = graph.query("""
            CREATE (f:Fact {
                id: 'fact-test-01',
                tx_to: 9999999999,
                status: 'verified',
                confidence: 0.95
            })
            RETURN f.id AS id
        """)
        assert len(res.result_set) == 1
        results["Node creation with sentinel (tx_to = 9999999999)"] = True
    except Exception as e:
        results["Node creation with sentinel (tx_to = 9999999999)"] = f"Failed: {e}"

    # Test 2: Equality match on sentinel
    try:
        res = graph.query("""
            MATCH (f:Fact)
            WHERE f.tx_to = 9999999999 AND f.status = 'verified'
            RETURN f.id AS id
        """)
        assert len(res.result_set) == 1
        results["WHERE clause with integer sentinel equality"] = True
    except Exception as e:
        results["WHERE clause with integer sentinel equality"] = f"Failed: {e}"

    # Test 3: Parameterized queries
    try:
        res = graph.query("""
            MATCH (f:Fact {id: $fid})
            RETURN f.confidence AS conf
        """, {"fid": "fact-test-01"})
        assert len(res.result_set) == 1
        results["Parameterized query with dictionary params"] = True
    except Exception as e:
        results["Parameterized query with dictionary params"] = f"Failed: {e}"

    # Test 4: Relationship creation and OPTIONAL MATCH
    try:
        graph.query("""
            MATCH (f:Fact {id: 'fact-test-01'})
            CREATE (e:Entity {id: 'ent-01', name: 'Service A'})
            CREATE (f)-[:SUBJECT]->(e)
        """)
        res = graph.query("""
            MATCH (f:Fact {id: 'fact-test-01'})
            OPTIONAL MATCH (f)-[:SUBJECT]->(e:Entity)
            OPTIONAL MATCH (f)-[:DERIVED_FROM]->(s:Source)
            RETURN f.id, e.name, s.uri
        """)
        row = res.result_set[0]
        assert row[1] == "Service A"
        assert row[2] is None  # s.uri should be None due to OPTIONAL MATCH
        results["OPTIONAL MATCH with NULL result"] = True
    except Exception as e:
        results["OPTIONAL MATCH with NULL result"] = f"Failed: {e}"

    # Test 5: Variable-length paths (*1..3)
    try:
        graph.query("""
            CREATE (a:Service {id: 'svc-1'})
            CREATE (b:Service {id: 'svc-2'})
            CREATE (c:Service {id: 'svc-3'})
            CREATE (a)-[:DEPENDS_ON]->(b)
            CREATE (b)-[:DEPENDS_ON]->(c)
        """)
        res = graph.query("""
            MATCH (start:Service {id: 'svc-1'})-[:DEPENDS_ON*1..3]->(target:Service)
            RETURN target.id AS tid
        """)
        target_ids = {row[0] for row in res.result_set}
        assert "svc-2" in target_ids and "svc-3" in target_ids
        results["Variable-length path traversal (*1..3)"] = True
    except Exception as e:
        results["Variable-length path traversal (*1..3)"] = f"Failed: {e}"

    # Test 6: Aggregation (collect and count)
    try:
        res = graph.query("""
            MATCH (s:Service)
            RETURN count(s) AS total, collect(s.id) AS ids
        """)
        row = res.result_set[0]
        assert row[0] == 3
        results["Aggregations (count, collect)"] = True
    except Exception as e:
        results["Aggregations (count, collect)"] = f"Failed: {e}"

    # Test 7: Edge deletion without deleting node
    try:
        graph.query("""
            MATCH (a:Service {id: 'svc-1'})-[r:DEPENDS_ON]->(b:Service {id: 'svc-2'})
            DELETE r
        """)
        res = graph.query("""
            MATCH (a:Service {id: 'svc-1'})-[:DEPENDS_ON]->(b:Service)
            RETURN b.id
        """)
        assert len(res.result_set) == 0
        res_nodes = graph.query("""
            MATCH (a:Service {id: 'svc-1'}) RETURN a.id
        """)
        assert len(res_nodes.result_set) == 1
        results["Edge deletion preserving nodes (Counterfactual Test)"] = True
    except Exception as e:
        results["Edge deletion preserving nodes (Counterfactual Test)"] = f"Failed: {e}"

    # Cleanup
    try:
        graph.delete()
        results["Graph cleanup (graph.delete())"] = True
    except Exception as e:
        results["Graph cleanup (graph.delete())"] = f"Failed: {e}"

    # Summary
    print("\n" + "=" * 60)
    print("FalkorDB Feature Verification Summary")
    print("=" * 60)
    all_passed = True
    for feature, status in results.items():
        if status is True:
            print(f"  ✅  {feature}")
        else:
            print(f"  ❌  {feature} -> {status}")
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 ALL FALKORDB CYPHER FEATURES VERIFIED COMPATIBLE!")
    else:
        print("⚠️ Some features had issues. Review errors above.")
    return all_passed

if __name__ == "__main__":
    test_falkordb_compatibility()
