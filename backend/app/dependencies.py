import os
from fastapi import Depends, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv()) # read local .env file

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
