"""
Image processing service.

Handles image processing, conversion, and manipulation operations.
"""

import io
from typing import Union, Any

import base64
import numpy as np
import torch
from PIL import Image, ImageOps


class ImageProcessingService:
    """Service for handling image processing operations."""
    
    def prepare_reference_image(self, ref_image_b64: str, target_size: int = 512) -> Image.Image:
        """
        Prepare a reference image for IP-Adapter.
        
        Args:
            ref_image_b64: Base64 encoded reference image
            target_size: Target size for the image
            
        Returns:
            Processed PIL Image
        """
        # Decode base64 image
        image_data = base64.b64decode(ref_image_b64.split(",")[-1])
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # Resize with letterboxing to preserve aspect ratio
        image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        
        # Add padding if needed
        pad_w, pad_h = target_size - image.width, target_size - image.height
        if pad_w or pad_h:
            image = ImageOps.expand(
                image,
                border=(
                    pad_w // 2, 
                    pad_h // 2, 
                    pad_w - pad_w // 2, 
                    pad_h - pad_h // 2
                ),
                fill=(0, 0, 0),
            )
        
        return image
    
    def extract_image_from_result(self, result: Any) -> Image.Image:
        """
        Extract PIL Image from generation result.
        
        Args:
            result: Generation result from the pipeline
            
        Returns:
            PIL Image object
        """
        try:
            # Try to get image from result.images
            if hasattr(result, "images"):
                image = result.images[0]
            else:
                # Fallback to first element if it's a list
                image = result[0]
        except (IndexError, AttributeError):
            # Create a black image as fallback
            return Image.new("RGB", (512, 512), color="black")
        
        # Ensure we have a PIL Image
        if not hasattr(image, "save"):
            image = self._convert_to_pil_image(image)
        
        return image
    
    def _convert_to_pil_image(self, image_data: Union[torch.Tensor, np.ndarray, Any]) -> Image.Image:
        """
        Convert various image formats to PIL Image.
        
        Args:
            image_data: Image data in various formats
            
        Returns:
            PIL Image object
        """
        try:
            if isinstance(image_data, torch.Tensor):
                # Convert PyTorch tensor to numpy array
                array = image_data.detach().cpu().numpy()
                
                # Normalize to 0-255 range if needed
                if array.max() <= 1.0:
                    array = (array * 255).astype(np.uint8)
                else:
                    array = array.astype(np.uint8)
                
                return Image.fromarray(array)
            
            elif hasattr(image_data, '__array__'):
                # Handle numpy array
                array = np.array(image_data)
                
                # Normalize to 0-255 range if needed
                if array.dtype != np.uint8:
                    if array.max() <= 1.0:
                        array = (array * 255).astype(np.uint8)
                    else:
                        array = array.astype(np.uint8)
                
                return Image.fromarray(array)
            
            else:
                # Fallback: create black image
                return Image.new("RGB", (512, 512), color="black")
                
        except Exception as e:
            from app.logging_setup import logger
            logger.warning(f"Failed to convert image to PIL: {e}")
            return Image.new("RGB", (512, 512), color="black")
