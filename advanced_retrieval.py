"""Real vector/hybrid retrieval and model-planned Foundry IQ retrieval."""

from __future__ import annotations

import math
import re
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote, urlparse

from evaluation import digest, read_json, write_json
from foundry_client import deployment_snapshot, validate_history
from rag_client import (
    DOCUMENT_FIELDS, SEMANTIC_CONFIG, definition_matches, index_definition,
    knowledge_source_definition, normalize_documents, validate_rag_config,
)

API_VERSION = "2026-08-01-preview"
VECTOR_FIELD = "content_vector"
BASE_KEYS = {"search_endpoint", "index_name", "knowledge_source", "knowledge_base", "top_k"}
EXTRA_KEYS = {
    "model_resource_endpoint", "embedding_deployment", "embedding_model",
    "embedding_dimensions", "planner_deployment", "planner_model", "retrieval_reasoning_effort",
}


def read_config(path: Path) -> dict:
    value = read_json(path)
    if not isinstance(value, dict) or set(value) != BASE_KEYS | EXTRA_KEYS:
        raise ValueError("Use the fields in advanced-rag/config.example.json.")
    base = validate_rag_config({key: value[key] for key in BASE_KEYS})
    if not isinstance(value["model_resource_endpoint"], str):
        raise ValueError("model_resource_endpoint must be a URL string.")
    endpoint = urlparse(value["model_resource_endpoint"])
    if (
        endpoint.scheme != "https" or not endpoint.hostname
        or not endpoint.hostname.endswith(".openai.azure.com")
        or endpoint.path not in ("", "/") or endpoint.query or endpoint.fragment
        or endpoint.username or endpoint.password or endpoint.port not in (None, 443)
        or "YOUR-" in value["model_resource_endpoint"]
    ):
        raise ValueError("Use the actual Azure OpenAI resource endpoint.")
    if value["embedding_model"] != "text-embedding-3-small" or value["embedding_dimensions"] != 1536:
        raise ValueError("This versioned lab requires text-embedding-3-small with 1536 dimensions.")
    if value["planner_model"] != "gpt-5.4-mini" or value["retrieval_reasoning_effort"] != "low":
        raise ValueError("This versioned lab requires the supported gpt-5.4-mini planner with low effort.")
    for key in ("embedding_deployment", "planner_deployment"):
        if not isinstance(value[key], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", value[key]):
            raise ValueError(f"Invalid {key}.")
    return {**value, **base, "model_resource_endpoint": value["model_resource_endpoint"].rstrip("/")}


@contextmanager
def embedding_client(config: dict):
    from azure.identity import AzureCliCredential, get_bearer_token_provider
    from openai import APIError, OpenAI
    try:
        with AzureCliCredential(process_timeout=30) as credential:
            token = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
            with OpenAI(
                base_url=config["model_resource_endpoint"] + "/openai/v1/",
                api_key=token, timeout=60, max_retries=0,
            ) as client:
                yield client
    except APIError as exc:
        raise RuntimeError(f"Embedding endpoint request failed ({type(exc).__name__}): {exc}") from exc


def validate_vector(vector, dimensions: int) -> None:
    if (
        not isinstance(vector, list) or len(vector) != dimensions
        or any(type(value) not in (int, float) or not math.isfinite(value) for value in vector)
        or not any(value != 0 for value in vector)
    ):
        raise ValueError("Embedding vectors must be finite, nonzero, and match the index dimensions.")


def embed(client, config: dict, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=config["embedding_deployment"], input=texts,
        dimensions=config["embedding_dimensions"], encoding_format="float",
    )
    entries = sorted(response.data, key=lambda item: item.index)
    if [entry.index for entry in entries] != list(range(len(texts))):
        raise ValueError("Embedding response indices are incomplete.")
    vectors = [entry.embedding for entry in entries]
    for vector in vectors:
        validate_vector(vector, config["embedding_dimensions"])
    return vectors


def model_contract(project, config: dict) -> dict:
    embedding = deployment_snapshot(project, config["embedding_deployment"])
    planner = deployment_snapshot(project, config["planner_deployment"])
    if embedding["model_name"] != config["embedding_model"] or planner["model_name"] != config["planner_model"]:
        raise ValueError("The deployed embedding/planning models differ from the advanced configuration.")
    return {"embedding": embedding, "planner": planner, "dimensions": config["embedding_dimensions"]}


def vector_index(config: dict, corpus_hash: str, models: dict) -> dict:
    definition = index_definition(config, corpus_hash)
    definition["description"] = "Advanced vector RAG contract=" + digest({
        "corpus": corpus_hash, "models": models, "version": "advanced-vector-v1",
    })
    definition["fields"].append({
        "name": VECTOR_FIELD, "type": "Collection(Edm.Single)",
        "searchable": True, "retrievable": False, "stored": False,
        "dimensions": config["embedding_dimensions"], "vectorSearchProfile": "vector-profile",
    })
    definition["vectorSearch"] = {
        "algorithms": [{
            "name": "vector-hnsw", "kind": "hnsw",
            "hnswParameters": {"metric": "cosine", "m": 4, "efConstruction": 400, "efSearch": 100},
        }],
        "profiles": [{"name": "vector-profile", "algorithm": "vector-hnsw", "vectorizer": "model-vectorizer"}],
        "vectorizers": [{
            "name": "model-vectorizer", "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": config["model_resource_endpoint"],
                "deploymentId": config["embedding_deployment"],
                "modelName": config["embedding_model"],
            },
        }],
    }
    return definition


def planned_base(config: dict) -> dict:
    return {
        "name": config["knowledge_base"],
        "description": "Official travel policy. Use real travel dates and scope/missing-information sources.",
        "knowledgeSources": [{"name": config["knowledge_source"]}],
        "models": [{
            "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": config["model_resource_endpoint"],
                "deploymentId": config["planner_deployment"],
                "modelName": config["planner_model"],
            },
        }],
        "retrievalReasoningEffort": {"kind": "low"},
        "outputMode": "extractiveData",
        "retrievalInstructions": (
            "Search official travel-policy evidence relevant to the user's actual question. "
            "Preserve actual travel dates separately from claim dates. "
            "For missing travel dates or overseas limits, include the appropriate scope policy. "
            "Do not invent missing dates or approval facts when formulating searches."
        ),
    }


def definition_hashes(setup: dict) -> dict:
    return {
        name: digest({key: value for key, value in setup[name].items() if not key.startswith("@")})
        for name in ("index", "knowledge_source", "knowledge_base")
    }


def verify_definitions(search, config: dict, expected: dict) -> None:
    actual = {
        "index": search.request("GET", f"indexes/{config['index_name']}"),
        "knowledge_source": search.request("GET", f"knowledgesources/{config['knowledge_source']}"),
        "knowledge_base": search.request("GET", f"knowledgebases/{config['knowledge_base']}"),
    }
    if definition_hashes(actual) != expected:
        raise ValueError("Live index/knowledge definitions changed after the experiment was frozen.")


def initialize(search, project, client, config: dict, documents: list[dict], cache_path: Path) -> dict:
    corpus_hash = digest(documents)
    models = model_contract(project, config)
    path = "indexes/" + quote(config["index_name"], safe="")
    source_path = "knowledgesources/" + quote(config["knowledge_source"], safe="")
    base_path = "knowledgebases/" + quote(config["knowledge_base"], safe="")
    definitions = {
        "index": (path, vector_index(config, corpus_hash, models)),
        "knowledge source": (source_path, knowledge_source_definition(config)),
        "knowledge base": (base_path, planned_base(config)),
    }
    existing = {}
    for kind, (resource_path, definition) in definitions.items():
        existing[kind] = search.request("GET", resource_path, missing_ok=True)
        if existing[kind] is not None and not definition_matches(existing[kind], definition):
            raise ValueError(f"Existing {kind} has a different retrieval/model contract. Use new object names; do not overwrite it.")
    embedding_contract = digest({"documents": documents, "models": models["embedding"], "dimensions": config["embedding_dimensions"]})
    if cache_path.exists():
        cache = read_json(cache_path)
        if cache["contract_hash"] != embedding_contract:
            raise ValueError("Embedding cache belongs to another corpus/model. Use a new cache path.")
        vectors = cache["vectors"]
        if len(vectors) != len(documents):
            raise ValueError("Embedding cache is incomplete.")
        for vector in vectors:
            validate_vector(vector, config["embedding_dimensions"])
    else:
        vectors = embed(client, config, [document["title"] + "\n" + document["content"] for document in documents])
        write_json(cache_path, {"contract_hash": embedding_contract, "models": models, "vectors": vectors})
    if existing["index"] is None:
        search.request("PUT", path, definitions["index"][1], create_only=True)
    inventory = search.request("POST", path + "/docs/search", {
        "search": "*", "select": ",".join(DOCUMENT_FIELDS), "top": 100,
    })["value"]
    expected = {document["id"]: {**document, "corpus_hash": corpus_hash} for document in documents}
    for item in inventory:
        if item["id"] not in expected or any(item.get(key) != value for key, value in expected[item["id"]].items()):
            raise ValueError("Indexed text differs from the intended corpus.")
    if len(inventory) != len(documents):
        response = search.request("POST", path + "/docs/index", {
            "value": [
                {"@search.action": "upload", **expected[document["id"]], VECTOR_FIELD: vector}
                for document, vector in zip(documents, vectors)
            ],
        })
        values = response.get("value", [])
        if len(values) != len(documents) or any(value.get("status") is not True for value in values):
            raise RuntimeError(f"Vector document upload failed: {values}")
    for kind in ("knowledge source", "knowledge base"):
        if existing[kind] is None:
            resource_path, definition = definitions[kind]
            search.request("PUT", resource_path, definition, create_only=True)
    return {
        "api_version": API_VERSION, "corpus_hash": corpus_hash, "models": models,
        "vector_dimensions": config["embedding_dimensions"], "document_count": len(documents),
        "embedding_contract_hash": embedding_contract,
        "index": search.request("GET", path), "index_stats": search.request("GET", path + "/stats"),
        "knowledge_source": search.request("GET", source_path),
        "knowledge_base": search.request("GET", base_path),
    }


def retrieve(search, client, config: dict, query: str, corpus_hash: str, *, mode="planned", history=None) -> dict:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A nonempty retrieval query is required.")
    filter_text = f"approved eq true and corpus_hash eq '{corpus_hash}'"
    started = time.monotonic()
    if mode in ("hybrid", "vector"):
        vector = embed(client, config, [query])[0]
        body = {
            "vectorQueries": [{"kind": "vector", "vector": vector, "fields": VECTOR_FIELD, "k": 50}],
            "filter": filter_text, "select": ",".join(DOCUMENT_FIELDS), "top": 50,
        }
        if mode == "hybrid":
            body.update({"search": query, "queryType": "semantic", "semanticConfiguration": SEMANTIC_CONFIG})
        raw = search.request("POST", f"indexes/{quote(config['index_name'], safe='')}/docs/search", body)
        documents = normalize_documents(raw, "search", corpus_hash, config["top_k"])
        evidence = {"query_vector_dimensions": len(vector), "vector_fields": VECTOR_FIELD, "text_query": mode == "hybrid"}
    elif mode == "planned":
        messages = [
            {"role": turn["role"], "content": [{"type": "text", "text": turn["content"]}]}
            for turn in validate_history(history)
        ] + [{"role": "user", "content": [{"type": "text", "text": query}]}]
        raw = search.request("POST", f"knowledgebases/{quote(config['knowledge_base'], safe='')}/retrieve", {
            "messages": messages,
            "retrievalReasoningEffort": {"kind": "low"}, "outputMode": "extractiveData",
            "includeActivity": True, "maxRuntimeInSeconds": 60,
            "knowledgeSourceParams": [{
                "knowledgeSourceName": config["knowledge_source"], "kind": "searchIndex",
                "filterAddOn": filter_text, "includeReferences": True,
                "includeReferenceSourceData": True, "rerankerThreshold": 0.0,
            }],
        })
        activity = raw.get("activity", [])
        if not any(item.get("type") == "modelQueryPlanning" for item in activity):
            raise RuntimeError("No LLM query-planning activity was returned; do not label this as planned retrieval.")
        documents = normalize_documents(raw, "iq", corpus_hash, config["top_k"])
        evidence = {
            "llm_query_planning": True,
            "planned_queries": [
                item.get("searchIndexArguments", {}).get("search")
                for item in activity if item.get("type") == "searchIndex"
            ],
            "activity_types": [item.get("type") for item in activity],
        }
    else:
        raise ValueError("Choose vector, hybrid, or planned retrieval.")
    return {
        "mode": mode, "query": query, "api_version": API_VERSION,
        "documents": documents, "raw_response": raw, "evidence": evidence,
        "latency_ms": round((time.monotonic() - started) * 1000, 2),
    }
