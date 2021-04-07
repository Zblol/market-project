from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class LatestProductsManager:
    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                                  reverse=True)
        return products


class LatestProducts:
    objects = LatestProductsManager()


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Category name')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Category', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Product name')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name="Image")
    description = models.TextField(verbose_name='Description', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Price')

    def __str__(self):
        return self.title


class Notebook(Product):
    diagonal = models.CharField(max_length=255)
    display_type = models.CharField(max_length=255)
    processor_freq = models.CharField(max_length=255)
    ram = models.CharField(max_length=255)
    video = models.CharField(max_length=255)
    battery_charge_time = models.CharField(max_length=255)

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)


class Smartphone(Product):
    diagonal = models.CharField(max_length=255)
    display_type = models.CharField(max_length=255)
    resolution = models.CharField(max_length=255)
    accum_volume = models.CharField(max_length=255)
    ram = models.CharField(max_length=255)
    sd = models.BooleanField(default=True)
    sd_volume_max = models.CharField(max_length=255)
    main_cam = models.CharField(max_length=255)
    front_cam = models.CharField(max_length=255)

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)


class CartProduct(models.Model):
    user = models.ForeignKey("Customer", verbose_name='Customer', on_delete=models.CASCADE)
    cart = models.ForeignKey("Cart", verbose_name='Cart', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    count = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='total price')

    def __str__(self):
        return "Product: {} (for cart)".format(self.product.title)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', verbose_name='Customer', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='total price')

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Customer', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='phone number')
    address = models.CharField(max_length=255, verbose_name='Address')

    def __str__(self):
        return "Customer: {} {}".format(self.user.first_name, self.user.last_name)
