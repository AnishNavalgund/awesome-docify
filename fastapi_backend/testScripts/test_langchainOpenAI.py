import sys
from pathlib import Path

from langchain_openai import OpenAIEmbeddings

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

print(embeddings.embed_query("Hello!"))
