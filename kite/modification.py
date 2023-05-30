"""Modifications to the calculations."""

__all__ = ['Modification']


class Modification:
    """TODO: Add some explenation."""
    def __init__(self, **kwargs):
        self._magnetic_field = kwargs.get('magnetic_field', None)
        self._flux = kwargs.get('flux', None)

    @property
    def magnetic_field(self):  # magnetic_field:
        """Returns true if magnetic field is on, else False."""
        return self._magnetic_field

    @property
    def flux(self):  # flux:
        """Returns the number of multiples of flux quantum."""
        return self._flux
