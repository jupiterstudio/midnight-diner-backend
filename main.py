from fastapi import FastAPI, HTTPException, Request, Depends
from auth import get_current_user  # Import the JWT verification function
from conversation import Conversation
from models import UserInfo
from langchain_core.messages import HumanMessage, SystemMessage
from user import get_chat_history, get_user, save_chat_history, sign_up_user, login_user, choose_character  # Import user operations

app = FastAPI()

conversation = Conversation()

# Endpoint for user sign up
@app.post("/api/signup")
async def sign_up(request: Request):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    # Sign up the user and store information in MongoDB
    return sign_up_user(email, password)


# Endpoint for user login
@app.post("/api/login")
async def login(request: Request):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    # Log in the user and return JWT token
    return login_user(email, password)


# Endpoint for character selection (protected route)
@app.post("/api/select-character")
async def select_character(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    selected_character = body.get("character")

    # Call the function to store the selected character in MongoDB
    return choose_character(user["sub"], selected_character)

@app.get("/api/user-info", response_model=UserInfo)
async def get_user_info(user: dict = Depends(get_current_user)):
    auth0_id = user["sub"]  # Auth0's unique identifier for the user

    # Fetch user data from MongoDB based on Auth0 ID
    user_data = get_user(auth0_id)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Return user information
    return UserInfo(
        selected_character=user_data.get("selected_character", "girl"),
    )
    
@app.post("/api/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    # Get the user ID from the JWT token
    user_id = user["sub"]
    
    # fetch chat history from MongoDB based on user ID
    chat_history = get_chat_history(user_id)

    # Get the user's message from the request
    body = await request.json()
    user_message = body.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message content is required")

    # Use the Conversation class to generate a response
    assistant_response = conversation.handle_message(user_message, chat_history)

    #Update the chat history with the new message and assistant response
    if not chat_history or not isinstance(chat_history[0], SystemMessage):
        chat_history.insert(0,SystemMessage(content="Hello! How can I help you today?"))  # Insert at the beginning if not present
    chat_history.append(HumanMessage(content=user_message))
    chat_history.append(SystemMessage(content=assistant_response))

    # Save the updated chat history back to MongoDB
    save_chat_history(user_id, chat_history)

    # Return the assistant's response
    return {"response": assistant_response}