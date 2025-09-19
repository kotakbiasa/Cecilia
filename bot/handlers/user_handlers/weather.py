from telegram import Update
from telegram.ext import ContextTypes
from bot.modules.weather import weather_info

async def func_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_message = update.effective_message
    location = " ".join(context.args)

    if not location:
        await effective_message.reply_text("Use <code>/weather location name</code>\nE.g. <code>/weather los angeles</code>")
        return
    
    info = await weather_info(location)
    if not info:
        await effective_message.reply_text("Oops! Something went wrong! (invalid location name? 🤔)")
        return
    
    text = f"""<blockquote><b>Location info</b></blockquote>

<b>City:</b> <code>{info['location']['name']}</code>
<b>Country:</b> <code>{info['location']['country']}</code>
<b>Zone:</b> <code>{info['location']['tz_id']}</code>
<b>Local time:</b> <code>{info['location']['localtime']}</code>

<blockquote><b>Weather info</b></blockquote>

<b>Condition:</b> <code>{info['current']['condition']['text']}</code>
<b>Temp (C):</b> <code>{info['current']['temp_c']}℃</code> <b>feels:</b> <code>{info['current']['feelslike_c']}℃</code>
<b>Temp (F):</b> <code>{info['current']['temp_f']}℉</code> <b>feels:</b> <code>{info['current']['feelslike_f']}℉</code>
<b>Humidity:</b> <code>{info['current']['humidity']}%</code>

<b>Wind:</b> <code>{info['current']['wind_mph']}mph</code> | <code>{info['current']['wind_kph']}kph</code>
<b>Wind (Angle):</b> <code>{info['current']['wind_degree']}°</code>
<b>UV Ray:</b> <code>{info['current']['uv']}</code>

<blockquote><b>Note:</b> ⚠ 8 or higher is harmful for skin!</blockquote>"""

    await effective_message.reply_text(text)
