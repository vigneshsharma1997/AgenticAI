from langchain_core.prompts import PromptTemplate 
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import StrOutputParser 
from langchain_openai import ChatOpenAI

from langchain_groq import ChatGroq 
import os 
from dotenv import load_dotenv 
load_dotenv() 
groq_api_key = os.getenv("GROQ_API_KEY") 
os.environ["LANGCHAIN_TRACING_V2"] = "false" 
 
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=groq_api_key,
    temperature=0
)

# llm = ChatOpenAI(
#     model="gpt-4o-mini",   # or gpt-4.1 / gpt-4o
#     temperature=0,
# )


# def CustomLLM():   
#     # LangGroq model (via LangChain interface) 
#     llm = ChatGroq(model="openai/gpt-oss-20b",groq_api_key=groq_api_key) 
#     return llm 
 
