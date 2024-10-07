import threading


class CallbackThread(threading.Thread):
    def __init__(self, callback, *args, **kwargs):
        target = kwargs.pop('target')
        super(CallbackThread, self).__init__(*args, **kwargs)
        self.callback = callback
        self.method = target
        self.method_args = kwargs.pop('args')

    def run(self):
        self.method(*self.method_args)
        if self.callback is not None:
            self.callback()
