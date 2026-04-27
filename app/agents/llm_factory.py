from venv import logger

from langchain_ollama import ChatOllama

import os

from langchain_openai import ChatOpenAI

class LLMsFactory:
    def __init__(self):
        self.ollama = None
        self.openai = None
        self.initialize_llms()
    
    def initialize_llms(self):
        self.ollama = ChatOllama(
                    model="llama3.2:3b",
                    temperature=0,
                    base_url="http://ollama:11434",
                )
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
            logger.warning("Missing OpenAI configuration in environment variables. Please set them to use the OpenAI chat.")
        else:
            # ChatOpenAI load OPENAI_API_KEY from environment variable by default, so we don't need to pass it in directly here.
            self.openai = ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL"),
                    # stream_usage=True,
                    # temperature=None,
                    # max_tokens=None,
                    # timeout=None,
                    # reasoning_effort="low",
                    # max_retries=2,
                    # api_key="...",  # If you prefer to pass api key in directly
                    # base_url="...",
                    # organization="...",
                    # other params...
                )
