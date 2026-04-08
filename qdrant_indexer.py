from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from typing import List, Dict
import hashlib
import os
import warnings

# Suppress version mismatch warning
warnings.filterwarnings("ignore", message=".*Qdrant client version.*")

class QdrantIndexer:
    def __init__(self, collection_name="repo_code", host="localhost", port=6333, vector_size=768):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name in collections:
                # Check if existing collection has correct vector size
                collection_info = self.client.get_collection(self.collection_name)
                existing_vector_size = collection_info.config.params.vectors.size
                if existing_vector_size != self.vector_size:
                    print(f"[WARNING] Collection has {existing_vector_size}D vectors, expected {self.vector_size}D. Recreating...")
                    self.client.delete_collection(self.collection_name)
                    self.client.recreate_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                    )
                return
            
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )
        except Exception as e:
            print(f"[ERROR] Failed to ensure collection: {e}")
            raise

    def upsert_code_chunks(self, code_chunks: List[Dict]):
        points = []
        for chunk in code_chunks:
            # chunk: {"file_path":..., "commit_hash":..., "chunk_id":..., "text":..., "embedding":...}
            point_id = self._make_point_id(chunk)
            points.append(PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload={
                    "file_path": chunk["file_path"],
                    "commit_hash": chunk["commit_hash"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"]
                }
            ))
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def delete_file(self, file_path: str):
        self.client.delete(collection_name=self.collection_name, filter={"must": [{"key": "file_path", "match": {"value": file_path}}]})

    def _make_point_id(self, chunk: Dict):
        # Unique by file, commit, chunk
        s = f"{chunk['file_path']}:{chunk['commit_hash']}:{chunk['chunk_id']}"
        return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (10 ** 12)

    def search(self, embedding: List[float], top_k=5):
        return self.client.query_points(
            collection_name=self.collection_name, 
            query=embedding, 
            limit=top_k,
            with_payload=True,
            with_vectors=False
        ).points
