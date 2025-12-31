import os
from typing import List
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from duckduckgo import DDGS
from langchain_ollama import ChatOllama