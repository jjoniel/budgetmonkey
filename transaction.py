
class Transaction:
    """
    This class represents a single transaction made by the user of the
    tracker and the associated details.

    Attributes:
    - net (int) : total monetary expense/inflow
    - vendor (str) : the vendor associated with the transaction
    - date (datetime.date) : the data of the transaction

    """
    def __init__(self, net, vendor, date):
        """
        The constructor creates a transaction object with a net value,
        an associated vendor, and a justifying description

        Attributes:
        - net (float) : total monetary expense/inflow
        - vendor (str) : the vendor associated with the transaction
        - date (datetime.date) : the data of the transaction

        """
        self.net = net
        self.vendor = vendor
        self.date = date

    def __str__(self):
        return (
            f"${self.net:>7.2f}  {self.vendor:<7}" 
        )

    def datestr(self):
        return (
            f"{self.date}  ${self.net:>7.2f}  {self.vendor:<7}"
        )

    def csv(self):
        return (
            f"{self.net},{self.vendor},{self.date.year},{self.date.month},{self.date.day}"
        )

    def __lt__(self, other):
        if self.date.year < other.date.year:
            return True
        if self.date.year > other.date.year:
            return False
        else:
            if self.date.month < other.date.month:
                return True
            if self.date.month > other.date.month:
                return False
            else:
                if self.date.day < other.date.day:
                    return True
                if self.date.day > other.date.day:
                    return False
                else:
                    return self.vendor < other.vendor
