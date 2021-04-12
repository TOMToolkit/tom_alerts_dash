import factory
from faker import Faker

from tom_targets.models import Target

fake = Faker()


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


def create_scimma_alert(ra=None, dec=None, rank=None):
    return {
        'alert_identifier': fake.pystr_format(string_format='S######y_X##'),
        'right_ascension_sexagesimal': ra if ra else fake.pystr_format(string_format='##:##:##.###'),
        'declination_sexagesimal': dec if dec else fake.pystr_format(string_format='##:##:##.###'),
        'topic': fake.pystr(max_chars=5),
        'message': {
            'rank': rank if rank else fake.pyint(min_value=1, max_value=4),
            'event_trig_num': fake.pystr_format(string_format='S######')
        },
        'extracted_fields': {
            'counterpart_identifier': fake.pystr_format(string_format='#??? ?######.#+######'),
            'comment_warnings': fake.pystr(),
        }
    }


def create_alerce_alert(meanra=None, meandec=None, firstmjd=None, lastmjd=None, class_name=None, classifier=None,
                        probability=None):
    return {'oid': fake.pystr_format(string_format='ZTF##???????', letters='abcdefghijklmnopqrstuvwxyz'),
            'meanra': meanra if meanra else fake.pyfloat(min_value=0, max_value=360),
            'meandec': meandec if meandec else fake.pyfloat(min_value=0, max_value=360),
            'firstmjd': firstmjd if firstmjd else fake.pyfloat(min_value=56000, max_value=59000, right_digits=1),
            'lastmjd': lastmjd if lastmjd else fake.pyfloat(min_value=56000, max_value=59000, right_digits=1),
            'class': class_name if class_name else fake.pystr_format(string_format='????????',
                                                                     letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            'classifier': classifier if classifier else fake.pystr_format(string_format='???',
                                                                          letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            'probability': probability if probability else fake.pyfloat(min_value=0, max_value=1)}
