from django.utils import timezone


def is_past_date(value):
    """
    Проверяет, является ли дата 'value' прошедшей по отношению к текущей дате.
    """
    return value < timezone.now().date()
