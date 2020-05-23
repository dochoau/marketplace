from django.shortcuts import render, get_object_or_404, redirect
from books.models import Book
from .models import Order, OrderItem, Payment
from django.http import HttpResponseRedirect
from django.conf import settings
import stripe
import string
import random

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    """Con esto creamos un código de referencia aleatorio """
    ''.join(random.choice(string.ascii_uppercase + string.digits, k=15))


def add_to_cart(request, book_slug):
    book = get_object_or_404(Book, slug=book_slug)
    order_item, created = OrderItem.objects.get_or_create(book=book)
    order, created = Order.objects.get_or_create(user=request.user)
    order.item.add(order_item)
    order.save()
    # Este redirect nos devuelve a la página donde estabamos
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def remove_from_cart(request, book_slug):
    book = get_object_or_404(Book, slug=book_slug)
    order_item = get_object_or_404(OrderItem, book=book)
    order = get_object_or_404(Order, user=request.user)
    order.item.remove(order_item)
    order.save()
    # Este redirect nos devuelve a la página donde estabamos
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def order_view(request):
    order = get_object_or_404(Order, user=request.user)
    context = {
        'order': order
    }
    return render(request, "order_summary.html", context)


def checkout(request):
    order = get_object_or_404(Order, user=request.user)
    context = {'order': order}
    if request.method == 'POST':
        # Completar la orden
        ref_code = create_ref_code()
        order.ref_code = ref_code
        # token de stripe
        token = request.POST.get('stripeToken')
        # crear el stripe charge
        charge = stripe.Charge.create(
            # esto está en centavos por eso se multiplica por 100
            amount=order.get_total() * 100,
            currency="usd",
            source=token,
            description=f"Charge for {request.user.username}"
        )
        print(charge)
        # payment = Payment()
        # payment.order = order
        # payment.stripe_charge_id = charge.id
        # payment.total_amount = order.get_total() * 100
        # payment.save()

        # # agregar los libros al usuario
        # books = [item.book for item in order.items.all()]
        # for book in books:
        #     request.user.userlibrary.item.add(book)
        # return redirect("/account/profile/")

    return render(request, "checkout.html", context)
