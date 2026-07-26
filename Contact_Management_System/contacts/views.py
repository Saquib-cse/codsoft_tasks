from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from rest_framework import generics, filters, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Contact
from .serializers import ContactSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ - create a new user account."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'username': user.username, 'token': token.key},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/auth/login/ - exchange username/password for an auth token."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError({'detail': 'Invalid username or password.'})

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'username': user.username, 'token': token.key})


class ContactSearchFilter(filters.SearchFilter):
    search_param = 'search'


class ContactListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/contacts/  - list the current user's contacts.
        Query params:
          ?search=<text>          fuzzy match on name, email, or phone
          ?ordering=<field>       e.g. name, -name, created_at, -created_at
          ?page=<n>&page_size=<n> pagination (page_size capped by server)
          ?company=<text>         exact filter by company
    POST /api/contacts/  - create a new contact for the current user.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, ContactSearchFilter, filters.OrderingFilter]
    filterset_fields = ['company']
    search_fields = ['name', 'email', 'phone_number']
    ordering_fields = ['name', 'email', 'created_at', 'updated_at']
    ordering = ['name']

    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            raise ValidationError(
                {'detail': 'A contact with this email or phone number already exists.'}
            )


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/contacts/<id>/
    Scoped so a user can only ever see or modify their own contacts.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except IntegrityError:
            raise ValidationError(
                {'detail': 'A contact with this email or phone number already exists.'}
            )
