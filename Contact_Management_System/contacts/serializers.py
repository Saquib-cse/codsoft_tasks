from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'email', 'phone_number',
            'address', 'company', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_email(self, value):
        return value.strip().lower()

    def validate_phone_number(self, value):
        return value.strip()

    def validate(self, attrs):
        """
        Cross-field validation: prevent duplicate contacts (same email or
        same phone number) for this user. Handles both create and update,
        excluding the current instance on update.
        """
        request = self.context.get('request')
        owner = request.user if request else None

        email = attrs.get('email', getattr(self.instance, 'email', None))
        phone_number = attrs.get(
            'phone_number', getattr(self.instance, 'phone_number', None)
        )

        if owner is not None:
            from django.db.models import Q

            qs = Contact.objects.filter(owner=owner).filter(
                Q(email=email) | Q(phone_number=phone_number)
            )
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    "A contact with this email or phone number already exists."
                )

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['owner'] = request.user
        return super().create(validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
