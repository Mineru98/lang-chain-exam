from typing import Any, Callable, Dict, List, Optional

import requests
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain_elasticsearch.vectorstores import (
    ElasticsearchStore,
    _hits_to_docs_scores,
)


class CustomElasticSearchStore(ElasticsearchStore):
    def custom_script_query(self, query_body: dict, query: str):
        query_vector = query_body["knn"]["query_vector"]
        _filter = query_body["knn"]["filter"]
        must_clauses = []

        # metadata가 있을 경우 추가한다.
        if _filter:
            for key, value in _filter.items():
                must_clauses.append({"match": {f"metadata.{key}.keyword": f"{value}"}})
        else:
            must_clauses.append({"match_all": {}})

        return {
            "query": {
                "script_score": {
                    "query": {
                        "bool": {"must": must_clauses},
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                        "params": {"query_vector": query_vector},
                    },
                }
            }
        }

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 50,
        filter: Optional[List[dict]] = None,
        *,
        custom_query: Optional[
            Callable[[Dict[str, Any], Optional[str]], Dict[str, Any]]
        ] = None,
        doc_builder: Optional[Callable[[Dict], Document]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        hits = self._store.search(
            query=query,
            k=k,
            num_candidates=fetch_k,
            filter=filter,
            custom_query=self.custom_script_query,
        )
        docs = _hits_to_docs_scores(
            hits=hits,
            content_field=self.query_field,
        )
        return [doc for doc, _score in docs]


class OllamaEmbeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "bge-m3",
        server_url: str = "http://127.0.0.1:11434",
    ):
        self.model_name = model_name
        self.server_url = server_url

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        url = f"{self.server_url}/api/embeddings"
        for text in texts:
            payload = {
                "model": self.model_name,
                "prompt": text,
            }
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                embeddings.append(data.get("embedding"))
            else:
                raise Exception(
                    f"임베딩 가져오기 실패: {response.status_code}, {response.text}"
                )
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        url = f"{self.server_url}/api/embeddings"
        payload = {"model": self.model_name, "prompt": text}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding")
            return embedding
        else:
            raise Exception(
                f"임베딩 가져오기 실패: {response.status_code}, {response.text}"
            )


class VectorStore:
    def __init__(
        self,
        index_name: str,
        embedding: Embeddings,
        es_url: str,
        es_user: str,
        es_password: str,
    ):
        self.index_name = index_name
        self.embedding = embedding
        self.es_url = es_url
        self.es_user = es_user
        self.es_password = es_password
        self.vector_store = CustomElasticSearchStore(
            index_name=self.index_name,
            embedding=self.embedding,
            es_url=self.es_url,
            es_user=self.es_user,
            es_password=self.es_password,
        )

    def save(self):
        text_list = [
            "Galaxy S9의 특징은 저렴하다는 것이다",
            "Galaxy S9의 배터리는 3000 mAh이다",
            "Galaxy S10의 카메라는 Triple rear cameras이다. ",
            "Galaxy S20의 Display는 6.2-inch Dynamic AMOLED이다.",
            "Galaxy S20의 저장공간은 128G이다",
            "Galaxy S21의 Ram은 8GB이다",
        ]

        for text in text_list:
            doc = [Document(page_content=text)]
            self.vector_store.add_documents(doc, add_to_docstore=True)

    def search(self, query: str):
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 1})
        vector_result = retriever.invoke(query)
        print(vector_result)


store = VectorStore(
    index_name="test",
    embedding=OllamaEmbeddings(),
    es_url="http://localhost:9200",
    es_user="elastic",
    es_password="test1234!#",
)
store.search("Galaxy S9의 특징은 저렴하다는 것이다")
