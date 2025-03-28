from PIL import Image, ImageDraw, ImageFont, ImageFilter
import torch
import numpy as np
import os

class TextOverlay:
    def __init__(self, device="cpu"):
        self.device = device
        self.fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        if not os.path.exists(self.fonts_dir):
            print(f"WARNING: Fonts directory not found at {self.fonts_dir}")
    
    _alignments = ["left", "right", "center"]
    _vertical_positions = ["top", "middle", "bottom"]
    
    @classmethod
    def NAME(cls):
        return "ComfyUI_textover"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                # Heading text settings
                "heading": ("STRING", {"multiline": True, "default": "Main Heading"}),
                "heading_font": (["SharpGroteskCyrBold-25.otf", "SharpGroteskCyrBook-25.otf"], {"default": "SharpGroteskCyrBold-25.otf"}),
                "heading_size": ("INT", {"default": 60, "min": 10, "max": 200}),
                "heading_color": ("STRING", {"default": "#000000"}),
                
                # Description text settings
                "description": ("STRING", {"multiline": True, "default": "This is a description of the image that can span multiple lines if needed."}),
                "description_font": (["SharpGroteskCyrBold-25.otf", "SharpGroteskCyrBook-25.otf"], {"default": "SharpGroteskCyrBook-25.otf"}),
                "description_size": ("INT", {"default": 30, "min": 10, "max": 200}),
                "description_color": ("STRING", {"default": "#333333"}),
                
                # Author text settings
                "author": ("STRING", {"multiline": False, "default": "Author Name"}),
                "author_font": (["SharpGroteskCyrBold-25.otf", "SharpGroteskCyrBook-25.otf"], {"default": "SharpGroteskCyrBook-25.otf"}),
                "author_size": ("INT", {"default": 24, "min": 10, "max": 200}),
                "author_color": ("STRING", {"default": "#666666"}),
                
                # Global settings
                "horizontal_align": (cls._alignments, {"default": "left"}),
                "vertical_position": (cls._vertical_positions, {"default": "top"}),
                "margin_percent": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 20.0, "step": 0.5}),
                "line_spacing": ("INT", {"default": 20, "min": 0, "max": 200}),
                "width_percent": ("FLOAT", {"default": 80.0, "min": 10.0, "max": 100.0, "step": 5.0}),
                
                # Text block padding settings
                "heading_padding": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1}),
                "description_padding": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1}),
                "author_padding": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1}),
                "boundary_padding": ("INT", {"default": 0, "min": 0, "max": 200, "step": 1}),
                
                # Updated Shadow settings
                "shadow_enabled": (["Yes", "No"], {"default": "Yes"}),
                "shadow_offset": ("INT", {"default": 2, "min": 1, "max": 10, "step": 1}),
                "shadow_color": ("STRING", {"default": "#000000"}),
                "shadow_opacity": ("INT", {"default": 128, "min": 0, "max": 255, "step": 1}),
                "shadow_blur": ("INT", {"default": 3, "min": 0, "max": 10, "step": 1}),  # New blur setting
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "overlay_text"
    CATEGORY = "image/text"

    def wrap_text(self, text, font, max_width, draw):
        words = text.split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_width = draw.textlength(word, font=font)
            space_width = draw.textlength(" ", font=font) if current_line else 0
            
            if current_width + word_width + space_width <= max_width:
                current_line.append(word)
                current_width += word_width + space_width
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width

        if current_line:
            lines.append(" ".join(current_line))
        
        return lines

    def calculate_text_block_height(self, lines_data, text_paddings):
        """Calculate total height of all text elements including spacing and padding"""
        total_height = 0
        
        for i, data in enumerate(lines_data):
            font_size = data['font_size']
            num_lines = len(data['lines'])
            block_height = (font_size * num_lines) + (self.line_spacing * (num_lines - 1))
            total_height += block_height
            
            # Add padding if it's not the last block
            if i < len(lines_data) - 1:
                total_height += text_paddings[i]
        
        return total_height

    def overlay_text(
        self, image, 
        heading, heading_font, heading_size, heading_color,
        description, description_font, description_size, description_color,
        author, author_font, author_size, author_color,
        horizontal_align, vertical_position, margin_percent, line_spacing, width_percent,
        heading_padding, description_padding, author_padding, boundary_padding,
        shadow_enabled, shadow_offset, shadow_color, shadow_opacity, shadow_blur
    ):
        # Convert tensor to PIL Image
        image_tensor = image
        image_np = image_tensor.cpu().numpy()
        image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
        
        # Create an RGBA version for alpha blending if needed
        if image_pil.mode != 'RGBA':
            image_pil = image_pil.convert('RGBA')
        
        draw = ImageDraw.Draw(image_pil)

        # Get image dimensions
        img_width, img_height = image_pil.size
        self.line_spacing = line_spacing

        # Calculate margins and max width based on percentages
        margin = int((margin_percent / 100) * img_width)
        max_width = int((width_percent / 100) * img_width)
        
        # Helper functions
        def load_font(font_name, size):
            font_path = os.path.join(self.fonts_dir, font_name)
            if not os.path.exists(font_path):
                print(f"WARNING: Font file not found at {font_path}, falling back to default system font")
                # Fallback to a system font if the specific font is not found
                return ImageFont.load_default()
            return ImageFont.truetype(font_path, size)

        def parse_color(color_str):
            return tuple(int(color_str.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        
        # Parse shadow color with opacity
        shadow_rgb = parse_color(shadow_color)
        shadow_rgba = (shadow_rgb[0], shadow_rgb[1], shadow_rgb[2], shadow_opacity)
        
        # Prepare all text elements
        text_blocks = []
        text_paddings = []
        
        if heading:
            heading_font_obj = load_font(heading_font, heading_size)
            heading_lines = self.wrap_text(heading, heading_font_obj, max_width, draw)
            text_blocks.append({
                'lines': heading_lines,
                'font': heading_font_obj,
                'color': parse_color(heading_color),
                'font_size': heading_size
            })
            text_paddings.append(heading_padding)

        if description:
            description_font_obj = load_font(description_font, description_size)
            description_lines = self.wrap_text(description, description_font_obj, max_width, draw)
            text_blocks.append({
                'lines': description_lines,
                'font': description_font_obj,
                'color': parse_color(description_color),
                'font_size': description_size
            })
            text_paddings.append(description_padding)

        if author:
            author_font_obj = load_font(author_font, author_size)
            author_lines = [author]  # Author text doesn't need wrapping
            text_blocks.append({
                'lines': author_lines,
                'font': author_font_obj,
                'color': parse_color(author_color),
                'font_size': author_size
            })
            text_paddings.append(author_padding)

        # Calculate total height of text block
        total_height = self.calculate_text_block_height(text_blocks, text_paddings)

        # Calculate vertical starting position with boundary padding
        if vertical_position == "top":
            current_y = margin + boundary_padding
        elif vertical_position == "middle":
            current_y = (img_height - total_height) // 2
        else:  # bottom
            current_y = img_height - total_height - margin - boundary_padding

        # Create two separate layers - one for shadow and one for text
        shadow_layer = Image.new('RGBA', image_pil.size, (0, 0, 0, 0))
        text_layer = Image.new('RGBA', image_pil.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        text_draw = ImageDraw.Draw(text_layer)

        # Draw all text blocks
        for i, block in enumerate(text_blocks):
            for line in block['lines']:
                line_width = draw.textlength(line, font=block['font'])
                
                # Calculate x position based on alignment
                if horizontal_align == "left":
                    x = margin
                elif horizontal_align == "center":
                    x = (img_width - line_width) // 2
                else:  # right
                    x = img_width - line_width - margin
                
                # Draw text shadow if enabled
                if shadow_enabled == "Yes":
                    # Draw shadow with offset
                    shadow_draw.text(
                        (x + shadow_offset, current_y + shadow_offset), 
                        line, 
                        fill=shadow_rgba, 
                        font=block['font']
                    )
                
                # Draw main text
                text_draw.text(
                    (x, current_y), 
                    line, 
                    fill=block['color'] + (255,),
                    font=block['font']
                )
                
                current_y += block['font_size'] + line_spacing
            
            # Add padding between text blocks
            if i < len(text_blocks) - 1:
                current_y += text_paddings[i]
        
        # Apply blur to shadow layer if enabled
        if shadow_enabled == "Yes" and shadow_blur > 0:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        
        # Composite the layers: first shadow, then text
        image_pil = Image.alpha_composite(image_pil, shadow_layer)
        image_pil = Image.alpha_composite(image_pil, text_layer)
        
        # Convert back to RGB for tensor conversion
        image_pil = image_pil.convert('RGB')
        
        # Convert back to tensor
        image_tensor_out = torch.tensor(np.array(image_pil).astype(np.float32) / 255.0)
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
        return (image_tensor_out,) 