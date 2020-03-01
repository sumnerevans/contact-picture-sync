from cps.stores.base import Contact


class PersistentLoginInformation(dict):
    pass


class BaseRetriever:
    def login(
        self,
        cached_login_info: PersistentLoginInformation = None,
    ) -> PersistentLoginInformation:
        raise NotImplementedError('`login` not implemented!')

    def retrieve(self, user: Contact):
        raise NotImplementedError('`retrieve` not implemented!')
