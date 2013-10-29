
class MoneyModelFormError(Exception):
    pass


class InvalidMoneyFieldCurrency(MoneyModelFormError):
    pass