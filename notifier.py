"""Notification system for good deals."""

import logging
from typing import List, Dict
from datetime import datetime
import platform

logger = logging.getLogger(__name__)


class Notifier:
    """
    Notification system for alerting users about good deals.

    Supports multiple notification methods:
    - Console output (always available)
    - Desktop notifications (Windows, macOS, Linux)
    - Sound alerts (optional)
    """

    def __init__(self, enable_desktop: bool = True, enable_sound: bool = False):
        self.enable_desktop = enable_desktop
        self.enable_sound = enable_sound
        self._desktop_available = self._check_desktop_notifications()

    def _check_desktop_notifications(self) -> bool:
        """Check if desktop notifications are available."""
        if not self.enable_desktop:
            return False

        try:
            # Try to import platform-specific notification libraries
            if platform.system() == 'Windows':
                try:
                    from win10toast import ToastNotifier
                    return True
                except ImportError:
                    logger.info("win10toast not available. Install with: pip install win10toast")
                    return False

            elif platform.system() == 'Darwin':  # macOS
                try:
                    import pync
                    return True
                except ImportError:
                    logger.info("pync not available. Install with: pip install pync")
                    return False

            else:  # Linux and others
                try:
                    import notify2
                    notify2.init('Marketplace Scraper')
                    return True
                except ImportError:
                    logger.info("notify2 not available. Install with: pip install notify2")
                    return False

        except Exception as e:
            logger.warning(f"Error checking desktop notifications: {e}")
            return False

    def notify(self, deals: List[Dict]):
        """
        Send notifications for good deals.

        Args:
            deals: List of deal dictionaries with keys:
                   title, price, url, source, confidence_score, deal_quality
        """
        if not deals:
            return

        # Console notification (always shown)
        self._console_notify(deals)

        # Desktop notification
        if self._desktop_available:
            self._desktop_notify(deals)

        # Sound alert
        if self.enable_sound:
            self._sound_alert()

    def _console_notify(self, deals: List[Dict]):
        """Print deals to console with formatting."""
        print("\n" + "=" * 80)
        print(f"🎉 FOUND {len(deals)} GOOD DEAL{'S' if len(deals) != 1 else ''}!")
        print("=" * 80)

        for i, deal in enumerate(deals, 1):
            print(f"\n{i}. {deal['title']}")
            print(f"   💰 Price: ${deal['price']:.2f}")
            print(f"   📍 Source: {deal['source']}")
            if deal.get('location'):
                print(f"   📌 Location: {deal['location']}")
            print(f"   ⭐ Quality: {deal['deal_quality'].upper()} "
                  f"(Score: {deal['confidence_score']:.1f}/100)")
            print(f"   🔗 URL: {deal['url']}")

        print("\n" + "=" * 80 + "\n")

    def _desktop_notify(self, deals: List[Dict]):
        """Send desktop notification."""
        try:
            if platform.system() == 'Windows':
                self._windows_notify(deals)
            elif platform.system() == 'Darwin':
                self._macos_notify(deals)
            else:
                self._linux_notify(deals)

        except Exception as e:
            logger.warning(f"Desktop notification failed: {e}")

    def _windows_notify(self, deals: List[Dict]):
        """Windows desktop notification."""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()

            if len(deals) == 1:
                deal = deals[0]
                title = "Good Deal Found!"
                message = f"{deal['title']}\n${deal['price']:.2f} - {deal['source']}"
            else:
                title = f"{len(deals)} Good Deals Found!"
                message = f"Check console for details"

            toaster.show_toast(
                title,
                message,
                duration=10,
                threaded=True
            )

        except Exception as e:
            logger.warning(f"Windows notification failed: {e}")

    def _macos_notify(self, deals: List[Dict]):
        """macOS desktop notification."""
        try:
            import pync

            if len(deals) == 1:
                deal = deals[0]
                title = "Good Deal Found!"
                message = f"{deal['title']} - ${deal['price']:.2f}"
            else:
                title = f"{len(deals)} Good Deals Found!"
                message = "Check console for details"

            pync.notify(
                message,
                title=title,
                sound='default'
            )

        except Exception as e:
            logger.warning(f"macOS notification failed: {e}")

    def _linux_notify(self, deals: List[Dict]):
        """Linux desktop notification."""
        try:
            import notify2

            if len(deals) == 1:
                deal = deals[0]
                title = "Good Deal Found!"
                message = f"{deal['title']}\n${deal['price']:.2f} - {deal['source']}"
            else:
                title = f"{len(deals)} Good Deals Found!"
                message = "Check console for details"

            notification = notify2.Notification(title, message)
            notification.show()

        except Exception as e:
            logger.warning(f"Linux notification failed: {e}")

    def _sound_alert(self):
        """Play a sound alert."""
        try:
            # Try to play a system beep
            if platform.system() == 'Windows':
                import winsound
                winsound.Beep(1000, 500)  # 1000 Hz for 500ms
            else:
                # Unix-like systems
                print('\a')  # ASCII bell character

        except Exception as e:
            logger.warning(f"Sound alert failed: {e}")
