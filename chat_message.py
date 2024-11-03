from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def serialize_message(message):
    """Convert a LangChain message object to a dictionary for MongoDB storage."""
    if isinstance(message, HumanMessage):
        return {
            "role": "human",
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "response_metadata": message.response_metadata,
        }
    elif isinstance(message, SystemMessage):
        return {
            "role": "system",
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "response_metadata": message.response_metadata,
        }
    elif isinstance(message, AIMessage):
        return {
            "role": "ai",
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "response_metadata": message.response_metadata,
        }
    else:
        raise TypeError(f"Cannot serialize message of type {type(message)}")

def deserialize_message(serialized_message):
    """Convert a dictionary back into a LangChain message object."""
    role = serialized_message["role"]
    content = serialized_message["content"]
    additional_kwargs = serialized_message.get("additional_kwargs", {})
    response_metadata = serialized_message.get("response_metadata", {})

    if role == "human":
        return HumanMessage(content=content, additional_kwargs=additional_kwargs, response_metadata=response_metadata)
    elif role == "system":
        return SystemMessage(content=content, additional_kwargs=additional_kwargs, response_metadata=response_metadata)
    elif role == "ai":
        return AIMessage(content=content, additional_kwargs=additional_kwargs, response_metadata=response_metadata)
    else:
        raise ValueError(f"Unknown role type: {role}")