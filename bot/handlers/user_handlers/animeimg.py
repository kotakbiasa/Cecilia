import asyncio
import aiohttp
import random

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anime_api import (
    NEKOSBEST, NEKOSIA, NEKOSLIFE, PICRE, WAIFUPICS,
    NEKOSAPI, NEKOBOT, NEKOSMOE, WAIFUIM, ANYANIME,
    fetch_nekos_best, fetch_nekos_life, fetch_nekosia, fetch_waifu_pics,
    fetch_nekosapi, fetch_pic_re, fetch_nekobot, fetch_nekos_moe, fetch_waifu_im, fetch_any_anime
)

# Dispatcher to map categories to their respective API fetchers.
# This allows multiple APIs to serve the same category, with one chosen at random.
API_DISPATCHER = {
    "picre": {"cats": PICRE, "fetcher": fetch_pic_re, "has_limit": True},
    "nekosapi": {"cats": NEKOSAPI, "fetcher": fetch_nekosapi, "has_limit": True, "has_tags": True},
    "nekoslife": {"cats": NEKOSLIFE, "fetcher": fetch_nekos_life, "has_limit": True},
    "nekosbest": {"cats": NEKOSBEST, "fetcher": fetch_nekos_best, "hyphenated": True, "has_limit": True},
    "waifupics": {"cats": WAIFUPICS, "fetcher": fetch_waifu_pics, "hyphenated": True, "has_limit": True},
    "nekosia": {"cats": NEKOSIA, "fetcher": fetch_nekosia, "hyphenated": True, "has_limit": True, "has_tags": True},
    "nekobot": {"cats": NEKOBOT, "fetcher": fetch_nekobot, "has_limit": True},
    "nekosmoe": {"cats": NEKOSMOE, "fetcher": fetch_nekos_moe, "has_limit": True},
    "waifuim": {"cats": WAIFUIM, "fetcher": fetch_waifu_im, "hyphenated": True, "has_limit": True, "has_tags": True},
    "anyanime": {"cats": ANYANIME, "fetcher": fetch_any_anime, "has_limit": True},
}


async def func_animeimg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all reaction categories via aliases."""
    message = update.effective_message
    
    command_text = message.text.split()[0].lstrip('/').split('@')[0]
    category = None
    limit_arg = None
    tags = []
    send_as_doc = False # New flag

    if command_text == 'animeimg':
        if not context.args:
            # If /animeimg is used without arguments, show the help message
            help_text_parts = [
                "Gunakan perintah dengan salah satu kategori yang tersedia.\n\n",
                "<b>Contoh:</b>\n<code>/animeimg waifu</code>\n<code>/animeimg pat 5</code> (kirim 5 gambar)\n<code>/animeimg waifu white-hair</code> (dengan tag tambahan)\n<code>/animeimg neko doc</code> (kirim sebagai dokumen)\n\n",
                "<b>Kategori yang tersedia berdasarkan API:</b>"
            ]

            api_sources = {
                "pic.re": PICRE,
                "nekos.best": NEKOSBEST,
                "nekos.life": NEKOSLIFE,
                "waifu.pics": WAIFUPICS,
                "nekosapi.com": NEKOSAPI,
                "nekosia.cat": NEKOSIA,
                "nekobot.xyz": NEKOBOT,
                "nekos.moe": NEKOSMOE,
                "waifu.im": WAIFUIM,
                "any-anime-api": ANYANIME,
            }

            for api_name, cats in api_sources.items():
                if not cats: continue
                sorted_cats = sorted(list(cats))
                category_list_str = " ".join(f"<code>{cat}</code>" for cat in sorted_cats)
                help_text_parts.append(f"\n\n<b>{api_name}</b>:\n<blockquote>{category_list_str}</blockquote>")

            await message.reply_text("".join(help_text_parts), parse_mode='HTML', disable_web_page_preview=True)
            return
        else:
            # If /animeimg is used with an argument, that argument is the category
            category = context.args[0].lower()
            remaining_args = list(context.args[1:]) # Make a mutable copy
    else:
        # For other commands (/waifu, /pat), the command itself is the category
        category = command_text.lower()
        remaining_args = list(context.args) # Make a mutable copy

    # Check for 'doc' or '-d' flag and remove it
    if 'doc' in remaining_args:
        send_as_doc = True
        remaining_args.remove('doc')
    if '-d' in remaining_args:
        send_as_doc = True
        remaining_args.remove('-d')

    if remaining_args:
        if remaining_args[0].isdigit():
            limit_arg = remaining_args[0]
            tags = remaining_args[1:]
        else:
            # No limit provided, all are tags
            tags = remaining_args

    status_msg = await message.reply_text(f"<i>Mencari <code>{category}</code>...</i>", parse_mode='HTML')

    # Use a single session for the entire operation.
    # DefaultResolver is used to avoid aiodns issues, and use_dns_cache is disabled for robustness.
    connector = aiohttp.TCPConnector(resolver=aiohttp.DefaultResolver(), use_dns_cache=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        user_error_message = None
        try:
            media_list = None
            error_msg = None
 
            # --- Argument & Limit Parsing ---
            limit = 1
            is_multi_request = False
            if limit_arg:
                try:
                    parsed_limit = int(limit_arg)
                    if 1 <= parsed_limit <= 10:
                        limit = parsed_limit
                        if limit > 1:
                            is_multi_request = True
                    else:
                        error_msg = "Limit must be between 1 and 10."
                except (ValueError, IndexError):
                    error_msg = "Invalid limit provided. Please use a number."
 
            if not error_msg:
                # --- API Selection & Fetching with Retry ---
                eligible_apis = [
                    (name, api_data) for name, api_data in API_DISPATCHER.items() if category in api_data["cats"]
                ]
 
                if not eligible_apis:
                    error_msg = f"Unknown category `{category}`."
                else:
                    if is_multi_request:
                        apis_with_limit = [api for api in eligible_apis if api[1].get("has_limit")]
                        if apis_with_limit:
                            eligible_apis = apis_with_limit
                        else:
                            error_msg = f"No API for category `{category}` supports fetching multiple images."
                    
                    if tags and not error_msg:
                        apis_with_tags = [api for api in eligible_apis if api[1].get("has_tags")]
                        if apis_with_tags:
                            eligible_apis = apis_with_tags
                        else:
                            error_msg = f"No API for category `{category}` supports additional tags."
 
                if not error_msg:
                    random.shuffle(eligible_apis) # Try APIs in a random order
                    api_name = None # To store the name of the successful API
                    for name, selected_api in eligible_apis:
                        fetcher = selected_api["fetcher"]
                        api_category = category.replace('_', '-') if selected_api.get("hyphenated") else category
                        
                        media_list, attempt_error_msg = await fetcher(session, api_category, limit, tags)
                        
                        if media_list:
                            api_name = name
                            error_msg = None 
                            break
                        elif attempt_error_msg:
                            logger.warning(f"API '{name}' failed for category '{category}': {attempt_error_msg}")
                            error_msg = attempt_error_msg
 
            if not error_msg and not media_list:
                error_msg = f"No media found for `{category}`."

            # Add the API source to the caption if the fetch was successful
            if not error_msg and media_list:
                # Map internal API names to user-friendly display names
                api_display_names = {
                    "picre": "pic.re",
                    "nekosapi": "nekosapi.com",
                    "nekoslife": "nekos.life",
                    "nekosbest": "nekos.best",
                    "waifupics": "waifu.pics",
                    "nekosia": "nekosia.cat",
                    "nekobot": "nekobot.xyz",
                    "nekosmoe": "nekos.moe",
                    "waifuim": "waifu.im",
                    "anyanime": "any-anime-api.vercel.app",
                }
                display_name = api_display_names.get(api_name, api_name)
                api_source_text = f"\n\n<i>via {display_name}</i>"

                for item in media_list:
                    # Append the source text to the existing caption or set it as the caption
                    item['caption'] = (item.get('caption', '') + api_source_text).lstrip()

            if error_msg:
                raise ValueError(error_msg)

            await status_msg.delete()
            status_msg = None  # Mark as deleted to prevent editing in the final except block

            # --- Download all media and categorize ---
            photos_to_send = []
            animations_to_send = []
            for media_item in media_list:
                image_url = media_item["url"]
                try:
                    async with session.get(image_url, timeout=30) as resp:
                        if not resp.ok:
                            logger.error(f"Failed to download media for '{category}' from URL {image_url}: HTTP {resp.status}")
                            continue
                        
                        image_content = await resp.read()
                        content_type = resp.headers.get('Content-Type', '').lower()
                        
                        item_data = {"content": image_content, "caption": media_item["caption"], "url": image_url, "content_type": content_type}
                        if 'gif' in content_type or image_url.lower().endswith((".gif", ".gifv")):
                            animations_to_send.append(item_data)
                        else:
                            photos_to_send.append(item_data)
                except Exception as download_error:
                    logger.error(f"Failed to download media for '{category}' from URL {image_url}: {download_error}")
                    await message.reply_text(f"Gagal mengunduh salah satu item untuk <code>{category}</code>.", parse_mode='HTML')
 
            # --- Sending Logic ---
            if send_as_doc:
                all_media_to_send = photos_to_send + animations_to_send
                
                for i, doc_item in enumerate(all_media_to_send):
                    try:
                        # Use caption only for the first item
                        caption_to_send = doc_item["caption"] if i == 0 else None
                        
                        filename = doc_item['url'].split('/')[-1].split('?')[0]
                        if not filename or '.' not in filename:
                            # Create a fallback filename if it's missing or has no extension
                            ext = 'gif' if 'gif' in doc_item['content_type'] else 'jpg'
                            filename = f"media_{i}.{ext}"

                        await message.reply_document(
                            document=doc_item["content"], 
                            caption=caption_to_send,
                            parse_mode='HTML' if caption_to_send else None,
                            filename=filename, 
                            message_thread_id=message.message_thread_id, 
                            write_timeout=600
                        )
                    except Exception as e:
                        logger.error(f"Failed to send item as document from URL {doc_item['url']}: {e}")
                        await message.reply_text(f"Gagal mengirim salah satu item sebagai dokumen.", parse_mode='HTML')
            else:
                # --- Send Photos ---
                PHOTO_SIZE_LIMIT = 10 * 1024 * 1024  # 10 MB
                small_photos = [p for p in photos_to_send if len(p["content"]) <= PHOTO_SIZE_LIMIT]
                large_photos_as_docs = [p for p in photos_to_send if len(p["content"]) > PHOTO_SIZE_LIMIT]
    
                if len(small_photos) > 1:
                    media_group = []
                    # The first item in the album gets the caption.
                    first_photo = small_photos[0]
                    media_group.append(InputMediaPhoto(media=first_photo["content"], caption=first_photo["caption"], parse_mode='HTML'))
                    
                    # Add the rest of the photos without captions.
                    for p in small_photos[1:]:
                        media_group.append(InputMediaPhoto(media=p["content"]))
                    
                    for i in range(0, len(media_group), 10):
                        chunk = media_group[i:i+10]
                        await message.reply_media_group(media=chunk, message_thread_id=message.message_thread_id)
                elif len(small_photos) == 1:
                    photo_item = small_photos[0]
                    try:
                        await message.reply_photo(photo=photo_item["content"], caption=photo_item["caption"], parse_mode='HTML', message_thread_id=message.message_thread_id)
                    except Exception as photo_error:
                        error_str = str(photo_error).lower()
                        if "invalid_dimensions" in error_str: # 'too big' is handled by the size check above
                            logger.warning(f"Photo send failed ({photo_error}), falling back to document: {photo_item['url']}")
                            filename = photo_item['url'].split('/')[-1]
                            await message.reply_document(document=photo_item["content"], caption=photo_item["caption"], parse_mode='HTML', filename=filename, message_thread_id=message.message_thread_id)
                        else:
                            raise photo_error
    
                # Send large photos individually as documents
                for doc_item in large_photos_as_docs:
                    try:
                        logger.warning(f"Photo is too large ({len(doc_item['content'])} bytes), sending as document: {doc_item['url']}")
                        filename = doc_item['url'].split('/')[-1]
                        await message.reply_document(document=doc_item["content"], caption=doc_item["caption"], parse_mode='HTML', filename=filename, message_thread_id=message.message_thread_id, write_timeout=600)
                    except Exception as e:
                        logger.error(f"Failed to send large photo as document from URL {doc_item['url']}: {e}")

                # --- Send Animations (one by one) ---
                for anim_item in animations_to_send:
                    try:
                        await message.reply_animation(animation=anim_item["content"], caption=anim_item["caption"], parse_mode='HTML', message_thread_id=message.message_thread_id)
                    except Exception as e:
                        logger.error(f"Failed to send animation for '{category}' from URL {anim_item['url']}: {e}")
                        await message.reply_text(f"Gagal mengirim salah satu animasi untuk <code>{category}</code>.", parse_mode='HTML')

        except aiohttp.ClientConnectorDNSError as e:
            logger.error(f"DNS error for '{category}': {e}", exc_info=True)
            user_error_message = "A DNS error occurred. The bot could not resolve the API's address. This might be a temporary network issue."
        except Exception as e:
            if isinstance(e, ValueError):
                # "Known" errors from API logic, message is safe for users
                user_error_message = str(e).replace('`', '<code>', 1).replace('`', '</code>', 1)
                logger.warning(f"Controlled error for '{category}': {e}")
            else:
                # Unexpected errors
                logger.error(f"Unexpected error for '{category}': {e}", exc_info=True)
                user_error_message = "An unexpected error occurred."

        if user_error_message:
            final_text = f"<b>Error:</b> {user_error_message}"

            if status_msg:
                await status_msg.edit_text(final_text, parse_mode='HTML')
            else:
                await message.reply_text(final_text, parse_mode='HTML')