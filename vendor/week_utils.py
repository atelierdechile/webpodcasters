# vendor/week_utils.py
import datetime


def get_week_range(reference_date=None):
    """
    Devuelve (lunes, domingo) de la semana de reference_date.
    """
    if reference_date is None:
        reference_date = datetime.date.today()

    monday = reference_date - datetime.timedelta(days=reference_date.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday
