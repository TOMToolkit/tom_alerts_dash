import factory
from faker import Faker

from tom_targets.models import Target


class SiderealTargetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Target

    name = factory.Faker('pystr')
    type = Target.SIDEREAL
    ra = factory.Faker('pyfloat', min_value=-90, max_value=90)
    dec = factory.Faker('pyfloat', min_value=-90, max_value=90)
    epoch = factory.Faker('pyfloat')
    pm_ra = factory.Faker('pyfloat')
    pm_dec = factory.Faker('pyfloat')


def create_mars_alert(ra=None, dec=None, magpsf=None, rb=None):
    fake = Faker()
    return {
        'avro': fake.uri(),
        'candid': fake.pyint(min_value=1000000000000000000, max_value=9999999999999999999),
        'objectId': fake.pystr_format(string_format='ZTF##???????'),
        'lco_id': fake.pyint(min_value=100000000, max_value=999999999),
        'candidate': {
            'ra': ra if ra else fake.pyfloat(min_value=0, max_value=360),
            'dec': dec if dec else fake.pyfloat(min_value=0, max_value=360),
            'magpsf': magpsf if magpsf else fake.pyfloat(min_value=12, max_value=22),
            'rb': rb if rb else fake.pyfloat(min_value=0, max_value=1),
            'drb': fake.pyfloat(min_value=0, max_value=1)
        }
    }
