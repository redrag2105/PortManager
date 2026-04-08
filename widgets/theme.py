class ThemeColors:
    @staticmethod
    def get(is_dark: bool) -> dict:
        return {
            'active': '#a6e3a1' if is_dark else '#40a02b',
            'inactive': '#585b70' if is_dark else '#9ca0b0',
            'port': 'bold #cba6f7' if is_dark else 'bold #1e66f5',
            'pid': '#89b4fa' if is_dark else '#209fb5',
            'name': 'bold' if is_dark else 'bold #4c4f69',
            'edit': '#fab387' if is_dark else '#df8e1d',
            'delete': '#f38ba8' if is_dark else '#d20f39',
            'accent': '#cba6f7' if is_dark else '#1e66f5'
        }
