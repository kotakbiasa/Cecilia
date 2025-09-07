import random
import string
import pyzipper
from time import time
from aiohttp import ClientSession, ClientTimeout
from app import logger

class UTILITY:
    @staticmethod
    def createProgressBar(percentValue, barSize=10) -> str:
        """
        :param percentValue: `int`
        :param barSize: `int` default 10
        :returns str: Progress Bar
        """
        emptySymbol = "▱"
        fullSymbol = "▰"

        barFilled = int(barSize * (int(percentValue) / 100))
        barEmpty = int(barSize - barFilled)

        barStr = f"[ {fullSymbol * barFilled}{emptySymbol * barEmpty} ]"
        return barStr
    

    @staticmethod
    def randomString(length: int = 16) -> str:
        """
        Generates a random string with a mix of:
        - hexdigits
        - octdigits
        """
        return "".join(random.choice(string.hexdigits + string.octdigits) for _ in range(length))


    @staticmethod
    def calculator(math) -> tuple[bool, float | int | str]:
        """
        solves normal maths: supported syntax: (+, -, *, /)
        """
        try:
            solved_math = eval(math)
            return True, solved_math
        except Exception as e:
            logger.error(e)
            return False, e
    

    @staticmethod
    async def pingServer(url, timeout=5) -> str:
        """:return str: Server `response time` or `infinite`"""
        try:
            start_time = time()
            async with ClientSession() as session:
                async with session.get(url, timeout=ClientTimeout(timeout)) as response:
                    response_time = int((time() - start_time) * 1000) # converting to ms
                    if response_time > 1000:
                        server_ping = f"{(response_time / 1000):.2f}s"
                    else:
                        server_ping = f"{response_time}ms"
                    return server_ping
        except:
            return "~ infinite ~"
    

    @staticmethod
    def unzipFile(path, password=None):
        """
        :param path: file path or bytes\n
        :returns list: file path list
        """
        EXTRACTION_PATH = "downloads"
        FILEPATH_LIST = []

        try:
            try:
                with pyzipper.AESZipFile(path) as archiveFile:
                    if password: archiveFile.setpassword(password.encode())
                    archiveFile.extractall(EXTRACTION_PATH)
            except:
                with pyzipper.ZipFile(path) as archiveFile:
                    if password: archiveFile.setpassword(password.encode())
                    archiveFile.extractall(EXTRACTION_PATH)
            
            name_list = archiveFile.namelist()
            for i in name_list:
                FILEPATH_LIST.append(f"{EXTRACTION_PATH}/{i}")
            return FILEPATH_LIST
        except Exception as e:
            return e
