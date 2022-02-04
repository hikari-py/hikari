`enable_signal_handlers` now only defaults to `True` when the run/start method is called in the main thread.
This avoids these functions from always raising when being run in a threaded environment as only the main thread can register signal handlers.
