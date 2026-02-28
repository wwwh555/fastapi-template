from starlette import status
class CustomException(Exception):

    def __init__(
            self,
            msg: str,
            code: int = status.HTTP_400_BAD_REQUEST,
            status_code: int = status.HTTP_200_OK,
            desc: str = None
    ):
        self.msg = msg
        self.code = code
        self.status_code = status_code
        self.desc = desc
