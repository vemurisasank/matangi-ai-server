class WorkflowCache:

    _cache = {}

    @staticmethod
    def get(name):

        return WorkflowCache._cache.get(name)

    @staticmethod
    def set(name, workflow):

        WorkflowCache._cache[name] = workflow

    @staticmethod
    def clear():

        WorkflowCache._cache.clear()