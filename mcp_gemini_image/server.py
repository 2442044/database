import os
import sys
import google.generativeai as genai
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Gemini Image Generator")

@mcp.tool()
def generate_image(prompt: str, output_filename: str = "generated_image.png") -> str:
    """
    Generate an image using Google's Imagen model via Gemini API.
    
    Args:
        prompt: The description of the image to generate.
        output_filename: The filename to save the generated image (default: generated_image.png).
    
    Returns:
        A message indicating where the image was saved.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY environment variable is not set. Please configure it in your MCP settings."

    try:
        genai.configure(api_key=api_key)
        
        # Try to use Imagen 3 model
        model_name = 'imagen-3.0-generate-001'
        
        try:
            # Check for ImageGenerationModel (available in newer versions)
            if hasattr(genai, 'ImageGenerationModel'):
                model = genai.ImageGenerationModel.from_pretrained(model_name)
            else:
                # Fallback or error if not available
                return "Error: ImageGenerationModel not found in google-generativeai library. Please update the library."
                
            # Generate images
            images = model.generate_images(
                prompt=prompt,
                number_of_images=1,
            )
            
            if not images:
                return "Error: No images were generated."
                
            # Determine output path - make it absolute
            # Use current working directory if path is relative
            if not os.path.isabs(output_filename):
                output_path = os.path.join(os.getcwd(), output_filename)
            else:
                output_path = output_filename
                
            # Save the image
            images[0].save(output_path)
            
            return f"Success! Image generated and saved to: {output_path}"
            
        except Exception as e:
            return f"Error generating image with model {model_name}: {str(e)}"

    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
