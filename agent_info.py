import os
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain.tools import tool


VECTORSTORE_DB = "./vectorstore"
EMBEDDING_NN = "mxbai-embed-large"
LLM = "qwen2.5"
DOCUMENTS_PDF_DIR = "./documents"


def build_vectorstore(folder_path: str, persist_dir: str = VECTORSTORE_DB):
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

    embeddings = OllamaEmbeddings(model=EMBEDDING_NN)

    vectorstore = Chroma.from_documents(
        docs_chunks,
        embeddings,
        persist_directory=persist_dir
    )

    return vectorstore


def create_pdf_tool(vectorstore):

    @tool
    def pdf_retriever(query: str) -> str:
        """Use this tool to search for information about dental office"""
        results = vectorstore.similarity_search(query, k=3)
        return "\n\n".join(d.page_content for d in results)

    return pdf_retriever


def main():
    vectorstore = build_vectorstore(DOCUMENTS_PDF_DIR)

    pdf_tool = create_pdf_tool(vectorstore)

    llm = ChatOllama(model=LLM)

    agent = create_agent(
        model=llm,
        tools=[pdf_tool],
        system_prompt="""
        You are an assistant at a dental office called Your Smile.

        Always use the tool to answer questions about the dental office.
        """
    )

    while True:
        user_input = input("\nUser: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        response = agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        print("\nDentalbot:", response["messages"][-1].content)


if __name__ == "__main__":
    main()