from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls.base import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from homepage.tokens import account_activation_token
from homepage.tests import factories
from artists import factories as artist_factories
from songs import factories as song_factories
from interactions import factories as interaction_factories

User = get_user_model()

MODARCHIVE_EMAIL = 'donotreply@modarchive.org'
NEW_USER_EMAIL = 'newuser@test.com'
PASSWORD = 'abcdef123!'

class PasswordResetViewTests(TestCase):
    username = 'test_user'
    email = 'testuser@test.com'
    password='testpassword'

    def setUp(self):
        self.user = factories.UserFactory(username=self.username, email=self.email, password=self.password)

    def test_get_request_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(self.user)

        # Act
        response = self.client.get(reverse('forgot_password'))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_get_request_returns_ok_when_not_authenticated(self):
        # Act
        response = self.client.get(reverse('forgot_password'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('templates/password_reset/forgot_password.html')

    def test_post_request_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(self.user)

        # Act
        response = self.client.post(reverse('forgot_password'), {'email': self.email})

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_post_request_redirects_to_password_reset_done_when_not_authenticated(self):
        # Act
        response = self.client.post(reverse('forgot_password'), {'email': self.email})

        # Assert
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertTemplateUsed('templates/password_reset/password_reset_done.html')

    def test_successful_post_sends_email(self):
        # Act
        self.client.post(reverse('forgot_password'), {'email': self.email})

        # Assert
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual([self.email], mail.outbox[0].to)
        self.assertEqual(MODARCHIVE_EMAIL, mail.outbox[0].from_email)
        self.assertEqual('Your ModArchive password has been reset', mail.outbox[0].subject)
        self.assertTrue('You have requested a password reset for your ModArchive account. To reset your password, please follow the link below.' in mail.outbox[0].body)

    def test_successful_post_with_email_not_in_database_does_not_send_email(self):
        # Act
        self.client.post(reverse('forgot_password'), {'email': 'notindatabase@test.com'})

        # Assert
        self.assertEqual(0, len(mail.outbox))

class PasswordResetConfirmViewTests(TestCase):
    kwargs = {'uidb64': 'Mg', 'token': 'asdfasdf'}

    def setUp(self):
        self.user = factories.UserFactory()

    def test_get_request_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(self.user)

        # Act
        response = self.client.get(reverse('password_reset', kwargs=self.kwargs))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_post_request_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(self.user)

        # Act
        response = self.client.post(reverse('password_reset', kwargs=self.kwargs))

        # Assert
        self.assertRedirects(response, reverse('home'))

class PasswordResetCompleteViewTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()

    def test_get_request_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(self.user)

        # Act
        response = self.client.get(reverse('password_reset_complete'))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_post_request_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(self.user)

        # Act
        response = self.client.post(reverse('password_reset_complete'))

        # Assert
        self.assertRedirects(response, reverse('home'))

class RegistrationTests(TestCase):
    def test_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(factories.UserFactory())

        # Act
        response = self.client.get(reverse('register'))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_renders_registration_form(self):
        # Act
        response = self.client.get(reverse('register'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('templates/registration/register.html')

    def test_renders_registration_form_if_submit_is_invalid(self):
        # Act
        response = self.client.post(reverse('register'), {})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('templates/registration/register.html')

    @patch("homepage.views.registration_views.is_recaptcha_success")
    def test_sends_registration_email_with_completed_form(self, mock_recaptcha):
        # Act
        mock_recaptcha.return_value = True
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': NEW_USER_EMAIL, 'password1': PASSWORD, 'password2': PASSWORD})

        # Assert
        self.assertRedirects(response, reverse('register_done'))
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual([NEW_USER_EMAIL], mail.outbox[0].to)
        self.assertEqual(MODARCHIVE_EMAIL, mail.outbox[0].from_email)
        self.assertEqual("Active your ModArchive account", mail.outbox[0].subject)
        self.assertTrue("Thank you for registering an account with the Mod Archive. To complete your registration, please follow this link:" in mail.outbox[0].body)
        self.assertTrue("https://testserver/activate_account" in mail.outbox[0].body)

    @patch("homepage.views.registration_views.is_recaptcha_success")
    def test_notifies_existing_user_if_email_address_already_in_use(self, mock_recaptcha):
        # Arrange
        mock_recaptcha.return_value = True
        user = factories.UserFactory(email='testuser@test.com')

        # Act
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': user.email, 'password1': PASSWORD, 'password2': PASSWORD})

        # Assert
        self.assertRedirects(response, reverse('register_done'))
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual([user.email], mail.outbox[0].to)
        self.assertEqual(MODARCHIVE_EMAIL, mail.outbox[0].from_email)
        self.assertEqual("ModArchive security warning", mail.outbox[0].subject)
        self.assertTrue("A user attempted to register a ModArchive account with your email address." in mail.outbox[0].body)

    @patch("homepage.views.registration_views.is_recaptcha_success")
    def test_redirects_to_register_fail_if_recaptcha_fails(self, mock_recaptcha):
        # Arrange
        mock_recaptcha.return_value = False

        # Act
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': NEW_USER_EMAIL, 'password1': PASSWORD, 'password2': PASSWORD})

        # Assert
        self.assertRedirects(response, reverse('register_fail'))

    @patch("homepage.views.registration_views.is_recaptcha_success")
    def test_registration_creates_user_but_not_profile(self, mock_recaptcha):
        # Act
        mock_recaptcha.return_value = True
        self.client.post(reverse('register'), {'username': 'new_user', 'email': NEW_USER_EMAIL, 'password1': PASSWORD, 'password2': PASSWORD})

        # Assert
        user = User.objects.get(username = 'new_user')
        self.assertIsNotNone(user)
        self.assertFalse(hasattr(user, 'profile'))

class ActivationTests(TestCase):
    kwargs = {'uidb64': 'Mg', 'token': 'asdfasdf'}

    def test_redirects_authenticated_user(self):
        # Arrange
        self.client.force_login(factories.UserFactory())

        # Act
        response = self.client.get(reverse('activate_account', kwargs=self.kwargs))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_activates_user(self):
        # Arrange
        user = factories.UserFactory(is_active=False)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        self.assertRedirects(response, reverse('account_activation_complete'))
        user.refresh_from_db()
        self.assertTrue(user.is_active, "Expected user to be active")

    def test_creates_profile_on_user_activation(self):
        # Arrange
        user = factories.UserFactory(is_active=False)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        user.refresh_from_db()
        self.assertTrue(hasattr(user, 'profile'))
        profile = user.profile
        self.assertIsNotNone(profile, "Expected profile to exist for user")
        self.assertEqual(user.username, profile.display_name, "Profile display name did not match username")

    def test_redirects_to_home_if_user_already_active(self):
        # Arrange
        user = factories.UserFactory(is_active=True)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_redirects_to_error_page_if_something_goes_wrong(self):
        # Arrange
        user = factories.UserFactory(is_active=True)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        user.delete()

        # Act
        response = self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        self.assertRedirects(response, reverse('activation_error'))

class LegacyRedirectionViewTests(TestCase):
    def test_redirects_to_home_if_no_match_found(self):
        response = self.client.get('/login.php/?blarg=blag')
        self.assertRedirects(response, reverse('home'))

    def test_mixed_case_query_param_still_redirects(self):
        response = self.client.get('/login.php/?request=lOg_iN')
        self.assertRedirects(response, reverse('login'))

    def test_old_login_url_redirects(self):
        response = self.client.get('/login.php/?request=log_in')
        self.assertRedirects(response, reverse('login'))

    def test_old_forgot_password_url_redirects(self):
        response = self.client.get('/assistance.php/?request=forgot_password_page')
        self.assertRedirects(response, reverse('forgot_password'))

    def test_old_change_password_url_redirects(self):
        self.client.force_login(factories.UserFactory())
        response = self.client.get('/interactive.php/?request=change_password_page')
        self.assertRedirects(response, reverse('change_password'))

    def test_old_register_url_redirects(self):
        response = self.client.get('/assistance.php/?request=create_account_page')
        self.assertRedirects(response, reverse('register'))

    def test_old_module_url_redirects(self):
        song = song_factories.SongFactory(id=48552)
        response = self.client.get('/index.php/?request=view_by_moduleid&query=48552')
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_old_module_url_redirects_to_home_for_invalid_id(self):
        response = self.client.get('/index.php/?request=view_by_moduleid&query=99999')
        self.assertRedirects(response, reverse('home'))

    def test_old_module_url_redirects_to_song_if_song_redirect_exists(self):
        song = song_factories.SongFactory(id=48553)
        song_factories.SongRedirectFactory(song=song, old_song_id=48553)
        response = self.client.get('/index.php/?request=view_by_moduleid&query=48553')
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

class ProfileViewTests(TestCase):
    def test_profile_page_contains_requested_profile(self):
        # Arrange
        user = factories.UserFactory()
        user.profile.display_name = 'Arcturus'
        user.profile.save()

        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': user.profile.id}))

        # Assert
        self.assertTemplateUsed(response, 'profile/profile_overview.html')
        self.assertTrue('profile' in response.context)

        profile = response.context['profile']
        self.assertEqual(profile, user.profile)
        self.assertIsNone(response.context['artist'])
    
    def test_profile_page_with_artist_contains_requested_profile_and_artist(self):
        # Arrange
        user = factories.UserFactory()
        user.profile.display_name = 'Arcturus'
        user.profile.save()
        artist = artist_factories.ArtistFactory(name='Arcturus', legacy_id=69117, user=user, profile=user.profile)
    
        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': user.profile.id}))

        # Assert
        self.assertTemplateUsed(response, 'profile/profile_overview.html')
        self.assertEqual(response.context['profile'], user.profile)
        self.assertEqual(artist, response.context['artist'])

    def test_profile_page_responds_with_404_when_profile_does_not_exist(self):
        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': 42}))

        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_profile_page_has_most_recent_messages(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        for _ in range(11):
            factories.MessageFactory(profile=user.profile, sender=user_2.profile)

        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': user.profile.id}))

        # Assert
        self.assertEqual(response.status_code, 200)
        most_recent_messages = response.context['most_recent_messages']
        all_messages = user.profile.profile_messages.order_by('-create_date')

        # Verify only 10 messages are included
        self.assertEqual(len(most_recent_messages), 10)

        # Verify they are the 10 most recent
        expected_messages = list(all_messages[:10])
        self.assertEqual(list(most_recent_messages), expected_messages)
    
    def test_profile_page_does_not_have_messages_when_shoutwall_disabled(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        factories.MessageFactory(profile=user.profile, sender=user_2.profile)
        profile = user.profile
        profile.enable_shoutwall = False
        profile.save()

        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': user.profile.id}))

        # Assert
        most_recent_messages = response.context.get('most_recent_messages')
        self.assertIsNone(most_recent_messages)

class ProfileSongViewTests(TestCase):
    def test_redirects_when_profile_is_not_artist(self):
        # Arrange
        user = factories.UserFactory()

        # Act
        response = self.client.get(reverse('view_profile_songs', kwargs = {'pk': user.profile.id}))

        # Assert
        self.assertRedirects(response, reverse('view_profile', kwargs = {'pk': user.profile.id}))
    
    def test_includes_first_page_of_songs(self):
        # Arrange
        user = factories.UserFactory()
        user.profile.display_name = 'Arcturus'
        user.profile.save()
        songs = [song_factories.SongFactory() for _ in range(30)]
        artist = artist_factories.ArtistFactory(name='Arcturus', legacy_id=69117, user=user, profile=user.profile, songs=songs)
        expected_first_page = list(artist.songs.order_by("-create_date")[:25])
        
        # Act
        response = self.client.get(reverse('view_profile_songs', kwargs = {'pk': user.profile.id}))

        # Assert
        self.assertEqual(response.status_code, 200)
        page_songs = list(response.context["songs"])
        self.assertEqual(len(page_songs), 25)
        self.assertEqual(page_songs, expected_first_page)
        self.assertEqual(artist, response.context['artist'])
        self.assertEqual(user.profile, response.context['profile'])
    
    def test_includes_second_page_of_songs(self):
        # Arrange
        user = factories.UserFactory()
        user.profile.display_name = 'Arcturus'
        user.profile.save()
        songs = [song_factories.SongFactory() for _ in range(30)]
        artist = artist_factories.ArtistFactory(name='Arcturus', legacy_id=69117, user=user, profile=user.profile, songs=songs)
        expected_first_page = list(artist.songs.order_by("-create_date")[25:])
        
        # Act
        response = self.client.get(reverse('view_profile_songs', kwargs = {'pk': user.profile.id}) + '?page=2')

        # Assert
        self.assertEqual(response.status_code, 200)
        page_songs = list(response.context["songs"])
        self.assertEqual(len(page_songs), 5)
        self.assertEqual(page_songs, expected_first_page)
        self.assertEqual(artist, response.context['artist'])

class ProfileCommentsViewTest(TestCase):
    def test_returns_404_when_profile_does_not_exist(self):
        # Act
        response = self.client.get(reverse('view_profile_comments', kwargs = {'pk': 500}))

        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_shows_first_40_comments_on_page_1(self):
        # Arrange
        user = factories.UserFactory()
        songs = [song_factories.SongFactory() for _ in range(50)]
        comments = [interaction_factories.CommentFactory(profile=user.profile, song=song) for song in songs]

        # Act
        response = self.client.get(reverse('view_profile_comments', kwargs = {'pk': user.profile.id}))

        # Assert
        actual_comments = response.context['object_list']
        self.assertEqual(len(actual_comments), 40)

        # Expect most recent 40
        expected_comments = list(reversed(comments))[:40]
        self.assertEqual([f.id for f in actual_comments], [f.id for f in expected_comments])
    
    def test_shows_next_comments_on_page_2(self):
        # Arrange
        user = factories.UserFactory()
        songs = [song_factories.SongFactory() for _ in range(50)]
        comments = [interaction_factories.CommentFactory(profile=user.profile, song=song) for song in songs]

        # Act
        response = self.client.get(reverse('view_profile_comments', kwargs = {'pk': user.profile.id}) + '?page=2')

        # Assert
        actual_comments = response.context['object_list']
        self.assertEqual(len(actual_comments), 10)

        # Expect the *oldest* 10
        expected_comments = list(reversed(comments))[40:]
        self.assertEqual([f.id for f in actual_comments], [f.id for f in expected_comments])

class ProfileFavoritesViewTest(TestCase):
    def test_returns_404_when_profile_does_not_exist(self):
        # Act
        response = self.client.get(reverse('view_profile_favorites', kwargs = {'pk': 500}))

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_shows_first_50_favorites_on_page_1(self):
        # Arrange
        user = factories.UserFactory()
        songs = [song_factories.SongFactory() for _ in range(60)]
        favorites = [interaction_factories.FavoriteFactory(profile=user.profile, song=song) for song in songs]

        # Act
        response = self.client.get(reverse('view_profile_favorites', kwargs = {'pk': user.profile.id}))

        # Assert
        actual_favorites = response.context['object_list']
        self.assertEqual(len(actual_favorites), 50)

        # Expect most recent 50
        expected_favorites = list(reversed(favorites))[:50]
        self.assertEqual([f.id for f in actual_favorites], [f.id for f in expected_favorites])
    
    def test_shows_next_favorites_on_page_2(self):
        # Arrange
        user = factories.UserFactory()
        songs = [song_factories.SongFactory() for _ in range(60)]
        favorites = [interaction_factories.FavoriteFactory(profile=user.profile, song=song) for song in songs]

        # Act
        response = self.client.get(reverse('view_profile_favorites', kwargs = {'pk': user.profile.id}) + '?page=2')

        # Assert
        actual_favorites = response.context['object_list']
        self.assertEqual(len(actual_favorites), 10)

        # Expect the *oldest* 10
        expected_favorites = list(reversed(favorites))[50:]
        self.assertEqual([f.id for f in actual_favorites], [f.id for f in expected_favorites])


class ProfileMessageViewTests(TestCase):
    def test_redirects_when_profile_shoutwall_disabled(self):
        # Arrange
        user = factories.UserFactory()
        user.profile.enable_shoutwall = False
        user.profile.save()

        # Act
        response = self.client.get(reverse('view_profile_messages', kwargs = {'pk': user.profile.id}))

        # Assert
        self.assertRedirects(response, reverse('view_profile', kwargs = {'pk': user.profile.id}))
    
    def test_returns_404_when_profile_does_not_exist(self):
        # Act
        response = self.client.get(reverse('view_profile_messages', kwargs = {'pk': 500}))

        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_messages_are_paginated(self):
        # Arrange
        user = factories.UserFactory()
        messages = [factories.MessageFactory(profile=user.profile, sender=user.profile) for _ in range(25)]
        # Create replies
        [factories.MessageFactory(profile=user.profile, sender=user.profile, thread_starter=msg, reply_to=msg,)for msg in messages]

        # Act
        response = self.client.get(reverse('view_profile_messages', kwargs = {'pk': user.profile.id}))

        # Assert
        top_level_messages = response.context["object_list"]
        self.assertEqual(len(top_level_messages), 20)

        all_rendered_messages = []
        for msg in top_level_messages:
            all_rendered_messages.append(msg)
            all_rendered_messages.extend(msg.replies.all())
        
        self.assertEqual(len(all_rendered_messages), 40)
        expected_top_level_ids =[m.id for m in messages[5:]][::-1]
        actual_top_level_ids = [m.id for m in top_level_messages]
        self.assertEqual(expected_top_level_ids, actual_top_level_ids)
    
    def test_messages_are_paginated_on_page_2(self):
        # Arrange
        user = factories.UserFactory()
        messages = [factories.MessageFactory(profile=user.profile, sender=user.profile) for _ in range(25)]
        # Create replies
        [factories.MessageFactory(profile=user.profile, sender=user.profile, thread_starter=msg, reply_to=msg,)for msg in messages]

        # Act
        response = self.client.get(reverse('view_profile_messages', kwargs = {'pk': user.profile.id}) + '?page=2')

        # Assert
        top_level_messages = response.context["object_list"]
        self.assertEqual(len(top_level_messages), 5)

        all_rendered_messages = []
        for msg in top_level_messages:
            all_rendered_messages.append(msg)
            all_rendered_messages.extend(msg.replies.all())
        
        self.assertEqual(len(all_rendered_messages), 10)
        expected_top_level_ids =[m.id for m in messages[:5]][::-1]
        actual_top_level_ids = [m.id for m in top_level_messages]
        self.assertEqual(expected_top_level_ids, actual_top_level_ids)


class UpdateProfileViewTests(TestCase):
    def test_get_update_profile_redirects_unauthenticated_user(self):
        # Arrange
        update_profile_url = reverse('update_profile')

        # Act
        response = self.client.get(reverse('update_profile'))

        # Assert
        self.assertRedirects(response, f'/login/?next={update_profile_url}')

    def test_get_update_profile_includes_correct_profile(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('update_profile'))

        # Assert
        self.assertTemplateUsed(response, 'update_profile.html')
        self.assertTrue('profile' in response.context)
        self.assertEqual(user.profile.display_name, response.context['profile'].display_name)

    def test_post_update_profile_redirects_unauthenticated_user(self):
        # Arrange
        update_profile_url = reverse('update_profile')

        # Act
        response = self.client.post(reverse('update_profile'))

        # Assert
        self.assertRedirects(response, f'/login/?next={update_profile_url}')

    def test_post_update_profile_successfully_updates_profile(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        self.client.post(reverse('update_profile'), {'blurb': 'new blurb', 'website': 'https://modarchive.org'})

        # Assert
        user.profile.refresh_from_db()
        self.assertEqual('new blurb', user.profile.blurb)
        self.assertEqual('https://modarchive.org', user.profile.website)
    
    def test_post_update_profile_fails_when_website_is_not_url(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('update_profile'), {'website': 'not a URL'})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('Enter a valid URL.', form.errors['website'])

class AccountSettingsViewTests(TestCase):
    def test_get_account_settings_rejects_unauthenticated_user(self):
        # Arrange
        account_settings_url = reverse('account_settings')

        # Act
        response = self.client.get(reverse('account_settings'))

        # Assert
        self.assertRedirects(response, f'/login/?next={account_settings_url}')
    
    def test_post_account_settings_rejects_unauthenticated_user(self):
        # Arrange
        account_settings_url = reverse('account_settings')

        # Act
        response = self.client.post(reverse('account_settings'))

        # Assert
        self.assertRedirects(response, f'/login/?next={account_settings_url}')
    
    def test_get_account_settings_includes_correct_profile(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('account_settings'))

        # Assert
        self.assertTemplateUsed(response, 'account_settings.html')
        self.assertTrue('profile' in response.context)
        self.assertEqual(user.profile.display_name, response.context['profile'].display_name)
    
    def test_post_account_settings_modifies_settings(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        self.client.post(
            reverse('account_settings'),
            {
                'enable_shoutwall': False,
                'enable_notifications': True,
                'enable_shoutwall_notifications': True,
                'email': 'newuser@website.com'
                }
        )

        # Assert
        user.profile.refresh_from_db()
        user.refresh_from_db()
        self.assertFalse(user.profile.enable_shoutwall)
        self.assertTrue(user.profile.enable_shoutwall_notifications)
        self.assertTrue(user.profile.enable_notifications)
        self.assertEqual('newuser@website.com', user.email)
    
    def test_email_address_cannot_be_blank(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('account_settings'), {'enable_shoutwall': False, 'email': ''})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('This field is required.', form.errors['email'])
    
    def test_email_address_must_be_valid(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('account_settings'), {'enable_shoutwall': False, 'email': 'not an email address'})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('Enter a valid email address.', form.errors['email'])
    
    def test_email_address_must_be_unique(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('account_settings'), {'enable_shoutwall': False, 'email': user_2.email})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('This email address is already in use.', form.errors['email'])
    
    def test_email_address_cannot_be_from_blacklisted_domain(self):
        # Arrange
        user = factories.UserFactory()
        factories.BlacklistedDomainFactory(domain='bad-domain.com', added_by=factories.UserFactory())
        self.client.force_login(user)      

        # Act
        response = self.client.post(reverse('account_settings'), {'enable_shoutwall': False, 'email': 'user@bad-domain.com'})  

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('Email addresses from this domain are not allowed.', form.errors['email'])

class FrontPageViewTests(TestCase):
    def test_front_page_has_five_most_recent_news_items(self):
        # Arrange
        user = factories.UserFactory()
        for n in range(6):
            factories.NewsFactory(profile=user.profile, headline=f"This is headline {n + 1}")

        # Act
        response = self.client.get(reverse('home'))

        # Assert
        self.assertEqual(5, len(response.context['latest_news']))
        self.assertEqual("This is headline 6", response.context['latest_news'][0].headline)
        self.assertEqual("This is headline 2", response.context['latest_news'][4].headline)
