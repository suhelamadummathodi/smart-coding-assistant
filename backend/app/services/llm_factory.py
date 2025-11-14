from typing import List
import requests
from app.core.config import settings
from google import genai
from google.genai.types import Content, Part
from openai import OpenAI
import anthropic
from dotenv import load_dotenv
import os


load_dotenv()

class LLMFactory:
    """
    A factory class to abstract interaction with different LLMs (Ollama, OpenAI, etc.)
    """
    
    @staticmethod
    def generate_response(messages: List[dict], model: str = "ollama") -> str:
        try:
            if model.lower() == "ollama":
                return LLMFactory._generate_with_ollama(messages)
            elif model.lower() == "openai":
                return LLMFactory._generate_with_openai(messages)
            elif model.lower() == "gemini":
                return LLMFactory._generate_with_genai(messages)
            elif model.lower() == "claude":
                return LLMFactory._generate_with_claudeai(messages)
            else:
                return f"Error: Unsupported model '{model}'. Try 'ollama' or 'openai' or genai."
        except Exception as e:
            return f"Error generating response: {str(e)}"

    @staticmethod
    def _generate_with_ollama(messages: List[dict]) -> str:
        """
        Use local Ollama server to generate response
        """
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={"model": "llama3", "messages": messages, "stream": True},
                timeout=300,
                stream=True
            )
            response.raise_for_status()

            full_response = ""

            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = line.decode("utf-8").strip()
                    if data.startswith("{"):
                        import json
                        json_data = json.loads(data)
                        if "message" in json_data and "content" in json_data["message"]:
                            full_response += json_data["message"]["content"]
                except Exception:
                    continue

            return full_response.strip() or "No response from Ollama."
        except requests.exceptions.RequestException as e:
            return f"Ollama Error: {str(e)}"

    @staticmethod
    def _generate_with_openai(messages: List[dict]) -> str:
        """
        Placeholder for OpenAI integration (future use)
        """
        try:
            print("API KEY:", os.getenv("OPENAI_API_KEY"))
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages= messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI Error: {e}"
        
    
    @staticmethod
    def _generate_with_genai(messages: List[dict]) -> str:
        """
        Placeholder for GoogleAI integration (future use)
        """
        try:
            # The client gets the API key from the environment variable `GEMINI_API_KEY`.
            client = genai.Client()
          
            contents = []
            for msg in messages:
                role = msg.get("role", "user")
                if role not in ["user", "model"]:
                # Map "assistant" or "system" → "model"
                    role = "model" if role in ["assistant", "system"] else "user"

                text = msg.get("content", "")
                contents.append(Content(role=role, parts=[Part(text=text)]))


            response = client.models.generate_content(
                model="gemini-2.5-flash", contents= contents
            )
            return response.text.strip() if response.text else "No response from Gemini AI."
        except Exception as e:
            return f"Gemini Error: {str(e)}"
        
    @staticmethod
    def _generate_with_claudeai(messages: List[dict]) -> str:
        try:
            client = anthropic.Anthropic()

            response = client.messages.create(
                model="claude-sonnet-4",
                max_tokens=50,
                messages=messages
            )
            return response.content.strip() if response.content else "No response from Claude AI."
        except Exception as e:
            return f"Claude Error: {str(e)}"
        