from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.http import HttpResponseRedirect, HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings


# ---------------------------------------------------------------------------------
# ------------------------ CUSTOMER RELATED VIEWS START ---------------------------
# ---------------------------------------------------------------------------------

def customer_home_view(request):
    products = models.Product.objects.all()
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(counter)
    else:
        product_count_in_cart = 0
    return render(request, 'ecom/customer_home.html', {'products': products, 'product_count_in_cart': product_count_in_cart})


# any one can add product to cart, no need of signin
def add_to_cart_view(request, pk):
    products = models.Product.objects.all()

    # for cart counter, fetching products ids added by customer from cookies
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(counter)
    else:
        product_count_in_cart = 1

    response = render(request, 'ecom/index.html',
                      {'products': products, 'product_count_in_cart': product_count_in_cart})

    # adding product id to cookies
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids == "":
            product_ids = str(pk)
        else:
            product_ids = product_ids+"|"+str(pk)
        response.set_cookie('product_ids', product_ids)
    else:
        response.set_cookie('product_ids', pk)

    #   product = models.Product.objects.get(id=pk)
    # messages.info(request, product.name + ' added to cart successfully!')

    return response


# for checkout of cart purchase
def cart_view(request):
    # for cart counter
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(counter)
    else:
        product_count_in_cart = 0

    # fetching product details from db whose id is present in cookie
    products = None
    total = 0
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        quantity = []
        if product_ids != "":
            product_id_in_cart = sorted(product_ids.split('|'))
            product_id_in_cart_distinct = set(product_id_in_cart)
            for x in product_id_in_cart_distinct:
                temp = product_id_in_cart.count(x)
                quantity.append(temp)
        products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        
        combined = zip(products , quantity)
        # for total price shown in cart
        # 2.0
        for x in product_id_in_cart:
            my_obj = models.Product.objects.get(id=x)
            total += my_obj.price
            # products = products | models.Product.objects.get(id=x)

            # 1.0
            # for p in products:
            # total=total+p.price

    return render(request, 'ecom/cart.html', {'combined' : combined , 'total': total, 'product_count_in_cart': product_count_in_cart})


def remove_from_cart_view(request, pk):
    # for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(counter)
    else:
        product_count_in_cart = 0

    # removing product id from cookie
    total = 0
    if 'product_ids' in request.COOKIES:
        quantity = []
        product_ids = request.COOKIES['product_ids']
        product_id_in_cart = sorted(product_ids.split('|'))
        # product_id_in_cart=list(set(product_id_in_cart))
        # hello
        product_id_in_cart.remove(str(pk))
        product_id_in_cart_distinct = set(product_id_in_cart)
        for x in product_id_in_cart_distinct:
            temp = product_id_in_cart.count(x)
            quantity.append(temp)
        products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # for total price shown in cart
        combined = zip(products , quantity)
        # 2.0
        for x in product_id_in_cart:
            my_obj = models.Product.objects.get(id=x)
            total += my_obj.price
            # products = products | models.Product.objects.get(id=x)
        # 1.0
        # for p in products:
            # total=total+p.price

        #  for update coookie value after removing product id in cart
        value = ""
        for i in range(len(product_id_in_cart)):
            if i == 0:
                value = value+product_id_in_cart[0]
            else:
                value = value+"|"+product_id_in_cart[i]
        response = render(request, 'ecom/cart.html', {'combined' : combined , 'total': total, 'product_count_in_cart': product_count_in_cart})
        if value == "":
            response.delete_cookie('product_ids')
        response.set_cookie('product_ids', value)
        return response


def customer_signup_view(request):
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerForm()
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customer = customerForm.save(commit=False)
            customer.user = user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('customerlogin')
    return render(request, 'ecom/customersignup.html', context=mydict)


def aboutus_view(request):
    return render(request, 'ecom/aboutus.html')


def customer_address_view(request):
    # this is for checking whether product is present in cart or not
    # if there is no product in cart we will not show address form
    product_in_cart = False
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_in_cart = True
    # for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(counter)
    else:
        product_count_in_cart = 0

    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            # here we are taking address, email, mobile at time of order placement
            # we are not taking it from customer account table because
            # these thing can be changes
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']
            # for showing total price on payment page.....accessing id from cookies then fetching  price of product from db
            total = 0
            if 'product_ids' in request.COOKIES:
                product_ids = request.COOKIES['product_ids']
                if product_ids != "":
                    product_id_in_cart = product_ids.split('|')
                    products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # 2.0
                    for x in product_id_in_cart:
                        my_obj = models.Product.objects.get(id=x)
                        total += my_obj.price

                    # for p in products:
                    #     total=total+p.price

            response = render(request, 'ecom/payment.html',
                              {'total': total, 'product_count_in_cart': product_count_in_cart})
            response.set_cookie('email', email)
            response.set_cookie('mobile', mobile)
            response.set_cookie('address', address)
            return response
    return render(request, 'ecom/customer_address.html', {'addressForm': addressForm, 'product_in_cart': product_in_cart, 'product_count_in_cart': product_count_in_cart})


def payment_success_view(request):

    # customer=models.Customer.objects.get(user_id=request.user.id)

    products = None
    email = None
    mobile = None
    address = None
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)
            # Here we get products list that will be ordered by one customer at a time

    # these things can be change so accessing at the time of order...
    if 'email' in request.COOKIES:
        email = request.COOKIES['email']
    if 'mobile' in request.COOKIES:
        mobile = request.COOKIES['mobile']
    if 'address' in request.COOKIES:
        address = request.COOKIES['address']

    # for product in products:
        # models.Orders.objects.get_or_create(customer=customer,product=product,status='Pending',email=email,mobile=mobile,address=address)
    # new orders

    # after order placed cookies should be deleted
    response = render(request, 'ecom/payment_success.html')
    response.delete_cookie('product_ids')
    response.delete_cookie('email')
    response.delete_cookie('mobile')
    response.delete_cookie('address')
    return response