class RankingsAPIError(Exception):
    """This exception catches errors in the RankingsAPI"""

    def __init__(self, message = "RankingsAPI default error"):
            self.message = message
            super().__init__(self.message)