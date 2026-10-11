"""Mock di lfs_plugins.toolbar: solo la parte usata dal plugin."""
calls = []


class _UtilityToolbarController:
    def dispatch(self, action, value):
        calls.append(action)
