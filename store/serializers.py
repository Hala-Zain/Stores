from rest_framework import serializers

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    # إجبار المستخدم على إدخال كلمة مرور قوية، وإخفائها من الردود (write_only)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    # حصر نوع المستخدم بخيارين فقط
    user_type = serializers.ChoiceField(choices=['seller', 'customer'], write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'user_type']
        
    def create(self, validated_data):
        # سحب نوع المستخدم لتحديد الصلاحيات
        user_type = validated_data.pop('user_type')
        validated_data['is_seller'] = (user_type == 'seller')
        validated_data['is_customer'] = (user_type == 'customer')
        
        # إنشاء المستخدم وتشفير كلمة المرور تلقائياً
        user = CustomUser.objects.create_user(**validated_data)
        return user
from .models import (
    Category,Product,Cart,CartItem,Order,OrderItem, Payment)


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