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

from app.core.logging import logger
from app.utils import out_path

class ImageProcessingService:  
    def save_image(self, image: Image.Image, stem: str) -> str:
        path = out_path(stem)
        image.save(path)
        return path

    def prepare_reference_image(self, ref_image_b64: str, target_size: int = 512) -> Image.Image:
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
        try:
            if hasattr(result, "images"):
                image = result.images[0]
            else:
                image = result[0]
        except (IndexError, AttributeError):
            return Image.new("RGB", (512, 512), color="black")
        
        if not hasattr(image, "save"):
            image = self._convert_to_pil_image(image)
        
        return image
    
    def _convert_to_pil_image(self, image_data: Union[torch.Tensor, np.ndarray, Any]) -> Image.Image:
        try:
            if isinstance(image_data, torch.Tensor):
                # Convert PyTorch tensor to numpy array
                array = image_data.detach().cpu().numpy()
                
                if array.ndim == 3 and array.shape[0] in (1, 3, 4):
                    array = array.transpose(1, 2, 0)
 
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
                return Image.new("RGB", (512, 512), color="black")
                
        except Exception as e:
            logger.warning(f"Failed to convert image to PIL: {e}")
            return Image.new("RGB", (512, 512), color="black")
