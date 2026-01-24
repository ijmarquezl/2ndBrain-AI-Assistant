from langchain_community.vectorstores import SupabaseVectorStore
from typing import Any, List, Dict, Optional, Tuple, Union
from langchain_core.documents import Document
from supabase.client import Client
import numpy as np

class SupabaseVectorStoreSpanish(SupabaseVectorStore):
    """
    Subclass of SupabaseVectorStore to use 'contenido' instead of 'content'
    as the column name for document text.
    """

    @staticmethod
    def _add_vectors(
        client: Client,
        table_name: str,
        vectors: List[List[float]],
        documents: List[Document],
        ids: List[str],
        chunk_size: int,
        **kwargs: Any,
    ) -> List[str]:
        """Add vectors to Supabase table (Override: uses 'contenido')."""

        rows: List[Dict[str, Any]] = [
            {
                "id": ids[idx],
                "contenido": documents[idx].page_content, # CHANGED FROM content
                "embedding": embedding,
                "metadata": documents[idx].metadata,
                **kwargs,
            }
            for idx, embedding in enumerate(vectors)
        ]
        
        id_list: List[str] = []
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]

            result = client.from_(table_name).upsert(chunk).execute()

            if len(result.data) == 0:
                raise Exception("Error inserting: No rows added")

            ids = [str(i.get("id")) for i in result.data if i.get("id")]
            id_list.extend(ids)

        return id_list

    def similarity_search_by_vector_with_relevance_scores(
        self,
        query: List[float],
        k: int,
        filter: Optional[Dict[str, Any]] = None,
        postgrest_filter: Optional[str] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Tuple[Document, float]]:
        """Override to read from 'contenido' and fix params issue."""
        
        # Manually construct match_documents_params including match_count (k)
        # This avoids using query_builder.params which fails on newer supabase versions
        match_documents_params = dict(
            query_embedding=query, 
            match_count=k,
            match_threshold=score_threshold if score_threshold is not None else 0.0
        )
        if filter:
            match_documents_params["filter"] = filter
        
        # Note: We ignore postgrest_filter manipulation for now to avoid the .params crash
        # If needed, filter logic should be moved inside the SQL function or applied on results
        
        query_builder = self._client.rpc(self.query_name, match_documents_params)

        res = query_builder.execute()

        match_result = [
            (
                Document(
                    metadata=search.get("metadata", {}),
                    page_content=search.get("contenido", "") or search.get("content", ""),
                ),
                search.get("similitud", 0.0) if search.get("similitud") is not None else search.get("similarity", 0.0),
            )
            for search in res.data
            if search.get("contenido") or search.get("content")
        ]

        if score_threshold is not None:
            match_result = [
                (doc, similarity)
                for doc, similarity in match_result
                if similarity >= score_threshold
            ]

        return match_result
