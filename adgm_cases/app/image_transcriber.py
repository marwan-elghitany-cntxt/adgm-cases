import asyncio
import os
import re
import base64
from glob import glob
from typing import List, Dict
from loguru import logger
from langchain_openai import ChatOpenAI

from templates.prompt_templates import TRANSCRIPER_TEMPLATE


class ImageTranscriber:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: str,
        max_concurrent_tasks: int = 7,
        image_folder: str = "output_best/*.jpg",
        prompt: str = TRANSCRIPER_TEMPLATE,
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.image_folder = image_folder
        self.prompt = prompt
        self.model = ChatOpenAI(
            base_url=base_url,
            model=model_name,
            api_key=api_key,
            temperature=0.1,
        )
        self.sem = asyncio.Semaphore(self.max_concurrent_tasks)
        self.completed_count = 0  # Shared counter for progress

    async def _transcribe_image(
        self, img_path: str, results: Dict[int, str], progress_bar, total_images
    ):
        """Handles transcription of a single image while respecting concurrency limits."""
        async with self.sem:
            idx = int("".join(re.findall(r"\d+", os.path.basename(img_path))))
            results[idx] = await self.image_transcription(img_path)

            # Update shared progress counter safely
            self.completed_count += 1
            progress_bar.progress(
                self.completed_count / total_images
            )  # Progress now moves strictly forward

    async def image_transcription(self, image_path: str) -> str:
        """Calls VLLM Model for image transcription."""
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ]

        return await self.model.ainvoke(messages)

    async def process_images(self, imgs_path: List[str] = None, progress_bar=None):
        """Manages concurrent transcription of images with progress tracking and stores them in a Markdown file."""
        if imgs_path is None:
            imgs_path = glob(self.image_folder)

        if not imgs_path:
            logger.info("No images found for transcription.")
            return []

        # Determine the output directory
        output_dir = os.path.dirname(imgs_path[0])
        output_file = os.path.join(output_dir, "transcriptions.md")

        results = {}
        total_images = len(imgs_path)
        self.completed_count = 0  # Reset counter before processing

        tasks = [
            self._transcribe_image(img_path, results, progress_bar, total_images)
            for img_path in imgs_path
        ]
        await asyncio.gather(*tasks)

        # Sort results by image index
        sorted_results = dict(sorted(results.items()))
        transcriptions = [
            f"## Image {idx}\n\n{c.content}\n" for idx, c in sorted_results.items()
        ]

        # Save transcriptions to Markdown file in the same directory as the images
        with open(output_file, "w", encoding="utf-8") as md_file:
            md_file.write("\n".join(transcriptions))

        logger.info(f"Transcriptions saved to: {output_file}")
        return [c.content for c in sorted_results.values()]

    async def run(self, imgs_path: List[str] = None, progress_bar=None):
        """Main function to start processing images."""
        return await self.process_images(imgs_path, progress_bar)
