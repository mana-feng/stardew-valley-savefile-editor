# Provide reusable UI helpers, shared constants, and input validation utilities.
import tkinter as tk

DEFAULT_WEATHER_TOMORROW_OPTIONS = [

    "Sun",

    "Rain",

    "GreenRain",

    "Wind",

    "Storm",

    "Festival",

    "Snow",

    "Wedding",

]

# Bind consistent mouse-wheel behavior for the provided scrollable widgets.
# It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
def setup_mousewheel(widget):

    # Scroll the widget when the pointer wheel is used over it.
    # It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
    def _on_mousewheel(event):

        try:

            if not widget.winfo_exists():

                return

            try:

                target = widget.winfo_containing(event.x_root, event.y_root)

            except (tk.TclError, KeyError):

                return

            if not target:

                return

            current = target

            while current is not None and current != widget:

                current = current.master

            if current != widget:

                return

            if event.delta != 0:

                if event.state & 0x1:

                    if event.delta > 0:

                        if widget.xview()[0] <= 0: return

                    else:

                        if widget.xview()[1] >= 1: return

                    widget.xview_scroll(int(-2 * (event.delta / 120)), "units")

                else:

                    if event.delta > 0:

                        if widget.yview()[0] <= 0: return

                    else:

                        if widget.yview()[1] >= 1: return

                    widget.yview_scroll(int(-3 * (event.delta / 120)), "units")

        except (tk.TclError, AttributeError, KeyError):

            pass

    widget.bind_all("<MouseWheel>", _on_mousewheel, add=True)

# Center the window on the active display.
# It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
def center_window(window, width, height):

    window.withdraw()

    window.update_idletasks()

    screen_width = window.winfo_screenwidth()

    screen_height = window.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)

    y = (screen_height // 2) - (height // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")

    window.deiconify()

# Restrict a text variable to numeric input within the configured bounds.
# It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
def bind_numeric_input_limit(var, max_value=None, min_value=None, allow_negative=False):

    # Normalize the numeric input after each edit.
    # It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
    def _on_change(*_args):

        raw = var.get()

        if raw == "":

            return

        sign = ""

        body = raw

        if allow_negative and body.startswith("-"):

            sign = "-"

            body = body[1:]

        digits = "".join(ch for ch in body if ch.isdigit())

        if not digits:

            if allow_negative and sign and min_value is not None and min_value < 0:

                cleaned = str(min_value)

            else:

                cleaned = ""

            if cleaned != raw:

                var.set(cleaned)

            return

        cleaned = f"{sign}{digits}"

        value = int(cleaned)

        if min_value is not None and value < min_value:

            cleaned = str(min_value)

        if max_value is not None and value > max_value:

            cleaned = str(max_value)

        if cleaned != raw:

            var.set(cleaned)

    return var.trace_add("write", _on_change)

# Restrict a text variable to floating-point input within the configured bounds.
# It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
def bind_float_input_limit(var, max_value=None, min_value=None, allow_negative=True):

    # Normalize the floating-point input after each edit.
    # It keeps Tk widgets, view state, and user actions synchronized for the active interface flow.
    def _on_change(*_args):

        raw = var.get().strip()

        if raw == "":

            return

        cleaned_chars = []

        dot_seen = False

        sign_allowed = allow_negative and (min_value is None or min_value < 0)

        for ch in raw:

            if ch.isdigit():

                cleaned_chars.append(ch)

            elif ch == "." and not dot_seen:

                if not cleaned_chars or cleaned_chars == ["-"]:

                    cleaned_chars.append("0")

                cleaned_chars.append(".")

                dot_seen = True

            elif ch == "-" and sign_allowed and not cleaned_chars:

                cleaned_chars.append("-")

        cleaned = "".join(cleaned_chars)

        if cleaned in {"", "-", "0.", "-0."}:

            if cleaned != raw:

                var.set(cleaned)

            return

        try:

            value = float(cleaned)

        except ValueError:

            if cleaned != raw:

                var.set(cleaned)

            return

        if min_value is not None and value < min_value:

            cleaned = f"{min_value:g}"

        if max_value is not None and value > max_value:

            cleaned = f"{max_value:g}"

        if cleaned != raw:

            var.set(cleaned)

    return var.trace_add("write", _on_change)
