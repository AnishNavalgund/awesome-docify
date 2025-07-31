from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from app.schemas import Intent
from app.config import settings
from app.utils import logger_info


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",  
    temperature=0.2,
    openai_api_key=settings.OPENAI_API_KEY
)

# Define the parser for Pydantic Intent
parser = PydanticOutputParser(pydantic_object=Intent)

# Prompt template with format instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract a structured developer intent from the query below."),
    ("human", "{query}\n\n{format_instructions}")
])

async def extract_intent(user_query: str) -> Intent:
    """
    Extract a structured Intent object from the user query using LangChain + OpenAI + Pydantic.
    """
    formatted_prompt = prompt.format_messages(
        query=user_query,
        format_instructions=parser.get_format_instructions()
    )

    try:
        response = await llm.ainvoke(formatted_prompt)
        logger_info.info(f"LLM Call successful")
        return parser.parse(response.content)
    except Exception as e:
        # Check if it's an API key error
        if "invalid_api_key" in str(e).lower() or "401" in str(e):
            raise ValueError(f"OpenAI API key error: Please check your API key configuration. Error: {e}")
        else:
            raise ValueError(f"Failed to extract intent: {e}")
