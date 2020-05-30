from django.shortcuts import render, get_object_or_404, redirect
from books.models import Book
from .models import Order, OrderItem, Payment
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import stripe
import string
import random
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_ref_code():
    """Con esto creamos un código de referencia aleatorio """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))


@login_required
def add_to_cart(request, book_slug):
    book = get_object_or_404(Book, slug=book_slug)
    order_item, created = OrderItem.objects.get_or_create(book=book)
    order, created = Order.objects.get_or_create(user=request.user)
    order.item.add(order_item)
    order.save()
    messages.info(request, "Item añadido al carro")
    # Este redirect nos devuelve a la página donde estabamos
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@login_required
def remove_from_cart(request, book_slug):
    book = get_object_or_404(Book, slug=book_slug)
    order_item = get_object_or_404(OrderItem, book=book)
    order = get_object_or_404(Order, user=request.user)
    order.item.remove(order_item)
    order.save()
    messages.info(request, "Item quitado del carro")
    # Este redirect nos devuelve a la página donde estabamos
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@login_required
def order_view(request):
    order = get_object_or_404(Order, user=request.user)
    context = {
        'order': order
    }
    return render(request, "order_summary.html", context)


@login_required
def checkout(request):
    order = get_object_or_404(Order, user=request.user)
    context = {'order': order}
    if request.method == 'POST':
        try:
            # Completar la orden
            ref_code = create_ref_code()
            order.ref_code = ref_code
            # token de stripe
            token = request.POST.get('stripeToken')
            # crear el stripe charge
            charge = stripe.Charge.create(
                # esto está en centavos por eso se multiplica por 100
                amount=int(order.get_total() * 100),
                currency="usd",
                source=token,
                description=f"Charge for {request.user.username}"
            )
            payment = Payment()
            payment.order = order
            payment.stipe_charge_id = charge.id
            payment.total_amount = order.get_total() * 100
            payment.save()

            # agregar los libros al usuario
            books = [item.book for item in order.item.all()]
            for book in books:
                request.user.userlibrary.books.add(book)
            order.is_ordered = True
            order.save()
            return redirect("/account/profile/")
        except stripe.error.CardError as e:
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(request, "Hubo un error con la tarjeta")
            return redirect(reverse("cart:checkout"))
    return render(request, "checkout.html", context)
