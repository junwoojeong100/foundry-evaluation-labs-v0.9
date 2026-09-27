"""Keyless Azure AI Search and Foundry IQ REST operations for the optional lab."""

from __future__ import annotations

import json
import math
import re
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote, urlparse

from evaluation import digest, read_json

SEARCH_API_VERSION = "2026-04-01"
SEMANTIC_CONFIG = "travel-semantic"
DOCUMENT_FIELDS = ("id", "source_id", "title", "content", "approved", "corpus_hash")
IQ_OUTPUT_TOKENS = 6000


def read_rag_config(path: Path) -> dict:
    config = read_json(path)
    keys = {"search_endpoint", "index_name", "knowledge_source", "knowledge_base", "top_k"}
    if not isinstance(config, dict) or set(config) != keys:
        raise ValueError("Use the five fields in optional-rag/config.example.json.")
    if not isinstance(config["search_endpoint"], str):
        raise ValueError("search_endpoint must be a URL string.")
    endpoint = urlparse(config["search_endpoint"])
    if (
        endpoint.scheme != "https" or not endpoint.hostname
        or not endpoint.hostname.endswith(".search.windows.net")
        or endpoint.path not in ("", "/") or endpoint.query or endpoint.fragment
        or endpoint.username or endpoint.password or endpoint.port not in (None, 443)
        or "YOUR-" in config["search_endpoint"]
    ):
        raise ValueError("A real https://SERVICE.search.windows.net endpoint is required.")
    for field in ("index_name", "knowledge_source", "knowledge_base"):
        if not isinstance(config[field], str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", config[field]):
            raise ValueError(f"Invalid {field}; use a dedicated lowercase workshop name.")
    if type(config["top_k"]) is not int or not 1 <= config["top_k"] <= 10:
        raise ValueError("top_k must be an integer from 1 to 10.")
    return {**config, "search_endpoint": config["search_endpoint"].rstrip("/")}


def read_documents(path: Path) -> list[dict]:
    documents = []
    expected = {"id", "source_id", "title", "content", "approved"}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path}:{number}: blank JSONL line.")
        document = json.loads(line)
        if not isinstance(document, dict) or set(document) != expected:
            raise ValueError(f"{path}:{number}: invalid document fields.")
        if type(document["approved"]) is not bool:
            raise ValueError("Document approved must be a boolean.")
        for key in ("id", "source_id", "title", "content"):
            if not isinstance(document[key], str) or not document[key].strip():
                raise ValueError(f"Document {key} must be nonempty text.")
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", document["id"]):
            raise ValueError("Document keys must be lowercase letters, digits and dashes.")
        if document["source_id"] not in ("TRAVEL-CURRENT", "TRAVEL-PREVIOUS", "SCOPE", "FAQ-DRAFT"):
            raise ValueError("Unexpected policy source ID.")
        if document["source_id"] == "FAQ-DRAFT" and document["approved"]:
            raise ValueError("The unapproved draft must not be marked approved.")
        documents.append(document)
    if not documents or len({document["id"] for document in documents}) != len(documents):
        raise ValueError("The corpus must be nonempty with unique chunk IDs.")
    return documents


def index_definition(config: dict, corpus_hash: str) -> dict:
    return {
        "name": config["index_name"],
        "description": f"Foundry evaluation optional RAG; corpus={corpus_hash}",
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "source_id", "type": "Edm.String", "filterable": True},
            {"name": "title", "type": "Edm.String", "searchable": True, "analyzer": "ko.microsoft"},
            {"name": "content", "type": "Edm.String", "searchable": True, "analyzer": "ko.microsoft"},
            {"name": "approved", "type": "Edm.Boolean", "filterable": True},
            {"name": "corpus_hash", "type": "Edm.String", "filterable": True},
        ],
        "semantic": {
            "defaultConfiguration": SEMANTIC_CONFIG,
            "configurations": [{
                "name": SEMANTIC_CONFIG,
                "prioritizedFields": {
                    "titleField": {"fieldName": "title"},
                    "prioritizedContentFields": [{"fieldName": "content"}],
                    "prioritizedKeywordsFields": [],
                },
            }],
        },
    }


def knowledge_source_definition(config: dict) -> dict:
    return {
        "name": config["knowledge_source"], "kind": "searchIndex",
        "description": "Approved fictional travel policy chunks for the optional RAG workshop.",
        "searchIndexParameters": {
            "searchIndexName": config["index_name"],
            "semanticConfigurationName": SEMANTIC_CONFIG,
            "sourceDataFields": [{"name": field} for field in DOCUMENT_FIELDS],
        },
    }


def knowledge_base_definition(config: dict) -> dict:
    return {
        "name": config["knowledge_base"],
        "description": "Foundry IQ: GA minimal extractive retrieval; gpt-6-luna generates answers separately.",
        "knowledgeSources": [{"name": config["knowledge_source"]}],
    }


def retrieval_contract(config: dict, corpus_hash: str) -> dict:
    return {
        "version": "rag-retrieval-v1", "api_version": SEARCH_API_VERSION,
        "semantic_configuration": SEMANTIC_CONFIG,
        "filter": f"approved eq true and corpus_hash eq '{corpus_hash}'",
        "document_fields": list(DOCUMENT_FIELDS), "application_top_k": config["top_k"],
        "iq_profile": "GA minimal extractive", "iq_output_token_limit": IQ_OUTPUT_TOKENS,
        "iq_reranker_threshold": 0.0,
    }


class SearchRestClient:
    def __init__(self, endpoint, pipeline):
        self.endpoint = endpoint
        self.pipeline = pipeline

    def request(self, method: str, path: str, body=None, *, missing_ok=False, create_only=False):
        from azure.core.pipeline.transport import HttpRequest
        request = HttpRequest(
            method, f"{self.endpoint}/{path}?api-version={SEARCH_API_VERSION}",
            headers={"Accept": "application/json"},
        )
        if create_only:
            request.headers["If-None-Match"] = "*"
        if body is not None:
            request.headers["Content-Type"] = "application/json"
            request.set_json_body(body)
        response = self.pipeline.run(request).http_response
        if missing_ok and response.status_code == 404:
            return None
        text = response.text()
        if response.status_code not in (200, 201, 204):
            raise RuntimeError(f"Search {method} {path}: HTTP {response.status_code}: {text[:1000]}")
        payload = json.loads(text) if text else {}
        if not isinstance(payload, dict):
            raise ValueError("Azure Search returned a non-object JSON response.")
        return payload


@contextmanager
def search_client(config: dict):
    from azure.core.exceptions import AzureError
    from azure.core.pipeline import Pipeline
    from azure.core.pipeline.policies import BearerTokenCredentialPolicy
    from azure.core.pipeline.transport import RequestsTransport
    from azure.identity import AzureCliCredential
    try:
        with (
            AzureCliCredential(process_timeout=30) as credential,
            Pipeline(
                transport=RequestsTransport(connection_timeout=15, read_timeout=90),
                policies=[BearerTokenCredentialPolicy(credential, "https://search.azure.com/.default")],
            ) as pipeline,
        ):
            yield SearchRestClient(config["search_endpoint"], pipeline)
    except AzureError as exc:
        raise RuntimeError(f"Azure Search request failed ({type(exc).__name__}): {exc}") from exc


def initialize(client, config: dict, documents: list[dict]) -> dict:
    corpus_hash = digest(documents)
    definition = index_definition(config, corpus_hash)
    index_path = "indexes/" + quote(config["index_name"], safe="")
    existing = client.request("GET", index_path, missing_ok=True)
    if existing is None:
        client.request("PUT", index_path, definition, create_only=True)
    elif existing.get("description") != definition["description"]:
        raise ValueError("This index has a different owner/corpus contract. Choose a new index name; do not overwrite it.")
    else:
        fields = {field["name"]: field["type"] for field in existing["fields"]}
        if fields != {field["name"]: field["type"] for field in definition["fields"]}:
            raise ValueError("Existing index fields differ from the optional workshop schema.")

    indexed = client.request("POST", index_path + "/docs/search", {
        "search": "*", "select": ",".join(DOCUMENT_FIELDS), "top": 100,
    })["value"]
    expected = {document["id"]: {**document, "corpus_hash": corpus_hash} for document in documents}
    for item in indexed:
        if item["id"] not in expected or any(item.get(key) != value for key, value in expected[item["id"]].items()):
            raise ValueError("Existing indexed content differs from the corpus. Preserve it and use a new index.")
    if len(indexed) != len(documents):
        uploaded = client.request("POST", index_path + "/docs/index", {
            "value": [{"@search.action": "upload", **document} for document in expected.values()],
        })
        outcomes = uploaded.get("value", [])
        if (
            len(outcomes) != len(documents)
            or {item.get("key") for item in outcomes} != set(expected)
            or any(item.get("status") is not True for item in outcomes)
        ):
            raise RuntimeError(f"Document upload is incomplete or failed: {outcomes}")

    source = knowledge_source_definition(config)
    source_path = "knowledgesources/" + quote(config["knowledge_source"], safe="")
    existing_source = client.request("GET", source_path, missing_ok=True)
    if existing_source is None:
        client.request("PUT", source_path, source, create_only=True)
    elif existing_source.get("kind") != "searchIndex" or existing_source.get("searchIndexParameters", {}).get("searchIndexName") != config["index_name"]:
        raise ValueError("Knowledge source targets another index; do not overwrite it.")
    base = knowledge_base_definition(config)
    base_path = "knowledgebases/" + quote(config["knowledge_base"], safe="")
    existing_base = client.request("GET", base_path, missing_ok=True)
    if existing_base is None:
        client.request("PUT", base_path, base, create_only=True)
    elif [source["name"] for source in existing_base.get("knowledgeSources", [])] != [config["knowledge_source"]]:
        raise ValueError("Knowledge base has different sources; do not overwrite it.")
    return {
        "api_version": SEARCH_API_VERSION, "corpus_hash": corpus_hash,
        "document_count": len(documents), "index": client.request("GET", index_path),
        "knowledge_source": client.request("GET", source_path),
        "knowledge_base": client.request("GET", base_path),
    }


def normalize_documents(raw: dict, mode: str, corpus_hash: str, top_k: int) -> list[dict]:
    if not isinstance(raw, dict):
        raise ValueError("The retrieval response must be a JSON object.")
    if mode == "search":
        if raw.get("@search.semanticPartialResponseReason"):
            raise RuntimeError("Search returned a partial semantic result; it is not a complete retrieval.")
        values = raw.get("value")
        if not isinstance(values, list) or any(not isinstance(item, dict) for item in values):
            raise ValueError("Search results must contain a document array.")
        entries = [(item, item.get("@search.rerankerScore"), None) for item in values]
    elif mode == "iq":
        activity = raw.get("activity")
        if (
            not isinstance(activity, list) or any(not isinstance(item, dict) for item in activity)
            or not any(item.get("type") == "searchIndex" for item in activity)
        ):
            raise ValueError("Foundry IQ returned no search activity evidence.")
        if any(item.get("error") for item in activity):
            raise RuntimeError("Foundry IQ activity contains an error; do not treat partial retrieval as success.")
        references = raw.get("references")
        if not isinstance(references, list) or any(not isinstance(item, dict) for item in references):
            raise ValueError("Foundry IQ results must contain a reference array.")
        entries = []
        for reference in references:
            document = reference.get("sourceData")
            if reference.get("type") != "searchIndex" or not isinstance(document, dict):
                raise ValueError("Foundry IQ sourceData is missing; include reference source data.")
            if reference.get("docKey") != document.get("id"):
                raise ValueError("IQ document key does not match its source data.")
            entries.append((document, reference.get("rerankerScore"), reference.get("id")))
    else:
        raise ValueError("Retrieval mode must be search or iq.")
    documents, seen = [], set()
    for document, score, reference_id in entries:
        if not all(field in document for field in DOCUMENT_FIELDS):
            raise ValueError("Retrieved document fields are incomplete.")
        if document["approved"] is not True or document["corpus_hash"] != corpus_hash:
            raise ValueError("Retrieval returned an unapproved or different-corpus document.")
        for field in ("id", "source_id", "title", "content"):
            if not isinstance(document[field], str) or not document[field].strip():
                raise ValueError(f"Retrieved {field} must be nonempty text.")
        if document["id"] in seen:
            raise ValueError("Duplicate retrieved chunk IDs are not valid ranking evidence.")
        seen.add(document["id"])
        if score is not None and (type(score) not in (int, float) or not math.isfinite(score)):
            raise ValueError("Invalid reranker score.")
        documents.append({**{key: document[key] for key in DOCUMENT_FIELDS}, "reranker_score": score, "reference_id": reference_id})
    if not documents:
        raise RuntimeError("No evidence was retrieved. The lab does not silently fall back to the full policy.")
    if all(document["reranker_score"] is not None for document in documents):
        documents.sort(key=lambda document: document["reranker_score"], reverse=True)
    return documents[:top_k]


def retrieve(client, config: dict, query: str, mode: str, corpus_hash: str) -> dict:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A nonempty query is required.")
    contract = retrieval_contract(config, corpus_hash)
    filter_text = contract["filter"]
    started = time.monotonic()
    if mode == "search":
        raw = client.request("POST", f"indexes/{quote(config['index_name'], safe='')}/docs/search", {
            "search": query, "queryType": "semantic", "semanticConfiguration": SEMANTIC_CONFIG,
            "filter": filter_text,
            "select": ",".join(DOCUMENT_FIELDS), "top": 50,
        })
    elif mode == "iq":
        raw = client.request("POST", f"knowledgebases/{quote(config['knowledge_base'], safe='')}/retrieve", {
            "intents": [{"type": "semantic", "search": query}],
            "includeActivity": True, "maxRuntimeInSeconds": 60, "maxOutputSizeInTokens": IQ_OUTPUT_TOKENS,
            "knowledgeSourceParams": [{
                "knowledgeSourceName": config["knowledge_source"], "kind": "searchIndex",
                "filterAddOn": filter_text, "includeReferences": True,
                "includeReferenceSourceData": True, "rerankerThreshold": 0.0,
            }],
        })
    else:
        raise ValueError("Retrieval mode must be search or iq.")
    return {
        "mode": mode, "query": query, "api_version": SEARCH_API_VERSION, "contract": contract,
        "documents": normalize_documents(raw, mode, corpus_hash, config["top_k"]),
        "raw_response": raw, "latency_ms": round((time.monotonic() - started) * 1000, 2),
    }


def retrieved_context(result: dict) -> str:
    return "\n\n".join(
        f"source_id: {document['source_id']}\nchunk_id: {document['id']}\n"
        f"title: {document['title']}\n{document['content']}"
        for document in result["documents"]
    )
