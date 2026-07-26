from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handling to return a consistent,
    meaningful error envelope for every API error:

        {
            "error": true,
            "detail": "...",
            "fields": {...}   # present only for field-level validation errors
        }
    """
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        payload = {'error': True}

        if isinstance(data, dict):
            # Field-level validation errors come back as {"field": [...]}
            non_field = data.pop('non_field_errors', None) or data.pop('detail', None)
            if data:
                payload['fields'] = data
            payload['detail'] = (
                non_field[0] if isinstance(non_field, list) and non_field
                else non_field or 'One or more fields are invalid.'
            )
        elif isinstance(data, list):
            payload['detail'] = data[0] if data else 'Invalid request.'
        else:
            payload['detail'] = str(data)

        response.data = payload
        return response

    # Unhandled exception (e.g. IntegrityError bubbling up) -> generic 500
    return Response(
        {'error': True, 'detail': 'An unexpected server error occurred.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
