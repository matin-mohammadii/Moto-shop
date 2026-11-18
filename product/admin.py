
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Product, Order, CartItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'date')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'customer_name',
        'phone',
        'product',
        'quantity',
        'status',
        'date'
    )

    list_filter = ('status',)

    def save_model(self, request, obj, form, change):

        with transaction.atomic():

            if change:
                old_order = Order.objects.select_for_update().get(
                    pk=obj.pk
                )

                product_ids = {
                    old_order.product_id,
                    obj.product_id
                }

                products = {
                    product.pk: product
                    for product in Product.objects.select_for_update().filter(
                        pk__in=product_ids
                    )
                }

                old_product = products[old_order.product_id]
                new_product = products[obj.product_id]

                if old_order.product_id == obj.product_id:

                    available_stock = (
                        old_product.stock + old_order.quantity
                    )

                    if obj.quantity > available_stock:
                        raise ValidationError(
                            "موجودی محصول کافی نیست."
                        )

                    new_product.stock = (
                        available_stock - obj.quantity
                    )

                else:

                    if obj.quantity > new_product.stock:
                        raise ValidationError(
                            "موجودی محصول جدید کافی نیست."
                        )

                    old_product.stock += old_order.quantity
                    new_product.stock -= obj.quantity

                    old_product.save(update_fields=['stock'])

                new_product.save(update_fields=['stock'])

            else:

                product = Product.objects.select_for_update().get(
                    pk=obj.product_id
                )

                if obj.quantity > product.stock:
                    raise ValidationError(
                        "موجودی محصول کافی نیست."
                    )

                product.stock -= obj.quantity
                product.save(update_fields=['stock'])

            super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):

        with transaction.atomic():

            product = Product.objects.select_for_update().get(
                pk=obj.product_id
            )

            product.stock += obj.quantity
            product.save(update_fields=['stock'])

            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):

        with transaction.atomic():

            orders = list(queryset)

            product_ids = {
                order.product_id for order in orders
            }

            products = {
                product.pk: product
                for product in Product.objects.select_for_update().filter(
                    pk__in=product_ids
                )
            }

            for order in orders:
                product = products[order.product_id]
                product.stock += order.quantity

            for product in products.values():
                product.save(update_fields=['stock'])

            super().delete_queryset(request, queryset)


admin.site.register(CartItem)
