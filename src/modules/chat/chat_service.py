from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_core.messages import (
  AIMessage,
  BaseMessage,
  HumanMessage,
  SystemMessage,
  ToolMessage,
)
from langchain_core.prompts import ChatMessagePromptTemplate

from ai_agents.base_agent import BaseAgent
from modules.chat.dto.chat_dto import ChatHistoryDTO


def _get_prompt_template() -> ChatMessagePromptTemplate:
  template = ChatMessagePromptTemplate.from_template(
    """# Instruction
Answer the message based only on the following context.

---

## Context

{context}

---

## User Question
{question}

---

## Tasks

Provide a detailed answer.
"""
  )

  return template


def _format_docs(docs: list[Document]) -> str:
  """Format retrieved documents into a string"""
  return '\n\n'.join(doc.page_content for doc in docs)


def _convert_chat_list(chat_list: list[ChatHistoryDTO]) -> list[BaseMessage]:
  """Convert chat history list to proper message list for LLM"""
  result: list[BaseMessage] = []

  for chat in chat_list:
    role = chat.role
    content = chat.content
    message: BaseMessage

    if role == 'user':
      message = HumanMessage(content=content)
    elif role == 'system':
      message = SystemMessage(content=content)
    elif role == 'assistant':
      message = AIMessage(content=content)
    elif role == 'tool':
      message = ToolMessage(content=content)
    else:
      raise HTTPException(
        status_code=400, detail=f'Invalid role `{role}` in chat history.'
      )

    result.append(message)

  return result


def process_chat(chat_list: list[ChatHistoryDTO]) -> AIMessage:
  agent = BaseAgent()

  messages = _convert_chat_list(chat_list)
  agent_res = agent.chat(messages=messages)

  return agent_res


def process_chat_with_rag(chat_list: list[ChatHistoryDTO]) -> AIMessage:
  # prompt_template = _get_prompt_template()

  agent = BaseAgent()

  messages = _convert_chat_list(chat_list)
  agent_res = agent.chat(messages=messages)

  return agent_res
