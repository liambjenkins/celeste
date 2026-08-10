"""
Celeste model backend boundary.

The knowledge system depends on this interface rather than
on a specific model provider.
"""


class ModelBackend:
    """
    Interface implemented by semantic extraction backends.
    """

    def extract_claims(
        self,
        *,
        passage,
        lens_id,
    ):
        """
        Return a JSON-compatible extraction payload.
        """

        raise NotImplementedError(
            "Model backend must implement "
            "extract_claims()."
        )
