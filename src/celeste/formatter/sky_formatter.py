from celeste.models.sky import SkySnapshot


class SkyFormatter:
    """Formats celestial data for humans."""

    @staticmethod
    def format(snapshot: SkySnapshot) -> str:
        return (
            f"Sun: {snapshot.sun:.2f}°\n"
            f"Moon: {snapshot.moon:.2f}°\n"
            f"Mercury: {snapshot.mercury:.2f}°\n"
            f"Venus: {snapshot.venus:.2f}°\n"
            f"Mars: {snapshot.mars:.2f}°"
        )