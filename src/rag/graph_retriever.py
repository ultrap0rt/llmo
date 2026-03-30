from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import PromptTemplate
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OLLAMA_BASE_URL, OLLAMA_MODEL

graph = None
llm = None

entity_extraction_template = """
Extract all key entities (people, places, concepts, objects) from the following text. 
Return only a comma-separated list of entities. 
If no entities are found, return "None".

Text: {text}
Entities:
"""
entity_chain = None

try:
    # Configure Neo4j connection
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USER,
        password=NEO4J_PASSWORD
    )

    # LLM for entity extraction from user queries
    llm = ChatOpenAI(
        api_key="ollama",
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0
    )

    entity_prompt = PromptTemplate(
        template=entity_extraction_template,
        input_variables=["text"]
    )
    entity_chain = entity_prompt | llm
except Exception as e:
    print(f"[graph_retriever] Init failed: {e}")

def retrieve_graph_context(query: str) -> str:
    """
    Extract entities from query and retrieve their 1-hop neighborhood from Neo4j.
    Returns formatted context string.
    """
    if not graph or not entity_chain:
        return ""

    try:
        response = entity_chain.invoke({"text": query})
        entities_text = response.content.strip()
        
        if not entities_text or entities_text.lower() == "none":
            return ""
            
        entities = [e.strip() for e in entities_text.split(',')]
        
        context = []
        for entity in entities:
            # Query 1-hop neighborhood
            # LLMGraphTransformer uses 'id' property as the main label for entities
            cypher = """
            MATCH (n)-[r]-(m) 
            WHERE toLower(n.id) CONTAINS toLower($entity) 
            RETURN n.id AS source, type(r) AS relation, m.id AS target
            LIMIT 15
            """
            
            result = graph.query(cypher, params={"entity": entity})
            for record in result:
                context.append(f"{record['source']} [{record['relation']}] {record['target']}")
                
        if context:
            # unique records
            context = list(set(context))
            return "Knowledge Graph Context:\n- " + "\n- ".join(context)
            
        return ""
    except Exception as e:
        print(f"Error retrieving graph context: {e}")
        return ""
