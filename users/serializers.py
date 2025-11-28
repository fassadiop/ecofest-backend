# users/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'role', 'langue_pref')

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'telephone', 'role', 'langue_pref', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        # If no password supplied, generate a random one and return it so frontend can show it.
        import secrets
        if not password:
            password = secrets.token_urlsafe(10)  # example random password
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # attach created_password to instance for response context
        user._created_password = password
        return user

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # include generated password only on create
        pwd = getattr(instance, '_created_password', None)
        if pwd:
            rep['generated_password'] = pwd
        return rep
