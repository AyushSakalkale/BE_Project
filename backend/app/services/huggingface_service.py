import aiohttp
from app.core.config import settings

class HuggingFaceService:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        self.headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    async def explain_log(self, log_message: str) -> str:
        prompt = f"Rewrite this technical log into one friendly, clear sentence a non-technical person can understand. Be specific but simple: {log_message}"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 50, "temperature": 0.7}}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            return result[0].get("generated_text", log_message)
                        return result.get("generated_text", log_message)
                    else:
                        print(f"HuggingFace API Error: {response.status}")
                        return log_message
        except Exception as e:
            print(f"HuggingFace Error: {e}")
            return log_message

huggingface_service = HuggingFaceService()
