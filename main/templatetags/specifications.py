from django import template
from django.utils.safestring import mark_safe
from main.models import Smartphone

register = template.Library()

TABLE_HEADER = """
                    <table class="table">
                        <tbody>
                """

TABLE_CONTENT = """
                     <tr>
                        <td>{name}</td>
                        <td>{value}</td>
                    </tr>
                """

TABLE_FOOTER = """
                       </tbody>
                        </table>
                """

PRODUCT_SPEC = {
    'notebook': {
        'Diagonal': 'diagonal',
        'Display Type': 'display_type',
        'Processor': 'processor_freq',
        'Ram': 'ram',
        'Video': 'video',
        'Battery': 'battery_charge_time',
    },

    'smartphone': {
        'Diagonal': 'diagonal',
        'Display Type': 'display_type',
        'Resolution': 'resolution',
        'Accumulator': 'accum_volume',
        'Ram': 'ram',
        'Sd': 'sd',
        'SD Max Volume': 'sd_volume_max',
        'Main Camera': 'main_cam',
        'Front Camera': 'front_cam',
    },
}


def get_product_spec(product, model_name):
    table_content = ''
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


@register.filter
def product_spec(product):
    if isinstance(product,Smartphone):
        if not product.sd:
            PRODUCT_SPEC['smartphone'].pop('SD Max Volume')
        else:
            PRODUCT_SPEC['smartphone']['SD Max Volume'] = 'sd_volume_max'

    model_name = product.__class__._meta.model_name
    return mark_safe(TABLE_HEADER + get_product_spec(product, model_name) + TABLE_FOOTER)
