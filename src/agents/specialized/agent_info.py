from src.agents.specialized.specialized_agent import SpecializedAgent
import os
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain.tools import tool



class AgentInfo(SpecializedAgent):
    def __init__(self):
        super().__init__("agent_info", "managing information requests")
        self.vectorstore_db = "./vectorstore"
        self.embedding_nn = "mxbai-embed-large"
        self.documents_pdf_dir = "./documents"
        self.llm_model = "qwen2.5"
        self.agent = None
        self.system_prompt = """
        You are an assistant at a dental office called Your Smile.

        Always use the tool to answer questions about the dental office.
        """


    def build_vectorstore(self,folder_path: str, persist_dir: str):
        docs = []

        for file in os.listdir(folder_path):
            if file.endswith(".pdf"):
                file_path = os.path.join(folder_path, file)
                loader = PyPDFLoader(file_path)
                docs.extend(loader.load())

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        docs_chunks = splitter.split_documents(docs)

        embeddings = OllamaEmbeddings(model=self.embedding_nn)

        vectorstore = Chroma.from_documents(
            docs_chunks,
            embeddings,
            persist_directory=persist_dir
        )

        return vectorstore

    def create_pdf_tool(self,vectorstore):

        @tool
        def pdf_retriever(query: str) -> str:
            """Use this tool to search for information about dental office"""
            results = vectorstore.similarity_search(query, k=3)
            return "\n\n".join(d.page_content for d in results)

        return pdf_retriever



    async def initialize(self):
        vectorstore = self.build_vectorstore(self.documents_pdf_dir, self.vectorstore_db)

        pdf_tool = self.create_pdf_tool(vectorstore)

        llm = ChatOllama(model=self.llm_model)

        self.agent = create_agent(
            model=llm,
            tools=[pdf_tool],
            system_prompt=self.system_prompt
        )

    async def run(self, messages: []) -> str:
        response = self.agent.invoke({
            "messages": messages
        })

        content = response["messages"][-1].content

        return content