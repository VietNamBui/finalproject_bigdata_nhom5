import os
import numpy as np
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from sentence_transformers import CrossEncoder
from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.core import PromptHelper
import nltk
import logging
import chardet
from tqdm import tqdm

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tải punkt_tab
nltk.download('punkt_tab', quiet=True)

# Kiểm tra vector index
def check_vector_index(client, db_name, collection_name, index_name):
    try:
        indexes = client[db_name][collection_name].list_search_indexes()
        for idx in indexes:
            if idx["name"] == index_name:
                logger.info(f"Vector index {index_name} exists: {idx}")
                return True
        logger.warning(f"Vector index {index_name} not found")
        return False
    except Exception as e:
        logger.error(f"Error checking index: {str(e)}", exc_info=True)
        return False

# Kiểm tra text index
def check_text_index(client, db_name, collection_name):
    try:
        indexes = client[db_name][collection_name].list_indexes()
        for idx in indexes:
            if idx.get("key", {}).get("text") == "text":
                logger.info("Text index exists")
                return True
        logger.warning("Text index not found")
        return False
    except Exception as e:
        logger.error(f"Error checking text index: {str(e)}", exc_info=True)
        return False

# Kiểm tra dữ liệu đầu vào
def inspect_documents(data_dir):
    files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    logger.info(f"Found {len(files)} files: {files}")
    valid_files = []
    for filename in files:
        file_path = os.path.join(data_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    logger.warning(f"File {filename} is empty")
                    continue
                logger.info(f"File: {filename}, Length: {len(content)}, Sample: {content[:200]}")
                valid_files.append(filename)
        except UnicodeDecodeError as e:
            logger.error(f"UnicodeDecodeError in {filename}: {str(e)}")
            try:
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result["encoding"] or "windows-1252"
                    logger.info(f"Detected encoding for {filename}: {encoding}")
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Converted {filename} to UTF-8")
                valid_files.append(filename)
            except Exception as e2:
                logger.error(f"Failed to read or convert {filename}: {str(e2)}")
    return valid_files

# Hàm tạo hoặc tải vector store
def create_or_load_vector_store(data_dir="backend/data/documents_cleaned", model_name="gemini-embedding", api_key=None):
    logger.info("Starting create_or_load_vector_store")

    # Kiểm tra api_key
    if not api_key:
        logger.error("API key is missing")
        return None
    
    # Cấu hình Gemini và SentenceSplitter
    logger.info("Configuring GoogleGenAIEmbedding...")
    try:
        Settings.embed_model = GoogleGenAIEmbedding(api_key=api_key, model_name="models/embedding-001")
    except Exception as e:
        logger.error(f"Failed to initialize GoogleGenAIEmbedding: {str(e)}", exc_info=True)
        return None
    
    # Cấu hình Gemini và SentenceSplitter
    Settings.llm = None
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    Settings.prompt_helper = PromptHelper(
        context_window=4096,
        num_output=256,
        chunk_overlap_ratio=0.1,
        chunk_size_limit=1024
    )
    logger.info("GoogleGenAIEmbedding and SentenceSplitter configured with chunk_size=1024, chunk_overlap=100")

    # Test Gemini API
    logger.info("Testing Gemini API...")
    try:
        emb_model = GoogleGenAIEmbedding(api_key=api_key, model_name="models/embedding-001")
        test_embedding = emb_model.get_text_embedding("Test sentence")
        logger.info(f"Test embedding length: {len(test_embedding)}, Sample: {test_embedding[:10]}")
    except Exception as e:
        logger.error(f"Gemini API test failed: {str(e)}", exc_info=True)
        return None

    # Kết nối MongoDB Atlas
    mongo_uri = "mongodb+srv://donggiangdoo:lEbpZCaVlhktFWQa@cluster0.pnd9a8y.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=120000, socketTimeoutMS=120000)
    try:
        client.admin.command('ping')
        logger.info("MongoDB connection successful")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}", exc_info=True)
        return None

    db = client['rag_database']
    collection = db['chunks']
    logger.info("Connected to MongoDB Atlas")

    # Xóa collection để bắt đầu lại
    logger.info("Dropping collection chunks to ensure fresh data")
    collection.drop()
    logger.info("Collection chunks dropped")

    # Tạo vector store
    vector_store = MongoDBAtlasVectorSearch(
        mongodb_client=client,
        db_name="rag_database",
        collection_name="chunks",
        vector_index_name="vector_index",
        embedding_key="embedding"
    )
    logger.info("Vector store initialized")

    # Kiểm tra hoặc tạo vector index
    if not check_vector_index(client, "rag_database", "chunks", "vector_index"):
        logger.info("Creating vector search index...")
        try:
            vector_store.create_vector_search_index(
                dimensions=768, path="embedding", similarity="cosine"
            )
            logger.info("Vector search index created")
        except Exception as e:
            logger.error(f"Error creating vector index: {str(e)}", exc_info=True)
            return None

    # Kiểm tra text index
    if not check_text_index(client, "rag_database", "chunks"):
        logger.info("Creating text index...")
        try:
            collection.create_index([("text", "text")])
            logger.info("Text index created")
        except Exception as e:
            logger.error(f"Error creating text index: {str(e)}", exc_info=True)

    # Kiểm tra file trong data_dir
    files = inspect_documents(data_dir)
    if not files:
        logger.error(f"No valid .txt files found in {data_dir}")
        return None
    logger.info(f"Found {len(files)} valid .txt files")

    # Tải tài liệu
    documents = []
    for file_path in [os.path.join(data_dir, f) for f in files]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                logger.warning(f"File {file_path} is empty")
                continue
            doc = Document(text=content, metadata={"filename": file_path, "source": "document"})
            documents.append(doc)
            logger.info(f"Loaded document: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {str(e)}", exc_info=True)
            continue
    logger.info(f"Loaded {len(documents)} documents")
    logger.info(f"Sample document: {documents[0].text[:200] if documents else 'No documents'}")

    # Tạo storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    logger.info("Storage context created")

    # Tạo index từ tài liệu
    try:
        logger.info("Creating index from documents...")
        logger.info(f"Number of documents: {len(documents)}")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        logger.info("Index created successfully")
        
        # Kiểm tra collection sau khi lưu
        doc_count = collection.count_documents({})
        logger.info(f"Số lượng document trong collection: {doc_count}")
        sample_doc = collection.find_one()
        logger.info(f"Sample document in MongoDB: {sample_doc}")
        return index
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}", exc_info=True)
        return None

# Hàm tìm kiếm tài liệu tương tự
def search_similar_docs(question: str, index, top_k=5):
    if index is None:
        logger.error("Vector store not initialized.")
        return []

    # Vector search
    try:
        vector_query_engine = index.as_query_engine(similarity_top_k=top_k)
        vector_response = vector_query_engine.query(question)
        vector_contexts = [node.text for node in vector_response.source_nodes]
        logger.info(f"Vector search retrieved {len(vector_contexts)} contexts")
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}", exc_info=True)
        vector_contexts = []

    # Text search
    client = MongoClient(
        "mongodb+srv://donggiangdoo:lEbpZCaVlhktFWQa@cluster0.pnd9a8y.mongodb.net/?retryWrites=true&w=majority",
        serverSelectionTimeoutMS=120000,
        socketTimeoutMS=120000
    )
    collection = client['rag_database']['chunks']
    text_contexts = []
    try:
        text_results = collection.find({"$text": {"$search": question}}, {"text": 1}).limit(top_k * 2)
        text_contexts = [doc['text'] for doc in text_results]
        logger.info(f"Text search retrieved {len(text_contexts)} contexts")
    except Exception as e:
        logger.error(f"Error in text search: {str(e)}", exc_info=True)
        text_contexts = []

    # Kết hợp và loại trùng
    contexts = list(set(vector_contexts + text_contexts))[:top_k * 2]

    # Reranking
    if contexts:
        try:
            cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            pairs = [[question, context] for context in contexts]
            scores = cross_encoder.predict(pairs)
            ranked_contexts = [context for _, context in sorted(zip(scores, contexts), reverse=True)][:top_k]
            logger.info(f"Reranked to {len(ranked_contexts)} contexts")
        except Exception as e:
            logger.error(f"Error in reranking: {str(e)}", exc_info=True)
            ranked_contexts = contexts[:top_k]
    else:
        ranked_contexts = []

    logger.info(f"Question: {question}")
    for i, context in enumerate(ranked_contexts):
        logger.info(f"Context {i+1}: {context[:200]}...")
    return ranked_contexts