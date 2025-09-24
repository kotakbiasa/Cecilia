import re
import requests
import logging

logger = logging.getLogger(__name__)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}

def get_download_link(url: str) -> dict:
    """
    Mendapatkan direct download link dari URL Terabox.
    """
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # Kunjungi URL awal untuk mendapatkan cookies dan resolusi redirect
        res = session.get(url, allow_redirects=True)
        
        # Ekstrak shorturl dari URL final
        match = re.search(r'surl=([a-zA-Z0-9_-]+)', res.url)
        if not match:
            logger.error("Gagal mengekstrak shorturl dari URL Terabox.")
            return {'status': 'failed', 'message': 'Shorturl tidak ditemukan.'}
        
        surl = match.group(1)
        
        # Dapatkan informasi file dari API
        api_url = f'https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl={surl}&root=1'
        api_res = session.get(api_url)
        api_res.raise_for_status()
        api_data = api_res.json()

        if api_data.get('errno') != 0:
            logger.error(f"API shorturlinfo mengembalikan error: {api_data}")
            return {'status': 'failed', 'message': 'Gagal mendapatkan info file dari API.'}

        if not api_data.get('list'):
            return {'status': 'failed', 'message': 'Tidak ada file yang ditemukan di link ini.'}

        # Ambil file pertama dari daftar
        file_info = api_data['list'][0]
        fs_id = file_info['fs_id']

        # Dapatkan jsToken dan browserid dari halaman wap
        wap_url = f'https://www.terabox.app/wap/share/filelist?surl={surl}'
        wap_res = session.get(wap_url)
        js_token_match = re.search(r'var\s+jsToken\s*=\s*"([^"]+)"', wap_res.text)
        if not js_token_match:
            logger.error("Gagal mendapatkan jsToken dari halaman WAP.")
            return {'status': 'failed', 'message': 'Gagal mendapatkan token otorisasi.'}
        js_token = js_token_match.group(1)

        # Siapkan parameter untuk mendapatkan link unduhan
        params = {
            'app_id': '250528',
            'web': '1',
            'channel': 'dubox',
            'clienttype': '0',
            'jsToken': js_token,
            'dplogid': '', # dp-logid bisa dikosongkan
            'shorturl': surl,
            'root': '1',
            'fid_list': f'[{fs_id}]'
        }

        download_api_url = 'https://www.terabox.com/api/download'
        download_res = session.get(download_api_url, params=params)
        download_res.raise_for_status()
        download_data = download_res.json()

        if download_data.get('errno') != 0:
            logger.error(f"API download mengembalikan error: {download_data}")
            return {'status': 'failed', 'message': 'Gagal mendapatkan link unduhan dari API.'}

        download_link = download_data.get('dlink')
        if not download_link:
            return {'status': 'failed', 'message': 'Link unduhan tidak ditemukan dalam respons API.'}

        # Lakukan HEAD request untuk mendapatkan URL final (resolusi redirect)
        final_link_res = session.head(download_link, allow_redirects=True)
        final_link = final_link_res.url

        result = {
            'status': 'success',
            'file_name': file_info.get('server_filename', 'N/A'),
            'size': file_info.get('size', 0),
            'download_link': final_link
        }
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Terjadi error request saat memproses URL Terabox: {e}")
        return {'status': 'failed', 'message': f'Error jaringan: {e}'}
    except Exception as e:
        logger.error(f"Terjadi error tidak terduga di Terabox API: {e}", exc_info=True)
        return {'status': 'failed', 'message': f'Error tidak terduga: {e}'}
    finally:
        session.close()
        