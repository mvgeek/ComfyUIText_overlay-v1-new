class TestNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "Hello World"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process"
    CATEGORY = "test"
    
    def process(self, text):
        print(f"Test node received text: {text}")
        return (text,)

# Add this to the node mappings in __init__.py 