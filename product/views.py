
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, CartItem
from .forms import OrderForm, RegisterForm, ProfileForm

from django.db import transaction
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST


def product_list(request):

    search = request.GET.get('search')

    if search:
        products = Product.objects.filter(name__icontains=search)
    else:
        products = Product.objects.all()

    return render(request, 'product/product_list.html', {
        'products': products
    })


def product_detail(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    return render(request, 'product/product_detail.html', {
        'product': product
    })


@login_required(login_url='login')
def create_order(request, product_id):

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            with transaction.atomic():

                product = get_object_or_404(
                    Product.objects.select_for_update(),
                    id=product_id
                )

                quantity = form.cleaned_data['quantity']

                if quantity > product.stock:
                    form.add_error(
                        'quantity',
                        'موجودی محصول کافی نیست.'
                    )
                else:
                    order = form.save(commit=False)
                    order.product = product
                    order.user = request.user
                    order.save()

                    product.stock -= quantity
                    product.save(update_fields=['stock'])

                    return redirect(
                        'order_success',
                        order_id=order.id
                    )

    else:
        form = OrderForm()

    product = get_object_or_404(Product, id=product_id)

    return render(request, 'product/order_form.html', {
        'form': form,
        'product': product
    })


@login_required(login_url='login')
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, 'product/order_success.html', {
        'order': order
    })


def register_view(request):

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect('product_list')

    else:
        form = RegisterForm()

    return render(request, 'product/register.html', {
        'form': form
    })


def login_view(request):

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            return redirect('product_list')

    else:
        form = AuthenticationForm(request)

    form.fields['username'].label = 'شماره موبایل'

    return render(request, 'product/login.html', {
        'form': form
    })


@require_POST
def logout_view(request):

    logout(request)

    return redirect('product_list')


@require_POST
@login_required(login_url='login')
def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    cart_item = CartItem.objects.filter(
        user=request.user,
        product=product
    ).first()

    current_quantity = cart_item.quantity if cart_item else 0

    if current_quantity + 1 > product.stock:
        messages.error(request, 'موجودی محصول کافی نیست.')

    else:
        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            CartItem.objects.create(
                user=request.user,
                product=product,
                quantity=1
            )

        messages.success(request, 'محصول به سبد خرید اضافه شد.')

    return redirect('product_detail', product_id=product_id)


@login_required(login_url='login')
def cart_view(request):

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('product')

    total_price = 0

    for item in cart_items:
        total_price += item.product.price * item.quantity

    return render(request, 'product/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


@require_POST
@login_required(login_url='login')
def update_cart(request, item_id):

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    try:
        quantity = int(request.POST.get('quantity'))

        if quantity < 1:
            messages.error(request, 'تعداد باید حداقل ۱ باشد.')

        elif quantity > cart_item.product.stock:
            messages.error(request, 'موجودی محصول کافی نیست.')

        else:
            cart_item.quantity = quantity
            cart_item.save()

            messages.success(request, 'تعداد محصول ویرایش شد.')

    except (ValueError, TypeError):
        messages.error(request, 'تعداد واردشده معتبر نیست.')

    return redirect('cart')


@require_POST
@login_required(login_url='login')
def remove_from_cart(request, item_id):

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    cart_item.delete()

    messages.success(request, 'محصول از سبد خرید حذف شد.')

    return redirect('cart')


@require_POST
@login_required(login_url='login')
def checkout(request):

    with transaction.atomic():

        cart_items = list(
            CartItem.objects.filter(
                user=request.user
            ).select_related('product')
        )

        if not cart_items:
            messages.error(request, 'سبد خرید شما خالی است.')
            return redirect('cart')

        if not request.user.first_name.strip():
            messages.error(
                request,
                'ابتدا نام خود را در حساب کاربری تکمیل کنید.'
            )
            return redirect('cart')

        # بررسی موجودی تمام محصولات
        for item in cart_items:

            product = Product.objects.select_for_update().get(
                pk=item.product_id
            )

            if item.quantity > product.stock:
                messages.error(
                    request,
                    f'موجودی محصول {product.name} کافی نیست.'
                )
                return redirect('cart')

        # ثبت سفارش و کاهش موجودی
        created_orders = []

        for item in cart_items:

            product = Product.objects.select_for_update().get(
                pk=item.product_id
            )

            order = Order.objects.create(
                user=request.user,
                customer_name=request.user.first_name,
                phone=request.user.username,
                product=product,
                quantity=item.quantity
            )

            product.stock -= item.quantity
            product.save(update_fields=['stock'])

            created_orders.append(order)

        # خالی کردن سبد خرید
        CartItem.objects.filter(user=request.user).delete()

    return redirect(
        'order_success',
        order_id=created_orders[-1].id
    )


@login_required(login_url='login')
def order_history(request):

    orders = Order.objects.filter(
        user=request.user
    ).select_related('product').order_by('-date')

    return render(request, 'product/order_history.html', {
        'orders': orders
    })


@login_required(login_url='login')
def profile_view(request):

    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'اطلاعات حساب با موفقیت ویرایش شد.'
            )

            return redirect('profile')

    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'product/profile.html', {
        'form': form
    })
