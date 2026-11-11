// Run one query at a time in Neo4j Browser. Both endpoints and sources are visible.
// Q19-Q24, Q46: actual subject-predicate-object triples and supporting passages.
MATCH (s:DiabetesConcept)-[:SUBJECT_OF]->(a:DiabetesAssertion)-[:OBJECT]->(o:DiabetesConcept),
      (a)-[:SUPPORTED_BY]->(c:DiabetesEvidence)<-[:HAS_CHUNK]-(source:DiabetesSource)
RETURN s.id AS subject, a.predicate AS predicate, o.id AS object,
       a.release AS release, a.supporting_quote AS quote, c.section AS section, source.url AS source
ORDER BY subject, predicate, object;

// Graph view: select the Graph result tab in Browser.
MATCH p=(s:DiabetesConcept)-[:SUBJECT_OF]->(a:DiabetesAssertion)-[:SUPPORTED_BY]->(c:DiabetesEvidence)
RETURN p LIMIT 50;

// Multi-hop provenance: concept -> assertion -> passage <- source.
MATCH p=(:DiabetesConcept {id:'type2'})-[:SUBJECT_OF]->(:DiabetesAssertion)-[:SUPPORTED_BY]->(:DiabetesEvidence)<-[:HAS_CHUNK]-(:DiabetesSource)
RETURN p LIMIT 25;

// Counts by release, keeping historical releases distinct.
MATCH (c:DiabetesEvidence)
RETURN c.release AS release, count(c) AS passages, count(DISTINCT c.source_id) AS sources;

// Assertions lacking a source passage should return zero rows.
MATCH (a:DiabetesAssertion)
WHERE NOT EXISTS { MATCH (a)-[:SUPPORTED_BY]->(:DiabetesEvidence) }
RETURN a.id AS unsupported_assertion;
