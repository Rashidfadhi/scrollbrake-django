import os
import time
import threading
from collections import deque
from plyer import notification

import django
import pygetwindow as gw
from pynput import mouse

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scrollbrake.settings")
django.setup()

from datetime import datetime
from django.utils import timezone
from django.db.models import Sum


from django.contrib.auth import get_user_model
from scrollapp.models import ScrollSession, BreakEvent, UserGoal
from django.contrib.auth.models import User


# Configuration
INACTIVITY_LIMIT = 2.0
ROLLING_WINDOW = 10.0

# Break settings
SCROLL_LIMIT_SECONDS = 10  # 20 minutes
BREAK_DURATION_SECONDS = 5

# Overall statistics
total_scrolls = 0
total_active_seconds = 0.0

# Per-app active scrolling time
app_active_seconds = {
    "YouTube": 0.0,
    "Instagram": 0.0,
    "Reddit": 0.0,
}

# Per-app timing
last_app_scroll_time = {}
app_break_until = {}

# Current session
session_start = None
last_scroll_time = None
session_scrolls = 0
session_app_name = "Other"

# Recent scroll timestamps
recent_scrolls = deque()
lock = threading.Lock()

daily_goal_notified_date = None


def notify_daily_goal_reached(total_minutes, goal_minutes):
    global daily_goal_notified_date

    today = timezone.localdate()

    if daily_goal_notified_date == today:
        return

    try:
        notification.notify(
            title="ScrollBrake — Daily Goal Reached",
            message=(
                f"You've scrolled for {total_minutes:.1f} minutes today. "
                f"Your daily goal is {goal_minutes} minutes."
            ),
            app_name="ScrollBrake",
            timeout=10,
        )

        daily_goal_notified_date = today

    except Exception as error:
        print(f"\nDaily goal notification failed: {error}")


def get_active_window_title():
    """Return the active window title."""
    try:
        window = gw.getActiveWindow()
        if window and window.title:
            return window.title
        return "Unknown"
    except Exception:
        return "Unknown"


def detect_app_name():
    """Identify supported apps from the active window title."""
    title = get_active_window_title().lower()

    if "youtube" in title:
        return "YouTube"
    if "instagram" in title:
        return "Instagram"
    if "reddit" in title:
        return "Reddit"
    return "Other"


def close_supported_app_window(app_name):
    """Close the active window only if it belongs to the target app."""
    try:
        window = gw.getActiveWindow()

        if not window or not window.title:
            return False

        title = window.title.lower()

        app_keywords = {
            "YouTube": "youtube",
            "Instagram": "instagram",
            "Reddit": "reddit",
        }

        keyword = app_keywords.get(app_name)

        if keyword and keyword in title:
            window.close()
            return True

        return False

    except Exception as error:
        print(f"Could not close {app_name} window: {error}")
        return False

def save_session(app_name, duration, scroll_count, momentum):
    """Save a completed session to Django."""
    try:
        User = get_user_model()

        DETECTOR_USERNAME = os.getenv("SCROLLBRAKE_USERNAME", "rashid")

        user = User.objects.get(username=DETECTOR_USERNAME)

        session = ScrollSession.objects.create(
            user=user,
            app_name=app_name,
            duration=max(1, round(duration)),
            scroll_count=scroll_count,
            momentum=momentum,
        )

        print(f"\nSaved session! Database ID: {session.id}")

    except User.DoesNotExist:
        print("\nError: Django user 'rashid' was not found.")
    except Exception as error:
        print(f"\nError saving session: {error}")


def check_daily_goal():
    """Check whether the selected user's saved daily goal is reached."""
    try:
        User = get_user_model()
        user = User.objects.get(username=DETECTOR_USERNAME)

        goal = UserGoal.objects.filter(user=user).first()

        if goal is None:
            return

        today = timezone.localdate()

        total_seconds = ScrollSession.objects.filter(
            user=user,
            created_at__date=today,
        ).aggregate(total=Sum("duration"))["total"] or 0

        total_minutes = total_seconds / 60

        if total_minutes >= goal.daily_limit_minutes:
            print(
                f"\nDaily scrolling goal reached: "
                f"{total_minutes:.1f} / "
                f"{goal.daily_limit_minutes} minutes"
            )

    except Exception as error:
        print(f"\nDaily goal check failed: {error}")


def save_break_event(app_name):
    """Save a triggered break to Django."""
    try:
        User = get_user_model()

        DETECTOR_USERNAME = os.getenv("SCROLLBRAKE_USERNAME", "rashid")

        user = User.objects.get(username=DETECTOR_USERNAME)

        event = BreakEvent.objects.create(
            user=user,
            app_name=app_name,
            duration=BREAK_DURATION_SECONDS,
        )

        print(f"\nBreak event saved! Database ID: {event.id}")

    except User.DoesNotExist:
        print("\nError: Django user 'rashid' was not found.")
    except Exception as error:
        print(f"\nError saving break event: {error}")


def show_break_notification(app_name):
    """Show a desktop notification when a break starts."""
    try:
        notification.notify(
            title="ScrollBrake — Time for a Break!",
            message=(
                f"You've reached your scrolling limit for {app_name}. "
                f"Take a {BREAK_DURATION_SECONDS}-second break."
            ),
            app_name="ScrollBrake",
            timeout=10,
        )
    except Exception as error:
        print(f"\nDesktop notification failed: {error}")


def finish_session(now):
    """Save the current scrolling session."""
    global session_start, last_scroll_time
    global session_scrolls, total_active_seconds, session_app_name

    if (
        session_start is None
        or last_scroll_time is None
        or session_scrolls == 0
    ):
        return

    duration = max(0.0, last_scroll_time - session_start)
    average_rate = session_scrolls / duration * 60 if duration > 0 else 0

    if average_rate >= 50:
        momentum = "HIGH"
    elif average_rate >= 20:
        momentum = "MEDIUM"
    else:
        momentum = "LOW"

    save_session(
        app_name=session_app_name,
        duration=duration,
        scroll_count=session_scrolls,
        momentum=momentum,
    )

    total_active_seconds += duration

    print(
        f"\nSession ended | App: {session_app_name} | "
        f"Events: {session_scrolls} | "
        f"Duration: {duration:.2f}s | "
        f"Total events: {total_scrolls}"
    )

    session_start = None
    last_scroll_time = None
    session_scrolls = 0
    session_app_name = "Other"



def check_break_limit(app_name, now):
    """Start a break when the app reaches its active-time limit."""
    if app_name not in app_active_seconds:
        return

    break_until = app_break_until.get(app_name)

    if break_until is not None:
        if now < break_until:
            return

        del app_break_until[app_name]
        app_active_seconds[app_name] = 0.0
        last_app_scroll_time.pop(app_name, None)

        print(f"\n{app_name} break finished. Monitoring resumed!")
        return

    if app_active_seconds[app_name] >= SCROLL_LIMIT_SECONDS:
        if session_app_name == app_name and session_start is not None:
            finish_session(now)

        closed = close_supported_app_window(app_name)

        app_break_until[app_name] = now + BREAK_DURATION_SECONDS
        save_break_event(app_name)
        show_break_notification(app_name)
        last_app_scroll_time.pop(app_name, None)

        if closed:
            print(f"\n{app_name} window closed because its time limit was reached.")
        else:
            print(f"\nCould not safely close the {app_name} window.")

        print(f"Take a {BREAK_DURATION_SECONDS}-second break.")



def monitor_breaks():
    """Update break countdowns and resume monitoring automatically."""
    last_displayed = {}

    while True:
        time.sleep(1)
        now = time.monotonic()

        with lock:
            for app_name, break_until in list(app_break_until.items()):
                remaining = max(0, int(break_until - now + 0.99))

                if remaining <= 0:
                    del app_break_until[app_name]
                    app_active_seconds[app_name] = 0.0
                    last_app_scroll_time.pop(app_name, None)
                    last_displayed.pop(app_name, None)

                    print(
                        f"\n{app_name} break finished. "
                        "Monitoring resumed!"
                    )
                elif last_displayed.get(app_name) != remaining:
                    print(
                        f"\r{app_name} break: {remaining}s remaining ",
                        end="",
                        flush=True,
                    )
                    last_displayed[app_name] = remaining


def on_scroll(x, y, dx, dy):
    global total_scrolls, session_scrolls, session_app_name
    global session_start, last_scroll_time

    now = time.monotonic()
    current_app_name = detect_app_name()

    # Keep the current break state and active-time calculation together.
    with lock:
        if current_app_name in app_active_seconds:
            # Do not count scrolls during an app's break.
            check_break_limit(current_app_name, now)

            break_until = app_break_until.get(current_app_name)
            if break_until is not None and now < break_until:
                return

            previous_time = last_app_scroll_time.get(current_app_name)

            if previous_time is not None:
                gap = now - previous_time

                # Count only short gaps between scroll events.
                if 0 < gap <= INACTIVITY_LIMIT:
                    app_active_seconds[current_app_name] += gap
                    print(
                        f"\n[DEBUG] App: {current_app_name} | "
                        f"Active time: {app_active_seconds[current_app_name]:.2f}s | "
                        f"Limit: {SCROLL_LIMIT_SECONDS}s"
                    )

            last_app_scroll_time[current_app_name] = now

            # Check again after updating the active time.
            check_break_limit(current_app_name, now)

            break_until = app_break_until.get(current_app_name)
            if break_until is not None and now < break_until:
                return

        print(f"\nActive window: {get_active_window_title()}")

        # Start a new session after inactivity or an app switch.
        if (
            last_scroll_time is None
            or now - last_scroll_time > INACTIVITY_LIMIT
            or current_app_name != session_app_name
        ):
            if session_start is not None:
                finish_session(now)

            session_start = now
            session_app_name = current_app_name
            session_scrolls = 0

        total_scrolls += 1
        session_scrolls += 1
        last_scroll_time = now

        recent_scrolls.append(now)

        while recent_scrolls and now - recent_scrolls[0] > ROLLING_WINDOW:
            recent_scrolls.popleft()

        elapsed = min(
            ROLLING_WINDOW,
            now - recent_scrolls[0] + 0.1,
        )
        speed = len(recent_scrolls) / max(elapsed, 1.0) * 60

        window_filled = now - recent_scrolls[0] >= ROLLING_WINDOW
        window_status = "10s window" if window_filled else "Warming up"

        if speed < 20:
            momentum = "LOW"
        elif speed < 50:
            momentum = "MEDIUM"
        else:
            momentum = "HIGH"

        print(
            f"\rTotal events: {total_scrolls} | "
            f"Session events: {session_scrolls} | "
            f"App: {session_app_name} | "
            f"Rate: {speed:.1f}/min ({window_status}) | "
            f"Momentum: {momentum}",
            end="",
            flush=True,
        )


def monitor_inactivity():
    while True:
        time.sleep(0.2)
        now = time.monotonic()

        with lock:
            if (
                session_start is not None
                and last_scroll_time is not None
                and now - last_scroll_time > INACTIVITY_LIMIT
            ):
                finish_session(now)


def main():
    print("ScrollBrake detector started!")
    print("Scroll to test. Press Ctrl+C to stop.")
    print(
        f"Break limit: {SCROLL_LIMIT_SECONDS} seconds "
        f"({SCROLL_LIMIT_SECONDS / 60:.2f} minutes); "
        f"break duration: {BREAK_DURATION_SECONDS} seconds."
    )

    threading.Thread(
        target=monitor_inactivity,
        daemon=True,
    ).start()
    threading.Thread(
    target=monitor_breaks,
    daemon=True,
    ).start()

    try:
        with mouse.Listener(on_scroll=on_scroll) as listener:
            listener.join()

    except KeyboardInterrupt:
        with lock:
            if session_start is not None:
                finish_session(time.monotonic())

        print("\nDetector stopped.")
        print(f"Total scroll events: {total_scrolls}")
        print(f"Approx. session time: {total_active_seconds:.2f} seconds")


if __name__ == "__main__":
    main()
