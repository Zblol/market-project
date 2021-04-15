from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from PIL import Image
from django.urls import reverse, path
from django.utils import timezone

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


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


class CategoryManager(models.Manager):
    CATEGORY_NAME_COUNT_NAME = {
        'Notebooks': 'notebook__count',
        'Smartphone': 'smartphone__count',
    }

    def get_query_set(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_query_set().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url, count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Category name')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


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

    def save(self, *args, **kwargs):
        super().save()
        img = Image.open(self.image.path)

        if img.height > 400 or img.width > 400:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


    def get_model_name(self):
        return self.__class__.__name__.lower()

class Notebook(Product):
    diagonal = models.CharField(max_length=255)
    display_type = models.CharField(max_length=255)
    processor_freq = models.CharField(max_length=255)
    ram = models.CharField(max_length=255)
    video = models.CharField(max_length=255)
    battery_charge_time = models.CharField(max_length=255)

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):
    diagonal = models.CharField(max_length=255)
    display_type = models.CharField(max_length=255)
    resolution = models.CharField(max_length=255)
    accum_volume = models.CharField(max_length=255)
    ram = models.CharField(max_length=255)
    sd = models.BooleanField(default=True)
    sd_volume_max = models.CharField(max_length=255, null=True, blank=True)
    main_cam = models.CharField(max_length=255)
    front_cam = models.CharField(max_length=255)

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CartProduct(models.Model):
    user = models.ForeignKey("Customer", verbose_name='Customer', on_delete=models.CASCADE)
    cart = models.ForeignKey("Cart", verbose_name='Cart', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    count = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='total price')

    def __str__(self):
        return "Product: {} (for cart)".format(self.content_object.title)

    def save(self, *args, **kwargs):
        self.total_price = self.count * self.content_object.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', null=True, verbose_name='Customer', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='total price')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Customer', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='phone number', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Address', null=True, blank=True)
    orders = models.ManyToManyField('Order', related_name='related_customer')

    def __str__(self):
        return self.user.username


class Order(models.Model):

    STATUS_NEW  = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW , 'new order'),
        (STATUS_IN_PROGRESS, 'order progressing'),
        (STATUS_READY, 'order finished'),
        (STATUS_COMPLETED, 'order delivered'),
    )


    BUYING_TYPE_CHOICES = (

        (BUYING_TYPE_SELF, 'take self'),
        (BUYING_TYPE_DELIVERY, 'delivery to'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='related_orders')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE, null=True,blank=True)
    address = models.CharField(max_length=1024, null=True, blank=True)
    status = models.CharField(
        max_length= 100,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    buying_type = models.CharField(
        max_length=100,
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF,
    )

    comment = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now=True)
    order_date = models.DateField(default=timezone.now)


    def __str__(self):
        return str(self.id)