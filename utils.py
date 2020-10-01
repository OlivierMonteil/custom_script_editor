import sys
import traceback

from custom_script_editor import constants as kk


def catch_error(func):
	def wrap(*args, **kwargs):
		try:
			return func(*args, **kwargs)

		except Exception as e:
			print kk.ERROR_MESSAGE.format(e)
			traceback.print_exc()

	return wrap

def run_after_event(new_method, target_method):
    """
    Wrap both functions into a new one so <new_method> is called after
    <target_method>.

    Usage:
        target_method = run_after_event(new_method, target_method)
    """

    def run_both(*args, **kwargs):
        target_method(*args, **kwargs)
        new_method(*args, **kwargs)

    return run_both

def run_before_event(new_method, target_method):
    """
    Wrap both functions into a new one so <new_method> is called before
    <target_method>.

    Usage:
        target_method = run_after_event(new_method, target_method)
    """
    def run_both(*args, **kwargs):
        new_method(*args, **kwargs)
        target_method(*args, **kwargs)

    return run_both
