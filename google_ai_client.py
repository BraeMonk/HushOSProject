import requests
import json

class GoogleAIClient:
    """Simple Google AI API client that works with Buildozer/Android"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def generate_content(self, model_name="gemini-1.5-flash", prompt="", max_tokens=1000):
        """Generate content using Google's Gemini API"""
        try:
            url = f"{self.base_url}/{model_name}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                return content
            else:
                return "Sorry, I couldn't generate a response."
                
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service."
        except KeyError as e:
            print(f"Response parsing error: {e}")
            return "Sorry, I received an unexpected response format."
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "Sorry, something went wrong."

# Example usage in your main code:
# Replace your google-generativeai import with:
# from google_ai_client import GoogleAIClient
# 
# Then instead of:
# import google.generativeai as genai
# genai.configure(api_key="your_api_key")
# model = genai.GenerativeModel("gemini-1.5-flash")
# response = model.generate_content("Hello")
#
# Use:
# client = GoogleAIClient("your_api_key")
# response = client.generate_content("gemini-1.5-flash", "Hello")
