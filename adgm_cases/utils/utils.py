import os
from typing import Optional, List
from loguru import logger
import pymupdf4llm
from pdf2image import convert_from_path
from tqdm import tqdm


class PDF2MD:
    @staticmethod
    def parse_pdf_2_md(pdf_path) -> Optional[str]:
        """
        Converts the provided PDF to Markdown format using the PdfConverter engine.

        Returns:
            str: The Markdown content extracted from the PDF, or None if parsing fails.
        """
        try:
            # Assuming the pdf_engine call returns an object with 'markdown' attribute
            logger.info("Running Conversion...")
            md_text = pymupdf4llm.to_markdown(pdf_path)
            logger.info("Running Cleaning...")
            md_text = PDF2MD.cleaning_md_4llm(md_text)
            return md_text
        except Exception as e:
            print(f"Error while converting PDF to markdown: {e}")
            raise ValueError(e)

    @staticmethod
    def cleaning_md_4llm(text: str) -> str:

        clean_lines = []

        for line in text.splitlines():
            if line == "-----":
                continue
            if line.startswith("**"):
                line = line.replace("*", "").replace("_", "")
                line = f"### {line}"
            clean_lines.append(line)

        return "\n".join(clean_lines)

    @staticmethod
    # Function to save uploaded file
    def save_uploaded_file(session_id, uploaded_file):
        temp_dir = os.path.join(session_id, "temp_pdfs")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())  # Save the uploaded file

        return file_path  # Return local file path

    @staticmethod
    def pdf_to_images(
        pdf_path: str, output_folder: str = None, dpi: int = 100
    ) -> List[str]:
        """
        Converts a PDF file into a list of image file paths.

        :param pdf_path: Path to the PDF file.
        :param output_folder: Folder to save images (optional, uses temp directory if not provided).
        :param dpi: Resolution for image conversion (default: 300 DPI).
        :return: List of file paths for the extracted images.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} does not exist.")

        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)

        images = convert_from_path(pdf_path, dpi=dpi)
        image_paths = []

        for i, image in tqdm(enumerate(images), total=len(images)):
            image_filename = f"page_{i + 1}.jpg"
            image_path = os.path.join(output_folder or os.getcwd(), image_filename)
            image.save(image_path, "JPEG")
            image_paths.append(image_path)

        return image_paths
