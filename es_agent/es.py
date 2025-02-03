from pprint import pprint
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
            },
            "_source": {"includes": ["_score"]},
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
        pprint(docs)
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
            {
                "company_name": "삼성전자",
                "sentences": [
                    "삼성전자는 반도체, 스마트폰, 가전제품 분야에서 세계적인 기업입니다.",
                    "삼성전자는 글로벌 시장에서의 강력한 경쟁력을 바탕으로 높은 매출과 이익을 창출합니다.",
                    "특히, 반도체 부문은 삼성전자의 핵심 성장 동력으로 꼽히며, 5G와 AI 기술 개발에도 앞장서고 있습니다.",
                ],
            },
            {
                "company_name": "LG화학",
                "sentences": [
                    "LG화학은 배터리와 석유화학 분야에서 글로벌 리더로 자리매김하고 있습니다.",
                    "전기차 배터리 부문에서 혁신적인 기술을 바탕으로 성장하고 있으며, 친환경 소재 개발에도 적극적으로 투자하고 있습니다.",
                    "LG화학은 지속 가능한 경영과 탄소 중립 실현을 목표로 하는 기업입니다.",
                ],
            },
            {
                "company_name": "네이버",
                "sentences": [
                    "네이버는 대한민국을 대표하는 인터넷 서비스 기업으로, 검색엔진과 포털 사이트를 운영합니다.",
                    "최근에는 인공지능, 클라우드, 콘텐츠 플랫폼 등 다양한 분야로 사업을 확장하고 있습니다.",
                    "네이버는 라인(LINE)과 같은 글로벌 메신저 플랫폼을 통해 해외에서도 높은 인지도를 가지고 있습니다.",
                ],
            },
            {
                "company_name": "카카오",
                "sentences": [
                    "카카오는 모바일 메신저 '카카오톡'을 통해 대한민국의 대표적인 IT 기업으로 성장했습니다.",
                    "모바일 결제, 게임, 금융, 엔터테인먼트 등 다양한 분야로 사업을 확장하여, 디지털 플랫폼 기업으로의 위상을 높이고 있습니다.",
                    "카카오는 최근 블록체인, AI, 모빌리티 등의 혁신 기술에도 적극적으로 투자하고 있습니다.",
                ],
            },
            {
                "company_name": "포스코",
                "sentences": [
                    "포스코는 세계적인 철강 기업으로, 고품질 철강재를 생산하며 다양한 산업에 공급하고 있습니다.",
                    "글로벌 시장에서 경쟁력을 유지하기 위해 신소재 개발과 기술 혁신에 힘쓰고 있습니다.",
                    "포스코는 지속 가능한 발전을 위한 친환경 경영을 추진하고 있으며, 수소 사업에도 진출하고 있습니다.",
                ],
            },
        ]

        for text in text_list:
            for sentence in text["sentences"]:
                doc = [
                    Document(
                        page_content=sentence,
                        metadata={
                            "company_name": text["company_name"],
                            "sentences": sentence,
                        },
                    )
                ]
                self.vector_store.add_documents(doc, add_to_docstore=True)

    def search(self, query: str):
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5, "score_threshold": 0.8}
        )
        vector_result = retriever.invoke(query)
        print(vector_result)


store = VectorStore(
    index_name="test",
    embedding=OllamaEmbeddings(),
    es_url="http://localhost:9200",
    es_user="elastic",
    es_password="test1234!#",
)
# store.save()
store.search("반도체")
