import os
from dotenv import load_dotenv
from fastapi import HTTPException
from auth import get_auth0_token
import requests
from chat_message import deserialize_message, serialize_message
from mongodb import MongoDB

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")


# MongoDB Singleton Instance
mongo_instance = MongoDB()

# Function to sign up a user and store their information in MongoDB
def sign_up_user(email: str, password: str):
    headers = {
        "Authorization": f"Bearer {get_auth0_token()}",
        "content-type": "application/json"
    }

    user_data = {
        "email": email,
        "password": password,
        "connection": "Username-Password-Authentication"
    }

    # Create user in Auth0
    response = requests.post(f'https://{AUTH0_DOMAIN}/api/v2/users', json=user_data, headers=headers)
    if response.status_code == 201:
        user_info = response.json()
        

        # Store user in MongoDB
        users_collection = mongo_instance.get_collection("users")
        new_user = {
            "auth0_id": user_info["user_id"],
            "email": email,
            "metadata": user_info.get("user_metadata", {})
        }
        users_collection.insert_one(new_user)  # Insert user data into MongoDB

        return {"message": "User created and stored successfully"}
    else:
        raise HTTPException(status_code=400, detail="Sign-up failed")


# Function to log in a user
def login_user(email: str, password: str):
    login_data = {
        "grant_type": "password",
        "username": email,
        "password": password,
        "audience": AUTH0_AUDIENCE,
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "realm": 'Username-Password-Authentication',
        "scope": 'offline_access openid',
    }

    # Requesting the token from Auth0
    response = requests.post(f'https://{AUTH0_DOMAIN}/oauth/token', json=login_data)
    if response.status_code == 200:
        return response.json()  # Return JWT token
    else:
        raise HTTPException(status_code=400, detail="Login failed")


# Function to select a character and store it in MongoDB
def choose_character(auth0_id: str, selected_character: str):
    if selected_character not in ["girl", "boy"]:
        raise HTTPException(status_code=400, detail="Invalid character selection")

    # Get the users collection and update the user's selected character
    users_collection = mongo_instance.get_collection("users")
    users_collection.update_one(
        {"auth0_id": auth0_id},  # 'auth0_id' contains the user's unique identifier
        {"$set": {"selected_character": selected_character}},
        upsert=True
    )

    return {"message": "Character selected successfully"}

def get_user(auth0_id: str):
    users_collection = mongo_instance.get_collection("users")
    user_data = users_collection.find_one({"auth0_id": auth0_id})
    return user_data
    
def get_chat_history(auth0_id: str):
    chat_history_collection = mongo_instance.get_collection("chat-history")
    chat_history_records = chat_history_collection.find_one({"user_id": auth0_id})
    serialized_history = chat_history_records.get("chat_history", []) if chat_history_records else []
    chat_history = [deserialize_message(msg) for msg in serialized_history]
    return chat_history

# Function to select a character and store it in MongoDB
def save_chat_history(auth0_id: str, chat_history: any):
    chat_history_collection = mongo_instance.get_collection("chat-history")
    serialized_history = [serialize_message(msg) for msg in chat_history]
    chat_history_collection.update_one(
        {"user_id": auth0_id},  # 'auth0_id' contains the user's unique identifier
        {"$set": {"chat_history": serialized_history}},
        upsert=True
    )

    return {"message": "Chat history saved successfully"}
