# ComfyUI Text Overlay Node

A custom node for ComfyUI that adds text overlays to images with support for multiple text elements, custom fonts, and automatic positioning.

## Features

- Multiple text elements (heading, description, author)
- Custom font support (currently includes Sharp Grotesk fonts)
- Automatic text positioning and wrapping
- Percentage-based margins and width
- Flexible alignment options
- Different font sizes and colors for each text element

## Installation

1. Clone this repository into your ComfyUI custom nodes directory:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/mvgeek/ComfyUIText_overlay-v1.git
```

2. Make sure you have the required fonts in the `fonts` directory:
   - SharpGroteskCyrBold-25.otf
   - SharpGroteskCyrBook-25.otf

## Usage

The node provides the following inputs:

### Text Elements
- **Heading**: Main title text
- **Description**: Body text that can span multiple lines
- **Author**: Single-line author attribution

### Styling Options
- Font selection for each text element
- Font size control
- Color customization
- Line spacing adjustment

### Positioning
- Vertical position (top/middle/bottom)
- Horizontal alignment (left/center/right)
- Margin percentage
- Width percentage

## Example

1. Connect an image input to the node
2. Set your text content:
   - Heading: "Amazing AI Art"
   - Description: "This piece was generated using stable diffusion..."
   - Author: "Created by YourName"
3. Adjust positioning and styling as needed

## License

MIT License - feel free to use this node in your projects!