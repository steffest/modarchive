import factory

from django.contrib.auth import models as auth_models

from homepage import models

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth_models.User

    username = factory.Sequence(lambda n: f'test_user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.org')

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for perm in extracted:
                self.user_permissions.add(perm)

class BlacklistedDomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BlacklistedDomain

class NewsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.News

    headline = factory.Sequence(lambda n: 'Headline %d' % n)
    content = factory.Sequence(lambda n: 'This is news content')

class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Message
    
    text = factory.Sequence(lambda n: f'Message number {n}')
