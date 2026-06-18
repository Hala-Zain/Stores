from rest_framework import serializers

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from .models import (
    Category,Product,Cart,CartItem,Order,OrderItem, Payment)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    user_type = serializers.ChoiceField(choices=['seller', 'customer'], write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'user_type']
        
    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        validated_data['is_seller'] = (user_type == 'seller')
        validated_data['is_customer'] = (user_type == 'customer')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class CategorySerializer(serializers.ModelSerializer):

    class Meta:

        model = Category

        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):

    class Meta:

        model = Product

        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:

        model = CartItem

        fields = '__all__'


class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Cart

        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:

        model = OrderItem

        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Order

        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:

        model = Payment

        fields = '__all__'