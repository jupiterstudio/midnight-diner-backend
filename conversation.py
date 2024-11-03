import os
from dotenv import load_dotenv
import logging
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from retriever import Retriever  # Import the existing Retriever class

from langchain_aws import ChatBedrock


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Conversation:
    def __init__(self):
        # Initialize the Retriever instance
        self.retriever = Retriever()  # This uses the existing Retriever class

        # Initialize the Claude model
        self.llm = ChatAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), model="claude-3-sonnet-20240229")  # Use the Claude model

        # Define prompt templates for question reformulation and answering
        self._setup_prompts()

        # Create history-aware retriever and RAG chain
        self.history_aware_retriever = create_history_aware_retriever(self.llm, self.retriever.get_retriever(), self.contextualize_q_prompt)
        # Chain to combine documents for answering
        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
        
        self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.question_answer_chain)

    def _setup_prompts(self):
        # Contextualize Question Prompt (Therapy Context)
        contextualize_q_template = """You are a supportive and thoughtful therapist assistant. Your task is to rephrase the user’s latest question 
        to make it clear and understandable without prior conversation context. 
        Do NOT answer the question; simply restate it in a compassionate and clear way.

        Chat History:
        {chat_history}

        Latest Question:
        {input}

        Rephrased Question:
        """
        self.contextualize_q_prompt = PromptTemplate(template=contextualize_q_template, input_variables=["chat_history", "input"])
        #===============================================
        # Question-Answering Prompt (Therapy Context)
        qa_template = """You are a compassionate assistant for therapy support. Using the retrieved information, 
        provide a thoughtful and concise response to the user's concern. If the context is incomplete, 
        acknowledge this gently, and encourage the user to share more if they feel comfortable. 
        Keep each response supportive, concise, and empathetic.

        Retrieved Context:
        {context}

        Chat History:
        {chat_history}

        User Question:
        {input}

        Response:
        """

        # Create the PromptTemplate
        self.qa_prompt = PromptTemplate(template=qa_template, input_variables=["chat_history", "context", "input"])

        

    def handle_message(self, user_message, chat_history):
        """
        Process a user's message with chat history using the RAG chain.
        
        Args:
            user_message (str): The user's message.
            chat_history (list): A list of previous messages.
        
        Returns:
            str: The assistant's response.
        """
        logging.info(f"Handling user message: {user_message}")
        logging.info(f"Handling user history message: {chat_history}")

        response = self.rag_chain.invoke({"input": user_message, "chat_history": chat_history})
        print(response)
        
        # Extract and return the assistant's response
        assistant_response = response["answer"]
        logging.info(f"Assistant response: {assistant_response}")
        
        return assistant_response
    
    def reformulate_question(self, user_message, chat_history):
      # Format the reformulation prompt with chat history and user message
      reformulation_input = self.contextualize_q_prompt.format(
          chat_history=chat_history,
          input=user_message
      )
      
      # Use LLM to reformulate the question based on the prompt
      reformulated_question = self.llm.invoke(reformulation_input)
      return reformulated_question

      
    def chat(self, user_message, chat_history):
        """
        Process a user's message with chat history using the RAG chain.
        
        Args:
            user_message (str): The user's message.
            chat_history (list): A list of previous messages.
        
        Returns:
            str: The assistant's response.
        """
        # Step 1: Use the retriever to get the relevant documents
        reformulated_question = self.reformulate_question(user_message, chat_history)

        # Step 2: Retrieve relevant documents based on the reformulated question
        retrieved_docs = self.retriever.get_retriever().invoke(reformulated_question.content)

        # Step 3: Pass the context and user input to the question-answering chain
        response = self.question_answer_chain.invoke({
            "context": retrieved_docs,
            "chat_history": chat_history,
            "input": user_message
        })

        assistant_response = response["answer"]
        logging.info(f"Assistant response: {assistant_response}")
        return assistant_response

    def continual_chat(self):
        """
        Start a continual chat session with the assistant.
        """
        print("Welcome to Midnight Diner, your late-night therapy assistant. Type 'exit' to end the conversation.")
        chat_history = []  # List to store chat history
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Thank you for sharing with Midnight Diner. Take care!")
                break

            # Process the user's message through the conversation handler
            response = self.handle_message(user_input, chat_history)

            # Display assistant's response
            print(f"AI: {response}")

            # Update chat history
            # if not chat_history or not isinstance(chat_history[0], SystemMessage):
            #   chat_history.insert(0, SystemMessage(content="Hello! How can I help you today?"))
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(SystemMessage(content=response))


# Main script entry point
if __name__ == "__main__":
    conversation = Conversation()
    conversation.continual_chat()
