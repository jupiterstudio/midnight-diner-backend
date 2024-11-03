import os
import logging
import uuid
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Import the text splitter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Ingestor:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME")
        self.qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"))
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)  # Set chunk size and overlap
        self._setup_collection()

    def _setup_collection(self):
        # Create or access collection
        try:
            self.qdrant_client.get_collection(self.collection_name)
            logging.info(f"Using existing collection: {self.collection_name}")
        except:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logging.info(f"Created new collection: {self.collection_name}")

    def ingest_all_pdfs(self):
        if not os.path.exists(self.folder_path):
          logging.error(f"PDF folder '{self.folder_path}' does not exist.")
          return
        # Traverse the folder and process all PDFs
        pdf_files = [f for f in os.listdir(self.folder_path) if f.endswith(".pdf")]
        logging.info(f"Found {len(pdf_files)} PDF files in folder: {self.folder_path}")
        
        for filename in pdf_files:
            file_path = os.path.join(self.folder_path, filename)
            logging.info(f"Starting ingestion for file: {filename}")
            self._process_pdf(file_path)
            logging.info(f"Finished ingestion for file: {filename}")

    def _process_pdf(self, pdf_path):
        try:
            # Load PDF and split into chunks
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()
            logging.info(f"Loaded {len(documents)} pages from {pdf_path}")

            # Process each page
            for idx, doc in enumerate(documents):
                content = doc.page_content

                # Split content into chunks using the text splitter
                chunks = self.text_splitter.split_text(content)
                logging.info(f"Split page {idx} into {len(chunks)} chunks")

                # Embed and store each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    embedding = self.embedding_model.embed_query(chunk)

                    # Create a unique point ID for each document chunk
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={"source": pdf_path, "page": idx, "chunk": chunk_idx}
                    )

                    # Insert embedding into Qdrant
                    self.qdrant_client.upsert(collection_name=self.collection_name, points=[point])
                    logging.info(f"Stored embedding for chunk {chunk_idx} of page {idx} in Qdrant")

            logging.info(f"Ingestion completed for {pdf_path}")

        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")

# Usage
current_dir = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(current_dir, "data")
ingestor = Ingestor(folder_path)
ingestor.ingest_all_pdfs()
