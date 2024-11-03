import os
import logging
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Retriever:
    def __init__(self):
        # Read collection name from environment variable
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME")
        if not self.collection_name:
            raise ValueError("QDRANT_COLLECTION_NAME environment variable is not set.")

        # Initialize Qdrant client and embeddings model
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Initialize Qdrant retriever with LangChain
        self.vectorstore = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.embedding_model
        )
        
    def get_retriever(self, top_k=5):
        """
        Returns a retriever object that can be used to retrieve relevant documents.
        
        Args:
            top_k (int): The number of top documents to retrieve.
        
        Returns:
            A configured retriever object.
        """
        return self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": top_k, "score_threshold": 0.6},
        )

    def retrieve(self, query, top_k=5):
        """
        Retrieves the top_k most relevant documents for a given query.
        
        Args:
            query (str): The user query.
            top_k (int): The number of top documents to retrieve.
        
        Returns:
            List[Document]: A list of retrieved documents with metadata.
        """
        logging.info(f"Retrieving documents for query: {query}")
        
        # Perform retrieval
        retriever = self.get_retriever(top_k)
        relevant_docs = retriever.invoke(query)
        
        # Log and return results
        for i, doc in enumerate(relevant_docs):
            logging.info(f"Result {i+1}: {doc.page_content} (Metadata: {doc.metadata})")
        return relevant_docs

# # Usage
# retriever = Retriever()
# query = "You are asking for guidance on effective strategies or techniques to manage and cope with feelings of stress in a healthy manner."
# retrieved_docs = retriever.retrieve(query, top_k=5)

# # Display retrieved document contents
# for doc in retrieved_docs:
#     print(doc.page_content)
