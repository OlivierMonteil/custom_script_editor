def run_after_event(new_method, target_method):
    def run_both(*args, **kwargs):
        target_method(*args, **kwargs)
        new_method(*args, **kwargs)

    return run_both

def run_before_event(new_method, target_method):
    def run_both(*args, **kwargs):
        new_method(*args, **kwargs)
        target_method(*args, **kwargs)

    return run_both
