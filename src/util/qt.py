import types


def monkeypatch_method(obj, name, fn):
    old_fn = getattr(obj, name)

    def wrapper(self, *args, **kwargs):
        return fn(self, old_fn, *args, **kwargs)
    setattr(obj, name, types.MethodType(wrapper, obj))
