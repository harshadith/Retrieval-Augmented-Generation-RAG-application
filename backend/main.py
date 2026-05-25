from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_classic.chains.question_answering import load_qa_chain
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()
# Ensure you have your GOOGLE_API_KEY in a .env file in the backend folder
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to hold our vector store temporarily (in production, use persistent storage)
vector_store = None

class QueryRequest(BaseModel):
    question: str

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf.file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

@app.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    global vector_store
    try:
        # 1. Extract Text
        raw_text = get_pdf_text(files)
        
        # 2. Chunk Text
        text_chunks = get_text_chunks(raw_text)
        
        # 3. Create Embeddings & Store in Vector DB (FAISS)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        
        return {"message": "Documents processed and vector database updated successfully."}
    except Exception as e:
        print(f"CRASH DETAILS: {str(e)}")  # <--- ADD THIS EXACT LINE
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(request: QueryRequest):
    global vector_store
    if not vector_store:
        raise HTTPException(status_code=400, detail="Please upload documents first.")
    
    # 1. Semantic Search
    docs = vector_store.similarity_search(request.question)
    
    # 2. Setup LLM & Prompt
    prompt_template = """
    Answer the question as detailed as possible from the provided context. If the answer is not in
    provided context, just say, "The answer is not available in the internal documents." Don't provide the wrong answer.
    
    Context:\n {context}?\n
    Question: \n{question}\n
    
    Answer:
    """
    
    model = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    
    # 3. Generate Answer
    response = chain.invoke({"input_documents": docs, "question": request.question})
    
    return {"answer": response["output_text"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)