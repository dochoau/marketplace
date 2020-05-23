from django.shortcuts import render, get_object_or_404
from .models import Book, Chapter, Exercise
from django.http import Http404
from shopping_cart.models import Order, OrderItem

OWNED = 'owned'
IN_CART = 'in_cart'
NOT_IN_CART = 'not_in_cart'


def check_book(request, book):
    if book in request.user.userlibrary.books.all():
        return OWNED
    order_qs = Order.objects.filter(user=request.user)
    if order_qs.exists():
        order = order_qs[0]
        order_item_qs = OrderItem.objects.filter(book=book)
        if order_item_qs.exists():
            order_item = order_item_qs[0]
            if order_item in order.item.all():
                return IN_CART
    return NOT_IN_CART


def book_list(request):
    qs = Book.objects.all()
    context = {
        'queryset': qs
    }
    return render(request, "book_list.html", context)


def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    book_status = check_book(request, book)
    context = {
        'book': book,
        'book_status': book_status
    }
    return render(request, "book_detail.html", context)


def chapter_detail(request, book_slug, chapter_number):
    # de esta forma accedemos a un atributo del atributo,
    chapter_qs = Chapter.objects.filter(
        book__slug=book_slug).filter(chapter_number=chapter_number)
    chapter = chapter_qs[0]
    book_status = check_book(request, chapter.book)
    if chapter_qs.exists():
        context = {
            'chapter': chapter,
            'book_status': book_status
        }
        return render(request, 'chapter_detail.html', context)
    return Http404


def exercise_detail(request, book_slug, chapter_number, exercise_number):
    # de esta forma accedemos a un atributo del atributo,
    exercise_qs = Exercise.objects.filter(
        chapter__book__slug=book_slug).filter(chapter__chapter_number=chapter_number).filter(exercise_number=exercise_number)
    exercise = exercise_qs[0]
    book_status = check_book(request, exercise.chapter.book)
    if exercise_qs.exists():
        context = {
            'exercise': exercise,
            'book_status': book_status}
        return render(request, 'exercise_detail.html', context)
    return Http404
