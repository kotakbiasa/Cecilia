import asyncio
import aiohttp
import random

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from bot import logger, config
from bot.modules.nsfwimg_api import (
    NEKOBOT_NSFW, WAIFUIM_NSFW, WAIFUPICS_NSFW, NEKOSAPI_NSFW,
    fetch_nekobot_nsfw, fetch_waifu_im_nsfw, fetch_waifu_pics_nsfw, fetch_nekosapi_nsfw
)
from telegram import InputMediaPhoto

# Dispatcher for NSFW APIs
API_DISPATCHER_NSFW = {
    "nekobot": {"cats": NEKOBOT_NSFW, "fetcher": fetch_nekobot_nsfw, "has_limit": True},
    "waifuim": {"cats": WAIFUIM_NSFW, "fetcher": fetch_waifu_im_nsfw, "hyphenated": True, "has_limit": True},
    "waifupics": {"cats": WAIFUPICS_NSFW, "fetcher": fetch_waifu_pics_nsfw, "has_limit": True},
    "nekosapi": {"cats": NEKOSAPI_NSFW, "fetcher": fetch_nekosapi_nsfw, "has_limit": True},
}

async def func_nsfwimg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles NSFW image categories."""
    message = update.effective_message
    chat = update.effective_chat
    user_id = update.effective_user.id

    # --- Permission & Safety Checks ---
    sudo_users = getattr(config, 'sudo_users', [])
    if user_id != config.owner_id and user_id not in sudo_users:
        await message.reply_text("Anda tidak memiliki izin untuk menggunakan perintah ini.")
        return

    if chat.type != ChatType.PRIVATE:
        await message.reply_text("Perintah ini hanya dapat digunakan dalam obrolan pribadi untuk alasan keamanan.")
        return

    if not context.args:
        # Show help message for NSFW commands
        help_text_parts = [
            "Gunakan perintah dengan salah satu kategori yang tersedia.\n\n",
            "<b>Contoh:</b>\n<code>/nsfwimg ass</code>\n<code>/nsfwimg pussy 5</code> (kirim 5 gambar)\n<code>/nsfwimg hentai doc</code> (kirim sebagai dokumen)\n\n",
            "<b>PERINGATAN:</b> Konten ini bersifat eksplisit.\n",
            "<b>Kategori yang tersedia berdasarkan API:</b>"
        ]

        api_sources = {
            "nekobot.xyz": NEKOBOT_NSFW,
            "waifu.im": WAIFUIM_NSFW,
            "waifu.pics": WAIFUPICS_NSFW,
            "nekosapi.com": NEKOSAPI_NSFW,
        }

        for api_name, cats in api_sources.items():
            if not cats: continue
            sorted_cats = sorted(list(cats))
            category_list_str = " ".join(f"<code>{cat}</code>" for cat in sorted_cats)
            help_text_parts.append(f"\n\n<b>{api_name}</b>:\n<blockquote>{category_list_str}</blockquote>")

        await message.reply_text("".join(help_text_parts), parse_mode='HTML', disable_web_page_preview=True)
        return
    
    # --- Argument Parsing ---
    category = context.args[0].lower()
    remaining_args = list(context.args[1:])
    send_as_doc = False
    limit_arg = None

    if 'doc' in remaining_args:
        send_as_doc = True
        remaining_args.remove('doc')
    if '-d' in remaining_args:
        send_as_doc = True
        remaining_args.remove('-d')

    if remaining_args and remaining_args[0].isdigit():
        limit_arg = remaining_args[0]

    status_msg = await message.reply_text(f"<i>Mencari gambar NSFW untuk <code>{category}</code>...</i>", parse_mode='HTML')

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
                # --- API Selection ---
                eligible_apis = [
                    (name, api_data) for name, api_data in API_DISPATCHER_NSFW.items() if category in api_data["cats"]
                ]
 
                if not eligible_apis:
                    error_msg = f"Kategori NSFW tidak diketahui: `{category}`."
                else:
                    if is_multi_request:
                        apis_with_limit = [api for api in eligible_apis if api[1].get("has_limit")]
                        if apis_with_limit:
                            eligible_apis = apis_with_limit
                        else:
                            error_msg = f"No API for category `{category}` supports fetching multiple images."
 
                if not error_msg:
                    random.shuffle(eligible_apis) # Try APIs in a random order
                    api_name = None # To store the name of the successful API
                    for name, selected_api in eligible_apis:
                        fetcher = selected_api["fetcher"]
                        api_category = category.replace('_', '-') if selected_api.get("hyphenated") else category
                        
                        media_list, attempt_error_msg = await fetcher(session, api_category, limit)
                        
                        if media_list:
                            api_name = name
                            error_msg = None 
                            break
                        elif attempt_error_msg:
                            logger.warning(f"API '{name}' failed for NSFW category '{category}': {attempt_error_msg}")
                            error_msg = attempt_error_msg

            if not error_msg and not media_list:
                error_msg = f"Tidak ada media yang ditemukan untuk `{category}`."

            if not error_msg and media_list:
                api_display_names = {
                    "nekobot": "nekobot.xyz",
                    "waifuim": "waifu.im",
                    "waifupics": "waifu.pics",
                    "nekosapi": "nekosapi.com",
                }
                display_name = api_display_names.get(api_name, api_name)
                api_source_text = f"\n\n<i>via {display_name}</i>"

                for item in media_list:
                    item['caption'] = (item.get('caption', '') + api_source_text).lstrip()

            if error_msg:
                raise ValueError(error_msg)

            await status_msg.delete()
            status_msg = None

            # --- Download all media and categorize ---
            photos_to_send = []
            animations_to_send = []
            for media_item in media_list:
                image_url = media_item["url"]
                try:
                    async with session.get(image_url, timeout=30) as resp:
                        if not resp.ok:
                            logger.error(f"Gagal mengunduh media NSFW untuk '{category}' dari URL {image_url}: HTTP {resp.status}")
                            continue
                        
                        image_content = await resp.read()
                        content_type = resp.headers.get('Content-Type', '').lower()
                        
                        item_data = {"content": image_content, "caption": media_item["caption"], "url": image_url, "content_type": content_type}
                        if 'gif' in content_type or image_url.lower().endswith((".gif", ".gifv")):
                            animations_to_send.append(item_data)
                        else:
                            photos_to_send.append(item_data)
                except Exception as download_error:
                    logger.error(f"Gagal mengunduh media NSFW untuk '{category}' dari URL {image_url}: {download_error}")
                    await message.reply_text(f"Gagal mengirim salah satu item untuk <code>{category}</code>.", parse_mode='HTML')

            # --- Sending Logic ---
            if send_as_doc:
                all_media_to_send = photos_to_send + animations_to_send
                
                for i, doc_item in enumerate(all_media_to_send):
                    try:
                        caption_to_send = doc_item["caption"] if i == 0 else None
                        filename = doc_item['url'].split('/')[-1].split('?')[0]
                        if not filename or '.' not in filename:
                            ext = 'gif' if 'gif' in doc_item['content_type'] else 'jpg'
                            filename = f"media_{i}.{ext}"

                        await message.reply_document(
                            document=doc_item["content"],
                            caption=caption_to_send,
                            parse_mode='HTML' if caption_to_send else None,
                            filename=filename,
                            write_timeout=600
                        )
                    except Exception as e:
                        logger.error(f"Gagal mengirim item NSFW sebagai dokumen dari URL {doc_item['url']}: {e}")
                        await message.reply_text("Gagal mengirim salah satu item sebagai dokumen.", parse_mode='HTML')
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
                        try:
                            await message.reply_media_group(media=chunk)
                        except Exception as e:
                            if "photo_invalid_dimensions" in str(e).lower():
                                logger.warning(f"NSFW Media group failed due to invalid dimensions. Sending one by one. Error: {e}")
                                photo_chunk_data = small_photos[i:i+10]

                                for idx, photo_item in enumerate(photo_chunk_data):
                                    caption_to_send = photo_item["caption"] if i == 0 and idx == 0 else None
                                    try:
                                        await message.reply_photo(photo=photo_item["content"], caption=caption_to_send, parse_mode='HTML' if caption_to_send else None)
                                    except Exception as photo_error:
                                        error_str = str(photo_error).lower()
                                        if "invalid_dimensions" in error_str:
                                            logger.warning(f"NSFW Photo send failed ({photo_error}), beralih ke dokumen: {photo_item['url']}")
                                            filename = photo_item['url'].split('/')[-1].split('?')[0]
                                            if not filename or '.' not in filename:
                                                ext = 'gif' if 'gif' in photo_item['content_type'] else 'jpg'
                                                filename = f"media_{i+idx}.{ext}"
                                            await message.reply_document(document=photo_item["content"], caption=caption_to_send, parse_mode='HTML' if caption_to_send else None, filename=filename, write_timeout=600)
                                        else:
                                            raise photo_error
                            else:
                                raise e
                elif len(small_photos) == 1:
                    photo_item = small_photos[0]
                    try:
                        await message.reply_photo(photo=photo_item["content"], caption=photo_item["caption"], parse_mode='HTML')
                    except Exception as photo_error:
                        error_str = str(photo_error).lower()
                        if "timed out" in error_str or "invalid_dimensions" in error_str: # 'too big' is handled by the size check above
                            logger.warning(f"Gagal mengirim foto NSFW ({photo_error}), beralih ke dokumen: {photo_item['url']}")
                            filename = photo_item['url'].split('/')[-1]
                            await message.reply_document(document=photo_item["content"], caption=photo_item["caption"], parse_mode='HTML', filename=filename)
                        else:
                            raise photo_error
    
                # Send large photos individually as documents
                for doc_item in large_photos_as_docs:
                    try:
                        logger.warning(f"Gagal mengirim foto NSFW karena terlalu besar ({len(doc_item['content'])} bytes), beralih ke dokumen: {doc_item['url']}")
                        filename = doc_item['url'].split('/')[-1]
                        await message.reply_document(document=doc_item["content"], caption=doc_item["caption"], parse_mode='HTML', filename=filename, write_timeout=600)
                    except Exception as e:
                        logger.error(f"Failed to send large NSFW photo as document from URL {doc_item['url']}: {e}")

                # --- Send Animations (one by one) ---
                for anim_item in animations_to_send:
                    try:
                        await message.reply_animation(animation=anim_item["content"], caption=anim_item["caption"], parse_mode='HTML')
                    except Exception as e:
                        logger.error(f"Gagal mengirim animasi NSFW untuk '{category}' dari URL {anim_item['url']}: {e}")
                        await message.reply_text(f"Gagal mengirim salah satu animasi untuk <code>{category}</code>.", parse_mode='HTML')

        except aiohttp.ClientConnectorDNSError as e:
            logger.error(f"DNS error untuk '{category}': {e}", exc_info=True)
            user_error_message = "Terjadi error DNS. Bot tidak dapat menghubungi alamat API."
        except Exception as e:
            if isinstance(e, ValueError):
                user_error_message = str(e).replace('`', '<code>', 1).replace('`', '</code>', 1)
                logger.warning(f"Controlled error untuk '{category}': {e}")
            else:
                logger.error(f"Unexpected error untuk '{category}': {e}", exc_info=True)
                user_error_message = "Terjadi error yang tidak terduga."

        if user_error_message:
            final_text = f"<b>Error:</b> {user_error_message}"
            if status_msg:
                await status_msg.edit_text(final_text, parse_mode='HTML')
            else:
                await message.reply_text(final_text, parse_mode='HTML')