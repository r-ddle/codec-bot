"""
Image Generation Helper Module
Unified image generation with error handling and performance optimization.
"""
import asyncio
from io import BytesIO
from typing import Callable, Optional, Any
import discord
from discord.ext import commands
from config.settings import logger


class ImageGenerationError(Exception):
    """Custom exception for image generation failures."""
    pass


async def generate_and_send_image(
    ctx_or_interaction,
    generator_func: Callable,
    fallback_embed_func: Optional[Callable] = None,
    filename: str = "image.png",
    **generator_kwargs
) -> bool:
    """
    Unified image generation and error handling for both Context and Interaction.

    Args:
        ctx_or_interaction: Discord Context or Interaction object
        generator_func: Function that generates PIL Image (runs off event loop)
        fallback_embed_func: Optional function that returns a fallback Embed
        filename: Output filename for Discord file
        **generator_kwargs: Arguments passed to generator_func

    Returns:
        bool: True if successful, False if fallback was used

    Usage:
        await generate_and_send_image(
            ctx,
            generate_rank_card,
            filename="rank.png",
            username="Snake",
            rank="Colonel",
            xp=5000
        )
    """
    # Determine if Context or Interaction
    is_interaction = hasattr(ctx_or_interaction, 'response') and hasattr(ctx_or_interaction, 'user')
    is_context = hasattr(ctx_or_interaction, 'send') and hasattr(ctx_or_interaction, 'author')

    # Show typing/thinking indicator
    try:
        if is_context:
            typing_ctx = ctx_or_interaction.typing()
            await typing_ctx.__aenter__()
        elif is_interaction:
            # Check if response was already deferred
            if not ctx_or_interaction.response.is_done():
                await ctx_or_interaction.response.defer()
    except Exception as e:
        logger.warning(f"Could not show typing indicator: {e}")

    try:
        # Generate image off event loop (CPU-bound operation)
        img = await asyncio.to_thread(generator_func, **generator_kwargs)

        # Convert PIL Image to bytes off event loop
        buffer = BytesIO()
        await asyncio.to_thread(img.save, buffer, 'PNG')
        buffer.seek(0)

        # Create Discord file
        file = discord.File(buffer, filename=filename)

        # Send based on type
        if is_context:
            await ctx_or_interaction.send(file=file)
        elif is_interaction:
            if ctx_or_interaction.response.is_done():
                await ctx_or_interaction.followup.send(file=file)
            else:
                await ctx_or_interaction.response.send_message(file=file)

        return True

    except Exception as e:
        logger.error(f"Image generation failed for {generator_func.__name__}: {e}", exc_info=True)

        # Use fallback embed if provided
        if fallback_embed_func:
            try:
                fallback_embed = fallback_embed_func()

                if is_context:
                    await ctx_or_interaction.send("⚠️ Image generation failed. Showing text version:", embed=fallback_embed)
                elif is_interaction:
                    if ctx_or_interaction.response.is_done():
                        await ctx_or_interaction.followup.send("⚠️ Image generation failed. Showing text version:", embed=fallback_embed)
                    else:
                        await ctx_or_interaction.response.send_message("⚠️ Image generation failed. Showing text version:", embed=fallback_embed)

            except Exception as fallback_error:
                logger.error(f"Fallback embed also failed: {fallback_error}")
                # Last resort: simple error message
                error_msg = f"❌ Error generating image: {str(e)}"
                if is_context:
                    await ctx_or_interaction.send(error_msg)
                elif is_interaction:
                    try:
                        await ctx_or_interaction.followup.send(error_msg, ephemeral=True)
                    except:
                        pass
        else:
            # No fallback provided
            error_msg = f"❌ Error generating image: {str(e)}"
            if is_context:
                await ctx_or_interaction.send(error_msg)
            elif is_interaction:
                try:
                    if ctx_or_interaction.response.is_done():
                        await ctx_or_interaction.followup.send(error_msg, ephemeral=True)
                    else:
                        await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
                except:
                    pass

        return False

    finally:
        # Clean up typing indicator if needed
        if is_context:
            try:
                await typing_ctx.__aexit__(None, None, None)
            except:
                pass


# Concurrency semaphore for image generation (prevents CPU overload)
from config.bot_settings import MAX_CONCURRENT_IMAGE_GENERATION
_image_generation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_IMAGE_GENERATION)


async def generate_and_send_image_safe(
    ctx_or_interaction,
    generator_func: Callable,
    fallback_embed_func: Optional[Callable] = None,
    filename: str = "image.png",
    **generator_kwargs
) -> bool:
    """
    Same as generate_and_send_image but with concurrency limiting.
    Use this for CPU-intensive image generation to prevent overload.
    """
    async with _image_generation_semaphore:
        return await generate_and_send_image(
            ctx_or_interaction,
            generator_func,
            fallback_embed_func,
            filename,
            **generator_kwargs
        )
