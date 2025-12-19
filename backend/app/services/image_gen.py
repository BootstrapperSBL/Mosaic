import logging
import httpx
import base64
import uuid
import asyncio
from app.config import settings
from app.database import supabase

logger = logging.getLogger(__name__)

class ImageGenerationService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        # Ensure we use the correct base URL for image generation
        # If BASE_URL is https://api.siliconflow.cn/v1, we use that.
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model = "black-forest-labs/FLUX.1-schnell" # Efficient and high quality

    async def generate_image(self, prompt: str, user_id: str) -> str:
        """
        Generate an image based on the prompt, upload to Supabase, and return the persistent URL.
        """
        try:
            # 1. Optimize prompt for Flux (English preferred)
            # We could use a small LLM call to translate/enhance prompt if it's Chinese, 
            # but Flux handles simple prompts okay. Let's assume the LLM generates Chinese descriptions,
            # so we might want to translate them or hope Flux handles Chinese (it often struggles).
            # Let's prepend "High quality, realistic, " to style it.
            
            # Simple translation/enhancement via LLM is safer but adds latency.
            # Let's try direct prompt first.
            
            logger.info(f"Generating image for prompt: {prompt}")
            
            payload = {
                "model": self.model,
                "prompt": f"high quality, realistic, {prompt}", 
                "image_size": "1024x1024",
                "batch_size": 1,
                "num_inference_steps": 4, # Schnell is fast
                "guidance_scale": 0.0 # Schnell often uses 0 or small guidance
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    json=payload,
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Image Gen API Error: {response.text}")
                    # Fallback to a placeholder service if generation fails
                    return f"https://image.pollinations.ai/prompt/{prompt}"
                
                result = response.json()
                
            # SiliconFlow usually returns a URL in 'data' list
            image_data = result["data"][0]
            image_url = image_data.get("url")
            
            if not image_url:
                raise Exception("No image URL returned")

            # 2. Download and Upload to Supabase to make it persistent
            # (SiliconFlow URLs are temporary)
            async with httpx.AsyncClient(timeout=30.0) as client:
                img_res = await client.get(image_url)
                img_res.raise_for_status()
                img_bytes = img_res.content
            
            # Generate filename
            filename = f"generated/{user_id}/{uuid.uuid4()}.jpg"
            
            # Upload
            supabase.storage.from_("uploads").upload(
                filename,
                img_bytes,
                {"content-type": "image/jpeg"}
            )
            
            # Get Public URL
            public_url = supabase.storage.from_("uploads").get_public_url(filename)
            
            logger.info(f"Image generated and stored: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}", exc_info=True)
            # Fallback
            return f"https://image.pollinations.ai/prompt/{prompt}"

image_gen_service = ImageGenerationService()
