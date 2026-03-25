"""
Health check endpoint
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint that returns 200 status
    No authentication required
    """
    return JsonResponse({
        'status': 'healthy',
        'message': 'Service is running'
    }, status=200)