# ScrollBrake 2.0

**A Django-based Digital Behavior Monitoring and Scrolling Analytics System**

ScrollBrake is a Python and Django project designed to monitor scrolling activity, analyze usage patterns, and encourage healthier digital habits through break reminders and usage limits.

## Features

- Track scrolling sessions and duration.
- Count scroll events and classify scrolling momentum.
- View activity statistics on a dashboard.
- Monitor daily usage goals.
- Trigger break reminders after reaching configured app usage limits.
- Maintain session and break history.
- Support multiple user accounts with user-specific records.

## Technologies Used

- Python
- Django
- HTML and CSS
- SQLite or MySQL, depending on configuration
- `pynput` for mouse-scroll monitoring
- `pygetwindow` for active-window detection
- `plyer` for desktop notifications

## Getting Started

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install the project's dependencies.
4. Configure the database and Django settings.
5. Apply database migrations.
6. Start the Django development server.
7. Run the scrolling detector in a separate terminal.

## Privacy

ScrollBrake is designed to keep activity records associated with individual user accounts. Configure credentials securely and avoid publishing private database details or local user data.

## Project Status

Core dashboard, scrolling detection, session tracking, and break intervention features have been implemented and tested locally.

## Author

Rashid